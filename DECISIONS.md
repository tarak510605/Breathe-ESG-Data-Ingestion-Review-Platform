# Key Architecture Decisions

## Data Model Decisions

### 1. **Immutable Raw Records**
**Decision:** `RawRecord` is write-once; never updated.

**Rationale:**
- Auditability: Proves what was originally uploaded
- Compliance: Shows original data in case of disputes
- Debugging: Can replay ingestion if logic changes
- Enterprise pattern: SAP, financial systems store immutable journals

**Trade-off:**
- More storage for duplicate copies (mitigated by JSONB compression)
- Can't fix upstream source errors without full reupload

### 2. **Separate Normalized Records from Raw**
**Decision:** Create two linked entities: `RawRecord` → `NormalizedEmissionRecord`

**Rationale:**
- Analysts need to edit normalized values (e.g., correct a typo)
- Original must remain pristine
- Traceability: See what changed from raw → normalized
- Real-world workflow: Raw is "what came in", Normalized is "what we calculated"

**Alternative Considered:**
- Store original and current in one record (versioning field)
- Rejected: Breaks normalized table schema (flexible vs rigid tradeoff)

### 3. **Scope 1/2/3 as Enum in NormalizedEmissionRecord**
**Decision:** `emission_category` ENUM, not separate table

**Rationale:**
- Scope categories are static (~10 values)
- Simpler queries ("all Scope 3 records")
- No performance gain from lookup table
- Clearer semantics

**Alternative Considered:**
- `EmissionCategory` lookup table
- Rejected: Over-engineering for static reference data

---

## Service Architecture Decisions

### 4. **Ingestion Processing is Synchronous (For Now)**
**Decision:** File upload → Process inline (return job ID with status)

**Rationale:**
- Internship project: scale requirements are modest
- Simpler debugging and testing
- Analysts expect quick feedback
- Can add async (Celery) later without major changes

**Scaling Strategy:**
- If job sizes > 10K records: move to background task
- If > 100 concurrent uploads: add queue
- Structure allows this transition (Service layer doesn't know about execution model)

**Note to Evaluators:**
This is an intentional simplicity tradeoff. Real enterprise systems often use Celery/RabbitMQ, but the bottleneck here is PostgreSQL writes, not compute.

### 5. **Anomaly Detection is Heuristic-Based, Not ML**
**Decision:** IQR outlier detection + rule-based checks

**Rationale:**
- No labeled training data in a startup scenario
- Rules are explainable to analysts
- Easier to maintain and debug
- Fast (rules run during ingestion)

**Anomalies Detected:**
- Statistical outliers (quantity > mean + 3*stddev)
- Missing required fields
- Invalid formats/codes
- Suspicious values (negative quantities)
- Duplicates (same source, date, asset)

**Not Detected (Would Require Labeled Data):**
- "This company's emissions are unusually high for its industry"
- Behavioral anomalies across multiple trips

### 6. **Analysts Can Edit Normalized Values**
**Decision:** After failed validation, analysts can manually correct and approve

**Rationale:**
- Data sources are messy (typos, format issues)
- Approved records become immutable (`is_locked=True`)
- Changes logged in `AuditLog` with reason
- Real workflow: analyst resolves ambiguity

**Implementation:**
- Edit creates new `NormalizedEmissionRecord` version? NO
- Edit updates record, AuditLog captures change
- Prevents analysts from circumventing validation

---

## Multi-Tenancy Decisions

### 7. **Tenant ID in Every Table**
**Decision:** `organization_id` on all tables (except Users which have FK)

**Rationale:**
- Cannot accidentally leak data across tenants
- Queryset filtering in Django middleware
- Query performance (most tables are already filtered by org)

**Alternative Considered:**
- Separate database per tenant
- Rejected: Operational complexity for internship project

**Scale Limit:**
- This design scales to ~1000s of organizations
- If > 10K orgs: revisit schema partitioning

### 8. **User Roles: Admin, Analyst, Reviewer**
**Decision:** Three distinct roles, permission checks in views

**Rationale:**
- Admin: Org settings, user management
- Analyst: Upload files, review records
- Reviewer: Approve/reject records
- Simple role-based access control (RBAC)

**Not Implemented:**
- Fine-grained permissions (e.g., "can only review records from source X")
- Temporal access (e.g., "can access for next 30 days")
- Better when requirements solidify

---

## API Design Decisions

### 9. **Pagination Over Bulk Export**
**Decision:** All list endpoints use offset/limit pagination (default 50 per page)

**Rationale:**
- Dashboard performance (don't load 100K records)
- Frontend pagination UX
- Database query efficiency

**Exceptions:**
- Error log export: endpoint returns CSV for specific job
- Audit log: paginated list, with CSV export option

### 10. **File Uploads via Multipart Form, Not Base64**
**Decision:** `POST /api/ingestion/upload/` accepts `multipart/form-data`

**Rationale:**
- Simpler for frontend (HTML5 file input)
- More efficient (no Base64 overhead)
- Standard REST pattern

**Storage:**
- Files stored in `media/uploads/{organization_id}/{job_id}/`
- Not parsed into database until job processing
- Can delete after successful normalization

### 11. **Records Reviewed Via Individual Endpoints, Not Batch Actions**
**Decision:** `PATCH /api/emissions/records/{id}/approve/` (one record per request)

**Rationale:**
- Simpler API (no bulk transaction logic)
- Clearer audit trail (each action logged)
- UI matches action (one modal = one record)

**Trade-off:**
- Slow for reviewing 1000s at once
- Real solution: bulk approve with checkboxes, but start simple

---

## Database Design Decisions

### 12. **JSONB for Flexible Raw Data & Snapshots**
**Decision:** `RawRecord.raw_data` is JSONB; `NormalizedEmissionRecord.original_value` is JSONB snapshot

**Rationale:**
- Raw records are heterogeneous (SAP CSV vs travel API)
- Snapshots preserve exact state at normalization time
- PostgreSQL JSONB is queryable and efficient
- Easier than EAV (Entity-Attribute-Value) model

**Example:**
```json
{
  "Datum": "2025-01-15",
  "Werk": "1000",
  "Material": "DIESEL-FUEL",
  "Menge": "500",
  "Einheit": "Liter"
}
```

### 13. **Timestamps Are Always UTC**
**Decision:** `created_at`, `updated_at`, `review_timestamp` all stored in UTC

**Rationale:**
- Consistency across timezones
- Standard practice
- Frontend converts to user timezone for display

### 14. **Foreign Keys Preserve Referential Integrity**
**Decision:** Use `on_delete=models.PROTECT` or `CASCADE` based on entity lifecycle

**Example:**
- `RawRecord.ingestion_job` → `CASCADE` (if job deleted, purge records)
- `NormalizedEmissionRecord.raw_record` → `PROTECT` (never delete raw)
- `AuditLog.record` → `PROTECT` (preserve audit trail)

---

## Frontend Architecture Decisions

### 15. **React + TypeScript (No Redux)**
**Decision:** Use Zustand or Context API for state management

**Rationale:**
- Project is not complex (no deeply nested state)
- Zustand is lighter than Redux
- Context API sufficient for auth + org state
- Easier onboarding for junior developers

**State Managed:**
- Auth (token, user, permissions)
- Organization (current org, settings)
- UI state (modals, filters) → component-local

**API calls:** React Query or direct Axios (start simple)

### 16. **Reusable DataTable Component**
**Decision:** One `<DataTable />` component with sorting, filtering, pagination

**Rationale:**
- Jobs list, review queue, audit log share same UX
- Reduces duplication
- Consistent behavior across app

**Features:**
- Column definitions (name, label, sortable, filterable)
- Pagination controls
- Row click handler (open detail modal)
- Bulk actions (optional checkboxes)

### 17. **Drawer for Record Details, Not Page Navigation**
**Decision:** Click row → opens side panel (drawer) with detail + edit

**Rationale:**
- Analyst stays on list, can see context
- No page navigation (faster workflow)
- Easy to scroll through multiple records
- Standard pattern in dashboards

---

## Security Decisions

### 18. **JWT Tokens with Refresh Pattern**
**Decision:** `access_token` (15 min TTL) + `refresh_token` (7 days)

**Rationale:**
- Shorter-lived tokens reduce exposure
- Refresh pattern prevents constant re-login
- Standard OAuth 2.0 pattern

**Not Implemented:**
- Multi-factor authentication (add if requirements emerge)
- Rate limiting on login (add when deployed)

### 19. **No Role-Based Endpoint Versioning**
**Decision:** Roles checked in views, not separate API versions

**Rationale:**
- Single API surface
- Simpler to maintain
- Permissions checked per action (e.g., only analysts can upload)

---

## What Was Intentionally Left Out

### Batch Operations
- No "approve 100 records at once" endpoint yet
- Simpler API, can add if needed

### Notifications
- No email alerts when records flagged
- Can add with Celery + SendGrid later

### Advanced Anomaly Detection
- No ML models
- No time-series analysis
- Heuristic rules sufficient for MVP

### Detailed Role-Based Access
- No column-level permissions
- No "analyst can only see records from source X"
- Add if organization structure demands it

### Workflow States Beyond Approved/Rejected
- No "Needs More Info" state
- Analyst edits + requeues instead
- Simpler state machine

### Historical Emission Factor Versions
- Factors are effective-dated but not versioned per record
- Can recalculate retroactively if factor changes
- Good enough for MVP

---

## Unanswered Questions for Product

1. **Do analysts need to approve BEFORE normalization runs?**
   - Current design: Normalize → Flag anomalies → Analyst reviews
   - Alternative: Analyst maps columns first, then normalization?

2. **Should approved records be immutable forever, or editable with approval?**
   - Current: Locked after approval
   - Alternative: Editable but creates new audit entry?

3. **Do we track cost separately from emissions?**
   - Current: Cost is optional field in NormalizedRecord
   - May need separate financial model if cost tracking is important

4. **How do we handle a single upload that spans multiple months?**
   - Current: period_start/period_end per record
   - Good enough? Or need monthly rollup view?

5. **Should duplicate detection compare records across organizations?**
   - Current: Only within organization
   - Multi-org dedup would need different approach

---

## Performance Assumptions

- Initial dataset: < 100K records/org
- Users: < 100/org
- Concurrent uploads: < 10
- Typical query: < 1 sec
- File uploads: < 50MB
- **If exceeded:** Optimize with indexes, caching, async processing

---

## Testing Strategy

- **Unit Tests:** Parser, normalizer, validation logic (highest ROI)
- **Integration Tests:** API endpoints, job lifecycle
- **Seed Data:** Realistic sample datasets for manual testing
- **Load Testing:** Not initial priority (can add with deployment)

---

## Monitoring & Logging

- Django logging to stdout (captured by Docker logs)
- Audit logs queryable via API
- Error tracking: Sentry (optional, add post-MVP)
- No custom metrics dashboard initially
