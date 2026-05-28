# ESG Data Ingestion Platform - Architecture Plan

## System Overview

A multi-tenant ESG data ingestion and audit review platform designed to handle enterprise emissions data from multiple sources (SAP, utilities, travel systems). The system emphasizes data quality, auditability, and analyst-friendly review workflows.

**Core Insight:** This is not an emissions calculator. It's a data ops platform for safely ingesting, validating, and approving enterprise ESG data.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                           │
│  React + TypeScript Dashboard (Analyst Review & Management)       │
├──────────────────────────────────────────────────────────────────┤
│                        API GATEWAY LAYER                          │
│  Django REST Framework - Auth, File Upload, Job Management       │
├──────────────────────────────────────────────────────────────────┤
│                      SERVICE LAYER (Business Logic)              │
│  Ingestion Pipeline │ Normalization │ Validation │ Review Queue  │
├──────────────────────────────────────────────────────────────────┤
│                      DATA MODEL LAYER                             │
│  Organizations │ Users │ Jobs │ Records │ Audit Logs             │
├──────────────────────────────────────────────────────────────────┤
│                    PostgreSQL Database                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## DOMAIN MODEL DESIGN

### Core Entities

#### 1. **Organization** (Multi-Tenant Root)
- `id` (UUID, PK)
- `name` (str)
- `slug` (str, unique per tenant)
- `created_at`, `updated_at`
- Stores organization-level settings, emission factors, unit preferences

#### 2. **User** (Scoped to Organization)
- `id` (UUID, PK)
- `organization_id` (FK)
- `email` (str)
- `full_name` (str)
- `role` (ENUM: admin, analyst, reviewer)
- `is_active` (bool)
- `created_at`, `updated_at`

#### 3. **DataSource** (Configuration)
- `id` (UUID, PK)
- `organization_id` (FK)
- `name` (str) - "SAP Fuel Feed", "Utility Portal", "Concur API"
- `source_type` (ENUM: sap_csv, utility_csv, travel_api)
- `connection_config` (JSON) - API keys, credentials, URLs
- `is_active` (bool)
- `metadata` (JSON) - Field mappings, defaults
- `created_at`, `updated_at`

#### 4. **IngestionJob** (Batch Processing Unit)
- `id` (UUID, PK)
- `organization_id` (FK)
- `data_source_id` (FK)
- `status` (ENUM: pending, processing, completed, failed)
- `file_name` (str)
- `file_path` (str) - S3 or local storage path
- `file_size` (int)
- `total_records` (int) - counted during processing
- `valid_records` (int) - passed validation
- `invalid_records` (int)
- `suspicious_records` (int)
- `processed_at` (timestamp, nullable)
- `processing_error` (text, nullable)
- `uploaded_by_id` (FK to User)
- `created_at`, `updated_at`

#### 5. **RawRecord** (Immutable Original Data)
- `id` (UUID, PK)
- `ingestion_job_id` (FK)
- `organization_id` (FK)
- `raw_data` (JSONB) - Original unparsed record
- `source_line_number` (int)
- `created_at` (timestamp)
- **NO updates** - complete immutability

#### 6. **NormalizedEmissionRecord** (Processed & Reviewable)
- `id` (UUID, PK)
- `organization_id` (FK)
- `raw_record_id` (FK, NOT NULL)
- `data_source_id` (FK)
- `ingestion_job_id` (FK)
- `status` (ENUM: pending_review, approved, rejected, flagged)
- `emission_category` (ENUM: scope_1_fuel, scope_1_process, scope_2_electricity, scope_2_steam, scope_3_travel, scope_3_procurement)
- `emission_source` (str) - "Fleet Fuel", "Electricity", "Air Travel", etc.
- **Normalized Fields:**
  - `quantity` (decimal)
  - `unit` (str) - "kg_co2e", "kg", "kWh", "miles", etc.
  - `emissions_kg_co2e` (decimal) - Calculated using emission factor
  - `period_start` (date)
  - `period_end` (date)
  - `facility_code` (str, nullable)
  - `source_reference_id` (str) - Link back to source
  - `asset_id` (str, nullable)
  - `currency` (str, nullable) - for cost tracking
  - `cost` (decimal, nullable)
- **Audit Fields:**
  - `original_value` (JSONB) - Snapshot of raw record at creation
  - `edited_value` (JSONB, nullable) - If analyst edited it
  - `review_notes` (text, nullable)
  - `is_locked` (bool) - Prevent edits after approval
- **Reviewer Info:**
  - `reviewed_by_id` (FK, nullable)
  - `review_decision` (ENUM: pending, approved, rejected)
  - `review_timestamp` (timestamp, nullable)
  - `review_comment` (text, nullable)
- `created_at`, `updated_at`

#### 7. **EmissionFactor** (Unit Normalization Lookup)
- `id` (UUID, PK)
- `organization_id` (FK)
- `source_unit` (str) - "liters", "gallons", "metric_tons", "kWh"
- `target_unit` (str) - Always "kg_co2e"
- `factor_value` (decimal) - Conversion factor
- `factor_type` (str) - "fuel_type_diesel", "fuel_type_gasoline", "grid_electricity_us"
- `description` (str) - "Diesel combustion emissions factor"
- `effective_from` (date)
- `effective_to` (date, nullable)
- `source_reference` (str) - "EPA eGRID 2023", "GHG Protocol", etc.
- `created_at`, `updated_at`

#### 8. **AuditLog** (Immutable Event History)
- `id` (UUID, PK)
- `organization_id` (FK)
- `user_id` (FK)
- `record_id` (FK to NormalizedEmissionRecord)
- `action` (ENUM: created, edited, approved, rejected, locked, comment_added)
- `previous_value` (JSONB, nullable)
- `new_value` (JSONB, nullable)
- `change_reason` (text, nullable)
- `created_at` (timestamp)
- **NO updates** - complete immutability

#### 9. **AnomalyFlag** (Data Quality)
- `id` (UUID, PK)
- `normalized_record_id` (FK)
- `organization_id` (FK)
- `anomaly_type` (ENUM: outlier, missing_field, duplicate, invalid_format, suspicious_value)
- `severity` (ENUM: info, warning, critical)
- `description` (str)
- `metric_name` (str) - What field triggered it
- `threshold_value` (str, nullable)
- `actual_value` (str, nullable)
- `is_resolved` (bool)
- `analyst_note` (text, nullable)
- `created_at`, `updated_at`

---

## BACKEND ARCHITECTURE

### Folder Structure

```
breathe-backend/
├── manage.py
├── requirements.txt
├── pytest.ini
├── docker-compose.yml
├── Dockerfile
├── breathe/
│   ├── settings.py              # Django settings
│   ├── urls.py
│   ├── wsgi.py
│   └── middleware.py            # Audit logging, org scoping
├── organizations/
│   ├── models.py               # Organization, User
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py          # Tenant-aware permissions
├── data_sources/
│   ├── models.py               # DataSource, EmissionFactor
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── ingestion/
│   ├── models.py               # IngestionJob, RawRecord
│   ├── serializers.py
│   ├── views.py                # File upload endpoint
│   ├── urls.py
│   ├── services.py             # Processing orchestration
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── sap_parser.py       # SAP CSV logic
│   │   ├── utility_parser.py   # Utility CSV logic
│   │   └── travel_parser.py    # Travel API payload logic
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── sap_validator.py
│   │   ├── utility_validator.py
│   │   └── travel_validator.py
│   └── normalizers/
│       ├── __init__.py
│       ├── sap_normalizer.py
│       ├── utility_normalizer.py
│       └── travel_normalizer.py
├── emissions/
│   ├── models.py               # NormalizedEmissionRecord, AnomalyFlag
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py             # Review queue logic
│   └── anomaly_detection.py    # Outlier detection
├── audit/
│   ├── models.py               # AuditLog
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py           # Auto-logging middleware
│   └── signals.py              # Django signals for logging
├── api/
│   ├── authentication.py       # JWT auth views
│   ├── dashboard.py            # Dashboard metrics
│   └── urls.py                 # Main API router
├── tests/
│   ├── conftest.py
│   ├── factories.py            # Factory Boy models
│   ├── test_sap_parser.py
│   ├── test_normalization.py
│   ├── test_api_endpoints.py
│   └── test_audit_logging.py
└── utils/
    ├── storage.py              # S3/Local file handling
    ├── validators.py           # Shared validation logic
    └── logging.py
```

### Key Service Layer Classes

**IngestioService** (`ingestion/services.py`)
```
class IngestionService:
    def process_upload(job: IngestionJob) -> None
        - Parse raw file
        - Create RawRecords
        - Call appropriate parser
        - Create NormalizedRecords
        - Run validators
        - Detect anomalies
    
    def get_processing_status(job_id) -> dict
        - Returns counts of valid/invalid/suspicious
```

**NormalizationService** (`emissions/services.py`)
```
class NormalizationService:
    def normalize_sap_record(raw_record) -> NormalizedRecord
    def normalize_utility_record(raw_record) -> NormalizedRecord
    def normalize_travel_record(raw_record) -> NormalizedRecord
    def calculate_co2e(quantity, unit, factor) -> decimal
```

**ReviewQueueService** (`emissions/services.py`)
```
class ReviewQueueService:
    def get_pending_records(org_id) -> QuerySet
    def approve_record(record_id, reviewer_id, comment) -> None
    def reject_record(record_id, reviewer_id, reason) -> None
    def edit_and_requeue(record_id, edits, reason) -> None
```

**AnomalyDetectionService** (`emissions/anomaly_detection.py`)
```
class AnomalyDetectionService:
    def detect_anomalies(record: NormalizedRecord) -> List[AnomalyFlag]
        - Check for outliers (IQR-based)
        - Missing required fields
        - Invalid formats
        - Suspicious values
        - Duplicates
```

**AuditService** (`audit/services.py`)
```
class AuditService:
    def log_action(user, record, action, prev_val, new_val) -> None
        - Creates immutable AuditLog entry
    
    def get_record_history(record_id) -> List[AuditLog]
        - Returns complete change history
```

---

## INGESTION PIPELINES

### SAP Fuel / Procurement Flow

**Data Format (Realistic):**
```csv
Datum,Werk,Material,Kostenart,Menge,Einheit,Lieferant
2025-01-15,1000,DIESEL-FUEL,4200,500,Liter,Vendor-A
2025-01-16,2000,GASOLINE,4200,300,Gallons,Vendor-B
2025-01-17,1000,NATURAL-GAS,4210,1500,kWh,Vendor-A
```

**Parser Logic:**
1. Map columns (German → English)
2. Parse date (multiple formats)
3. Validate plant code exists
4. Convert units to kg
5. Look up emission factor

**Normalization:**
- Create `NormalizedEmissionRecord` with:
  - `emission_category`: Scope 1 Fuel
  - `emission_source`: "Fleet Fuel" or "Facility Heating"
  - `quantity`: Normalized to kg
  - `facility_code`: From Werk
  - `period_start`/`period_end`: Daily period
  - Calculated `emissions_kg_co2e`

**Anomalies to Flag:**
- Invalid Werk codes
- Unknown material types
- Quantity = 0 or negative
- Quantity > 100,000 (outlier)
- Missing units
- Duplicate records (same plant, date, material)

### Utility Electricity Flow

**Data Format:**
```csv
Meter_ID,Billing_Start,Billing_End,Service_Location,Consumption_kWh,Rate_Category
EM-001,2025-01-01,2025-02-01,Facility A,125000,Commercial
EM-002,2025-01-01,2025-02-01,Facility B,45000,Commercial
```

**Parser Logic:**
1. Validate meter ID format
2. Parse billing period dates
3. Validate consumption > 0
4. Match rate category

**Normalization:**
- Create `NormalizedEmissionRecord`:
  - `emission_category`: Scope 2 Electricity
  - `quantity`: kWh value
  - `period_start`/`period_end`: Billing period
  - Calculate `emissions_kg_co2e` using grid emission factor
  - Store facility mapping

**Anomalies:**
- Meter ID not recognized
- Billing period not aligned to calendar month
- Consumption > 500,000 kWh (potential duplicate upload)
- Missing rate category
- Negative consumption

### Travel Data Flow

**Data Format (Concur-style JSON):**
```json
{
  "trip_id": "TRIP-2025-001",
  "employee_id": "EMP-123",
  "trip_start": "2025-01-15",
  "trip_end": "2025-01-17",
  "expenses": [
    {
      "type": "flight",
      "origin": "JFK",
      "destination": "LAX",
      "cabin_class": "economy",
      "pax_count": 1
    },
    {
      "type": "hotel",
      "location": "Los Angeles",
      "nights": 2
    },
    {
      "type": "ground_transport",
      "mode": "taxi",
      "distance_miles": 50
    }
  ]
}
```

**Parser Logic:**
1. Validate trip structure
2. Parse airport codes
3. Estimate flight distances (JFK-LAX = ~2500 miles)
4. Parse hotel location
5. Parse ground transport

**Normalization:**
- Create separate `NormalizedEmissionRecord` for each expense:
  - **Flight:** Scope 3 Air Travel
    - Distance-based calculation (miles × emission factor)
    - Cabin class adjustment (economy=1x, business=3x, first=5x)
  - **Hotel:** Scope 3 Accommodation
    - Nights × emission factor
  - **Ground:** Scope 3 Ground Transport
    - Distance × mode factor (taxi > rideshare > public transit)

**Anomalies:**
- Invalid airport codes
- Negative distances
- Trip with no valid legs
- Suspicious patterns (10+ trips/week for same employee)
- Missing origin/destination

---

## API DESIGN

### Authentication
```
POST /api/auth/login/
  payload: { email, password }
  returns: { access_token, refresh_token }

POST /api/auth/refresh/
  returns: { access_token }
```

### Organizations (Tenant Management)
```
GET /api/organizations/
  - List orgs (admin only)

GET /api/organizations/me/
  - Current org details

POST /api/organizations/{id}/users/
  - Add user to org

GET /api/organizations/{id}/settings/
  - Org-level settings (units, emission factors)
```

### Data Sources
```
GET /api/data-sources/
  - List configured sources

POST /api/data-sources/
  - Create new source

PATCH /api/data-sources/{id}/
  - Update configuration
```

### Ingestion Jobs
```
POST /api/ingestion/upload/
  - Upload file → Create IngestionJob
  - payload: multipart/form-data (file, data_source_id)
  - returns: job_id, status

GET /api/ingestion/jobs/
  - List jobs with pagination, filters (status, date_range)

GET /api/ingestion/jobs/{id}/
  - Job detail + counts (valid/invalid/suspicious/approved)

GET /api/ingestion/jobs/{id}/download-errors/
  - Export invalid records as CSV

POST /api/ingestion/jobs/{id}/reprocess/
  - Reprocess a failed job
```

### Review Queue
```
GET /api/emissions/review-queue/
  - List pending records
  - Filters: status, anomaly_type, source_type, date_range
  - Pagination

GET /api/emissions/records/{id}/
  - Record detail + audit trail

PATCH /api/emissions/records/{id}/approve/
  - Approve record
  - payload: { comment }

PATCH /api/emissions/records/{id}/reject/
  - Reject record
  - payload: { reason }

PATCH /api/emissions/records/{id}/edit/
  - Analyst edits normalized values
  - payload: { field, new_value, reason }
  - Creates new review entry, doesn't modify locked records
```

### Audit & History
```
GET /api/emissions/records/{id}/audit-trail/
  - Complete change history

GET /api/audit-logs/
  - Org-wide audit log search
  - Filters: user, action, date_range, record_type
```

### Dashboard
```
GET /api/dashboard/
  - Metrics: total_records, approved, pending, failed
  - Recent jobs
  - Recent anomalies
  - Approval queue summary
```

---

## FRONTEND ARCHITECTURE

### Folder Structure
```
breathe-frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── src/
│   ├── index.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts              # Axios instance
│   │   ├── auth.ts                # Auth endpoints
│   │   ├── ingestion.ts           # Upload, job status
│   │   ├── emissions.ts           # Record detail, review
│   │   ├── audit.ts               # Audit trail
│   │   └── types.ts               # API response types
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── DashboardLayout.tsx
│   │   ├── Common/
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── SeverityBadge.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorAlert.tsx
│   │   │   └── AnomalyIndicator.tsx
│   │   ├── Tables/
│   │   │   ├── DataTable.tsx      # Reusable table
│   │   │   ├── JobsTable.tsx
│   │   │   ├── ReviewQueueTable.tsx
│   │   │   └── AuditTable.tsx
│   │   ├── Forms/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── FileUploadForm.tsx
│   │   │   └── RecordEditForm.tsx
│   │   ├── Modals/
│   │   │   ├── RecordDetail.tsx
│   │   │   ├── AuditTrailDrawer.tsx
│   │   │   └── ApprovalConfirm.tsx
│   │   └── Dashboard/
│   │       ├── MetricsCard.tsx
│   │       ├── JobsList.tsx
│   │       └── AnomalyList.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── IngestionsPage.tsx
│   │   ├── ReviewQueuePage.tsx
│   │   └── AuditLogPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useOrganization.ts
│   │   └── useInfiniteScroll.ts
│   ├── store/
│   │   ├── authStore.ts           # Zustand or Context
│   │   └── orgStore.ts
│   ├── types/
│   │   └── domain.ts              # TypeScript types mirroring backend
│   ├── utils/
│   │   ├── format.ts              # Date, number formatting
│   │   ├── validation.ts
│   │   └── constants.ts           # Enums, status codes
│   └── styles/
│       └── globals.css
└── public/
```

### Key UI Pages

**Dashboard**
- Metrics cards: Total records, approved, pending, failed
- Recent ingestion jobs (status, date, file name)
- Anomalies needing attention (count by severity)
- Approval queue summary
- Quick filters (date range, source type)

**Ingestions Page**
- Table: Job name, source, status, record counts, uploaded date
- Upload button → Modal with source selection
- Job detail → Shows error log if failed
- Reprocess button (admin)

**Review Queue**
- Table: Record ID, source, category, quantity, unit, status, anomalies
- Filters: Status (pending, approved, rejected), anomaly type, date range
- Click row → Detail drawer

**Record Detail Modal**
- Left panel: Normalized values, original values (read-only comparison)
- Middle panel: Edit form (for analyst corrections)
- Right panel: Audit trail (who changed what, when)
- Anomalies list with explanations
- Action buttons: Approve, Reject, Edit & Save

**Audit Log Page**
- Full-text search
- Filters: User, action type (created, edited, approved), date range
- Table: Timestamp, user, action, previous value, new value, reason

---

## KEY IMPLEMENTATION DECISIONS

### 1. **Immutability of Raw & Audit Data**
- `RawRecord` never updated → preserves exact original
- `AuditLog` never updated → complete change history
- Approved records become `is_locked=True` → no accidental edits
- Decision: Trust and compliance in regulated environments

### 2. **Separate Raw vs Normalized Records**
- `RawRecord` = what came in
- `NormalizedEmissionRecord` = what was processed
- Links via foreign key → traceability
- Decision: Data lineage is critical for audits

### 3. **Multi-Tenant at Database Level**
- Every table has `organization_id`
- Django middleware scopes queries
- Impossible to access another org's data via query
- Decision: Security by architecture, not permission checks

### 4. **Service Layer for Business Logic**
- Views delegate to services (`IngestionService`, `ReviewQueueService`)
- Services are testable, reusable
- Services handle transactions, error handling
- Decision: Separation of concerns, easier to test

### 5. **Flexible Emission Factor Lookup**
- `EmissionFactor` table with effective dates
- Lookup by source unit, factor type, date
- Allows updating factors without recalculating history
- Decision: Realistic enterprise requirement (factors change yearly)

### 6. **Anomaly Flags as Separate Model**
- Not hardcoded in Record validation
- Flagged records still processable
- Analyst can override/resolve flags
- Decision: Balance between alerting and not blocking workflows

---

## DEPLOYMENT CONSIDERATIONS

### Environment Setup
- `DEBUG=False` in production
- PostgreSQL 13+ (JSONB, UUID support)
- Redis for caching (optional, initially)
- S3 or local storage for file uploads
- `.env` file for secrets

### Docker
- Multi-stage build (Python 3.11)
- Gunicorn for WSGI
- Separate images for backend/frontend
- docker-compose for local development

### Database Migrations
- Use Django migrations from day one
- Test migrations locally before deploy
- Rollback plan documented

### Monitoring
- Error tracking (Sentry)
- Slow query logging
- Audit log access tracking (who queried audit logs?)

---

## REALISTIC SAMPLE DATA

Will generate:
1. **SAP Export CSV** - 50 records across 3 plants, mixed units, some errors
2. **Utility CSV** - 12 meters, billing periods, varying consumption
3. **Travel API JSON** - 5 trips with flights, hotels, ground transport

---

## NEXT STEPS

Phase 1 is ARCHITECTURE & DECISIONS. This document covers high-level design.

Next: Generate detailed code for Django models, then serializers, then views, then tests, then sample data.

Do NOT generate all code at once. Proceed systematically.
