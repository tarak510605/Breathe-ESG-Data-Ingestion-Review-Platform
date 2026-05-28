# Breathe ESG - Environmental Data Ingestion Platform

A comprehensive Django + React application for ingesting, validating, normalizing, and reviewing ESG (Environmental, Social, and Governance) emissions data from multiple sources.

## 🌍 Features

### Data Ingestion
- **Multi-Source Support**: SAP, utility portals, travel expense APIs
- **CSV & JSON Parsing**: Intelligent column mapping and data extraction
- **Batch Processing**: Process hundreds of thousands of records per job
- **Immutable Raw Records**: Full audit trail of original data

### Data Normalization
- **Smart Unit Conversion**: Automatic conversion to standardized units
- **Emission Calculations**: Convert fuel/electricity/travel to CO2e using up-to-date factors
- **Multi-Tenant**: Fully isolated organizations with independent emission factors

### Quality Assurance
- **Anomaly Detection**: Statistical outlier detection using IQR method
- **Duplicate Detection**: Identifies potential duplicate records
- **Field Validation**: Required field checks, format validation
- **Analyst Workflow**: Human review and approval queue

### Audit & Compliance
- **Immutable Audit Log**: Every change tracked and logged
- **Version Control**: Track all edits with before/after values
- **Scope Classification**: Proper GHG Protocol Scope 1/2/3 categorization
- **Emission Factor Tracking**: Source and date reference for all conversions

## 📁 Architecture

### Backend Structure
```
backend/
├── breathe/              # Django project settings
├── organizations/        # Multi-tenant organizations & users
├── data_sources/        # Data source configs & emission factors
├── ingestion/           # File upload & parsing
│   ├── parsers/        # Format-specific parsers
│   ├── validators/     # Data quality validators
│   └── normalizers/    # Data transformation logic
├── emissions/          # Normalized records & review queue
├── audit/              # Immutable audit logs
├── api/                # REST API routes
└── utils/              # Shared utilities
```

### Frontend Structure
```
frontend/
├── src/
│   ├── api/           # API client & endpoints
│   ├── pages/         # Page components
│   ├── components/    # Reusable components
│   ├── stores/        # Zustand state management
│   ├── types/         # TypeScript interfaces
│   └── utils/         # Helper functions
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15 (if not using Docker)
- Python 3.11
- Node.js 18

### Using Docker Compose (Recommended)

1. **Clone and navigate**
```bash
cd breathe
```

2. **Start all services**
```bash
docker-compose up
```

3. **Seed database** (in another terminal)
```bash
docker-compose exec backend python manage.py shell < manage_commands/seed_data.py
```

4. **Access application**
- Frontend: http://localhost:3000
- API: http://localhost:8000/api
- Admin: http://localhost:8000/admin

5. **Test credentials**
```
Email: analyst@example.com
Password: testpass123
```

### Manual Setup

#### Backend

1. **Create virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create .env file**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Seed data**
```bash
python manage.py shell < manage_commands/seed_data.py
```

6. **Start server**
```bash
python manage.py runserver
```

#### Frontend

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Start development server**
```bash
npm run dev
```

## 📊 Usage

### Uploading Data

1. Navigate to **Ingestions** page
2. Click **New Upload**
3. Select data source (SAP, Utility, Travel)
4. Choose file to upload
5. System automatically:
   - Parses data
   - Validates records
   - Normalizes to CO2e
   - Detects anomalies
   - Creates review items

### Reviewing Records

1. Go to **Review Queue**
2. Records show anomalies and basic info
3. Click to view full details
4. **Approve** or **Reject** with comments
5. Locked records cannot be edited after approval

### Viewing Audit Trail

1. Click on any record's **Audit** link
2. See complete change history
3. View who made changes and when
4. All changes are immutable

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/login/` - Login
- `POST /api/auth/refresh/` - Refresh token

### Organizations
- `GET /api/organizations/me/` - Current org

### Data Sources
- `GET/POST /api/data-sources/` - List/create data sources
- `GET/POST /api/emission-factors/` - Manage emission factors

### Ingestion
- `POST /api/ingestion-jobs/upload/` - Upload file
- `GET /api/ingestion-jobs/` - List jobs
- `POST /api/ingestion-jobs/{id}/reprocess/` - Retry failed job

### Emissions
- `GET /api/emissions/` - List records
- `GET /api/emissions/review-queue/` - Pending review
- `POST /api/emissions/{id}/approve/` - Approve
- `POST /api/emissions/{id}/reject/` - Reject
- `GET /api/emissions/{id}/audit-trail/` - History

### Anomalies
- `GET /api/anomalies/` - All flags
- `GET /api/anomalies/unresolved/` - Critical issues

## 📈 Data Models

### Organization
- Multi-tenant root entity
- Contains users, data sources, records

### User
- Role-based: Admin, Analyst, Reviewer
- Scoped to single organization

### IngestionJob
- Batch processing unit
- Tracks status, record counts
- Stores file reference

### RawRecord
- Immutable copy of original data
- Never modified or deleted
- Links to normalized records

### NormalizedEmissionRecord
- Standardized emission data
- Editable by analysts
- Locked after approval
- Contains full audit state

### AnomalyFlag
- Quality issues
- Severity levels (info/warning/critical)
- Linked to records

### AuditLog
- Immutable change log
- Every action recorded
- Before/after values

## 🔐 Security

- **JWT Authentication**: Secure token-based auth
- **Multi-Tenant Isolation**: Organization-level data separation
- **Role-Based Access**: Admin/Analyst/Reviewer permissions
- **CORS**: Restricted to allowed origins
- **Audit Trail**: Every change logged immutably

## 📝 Sample Data

Sample files available in `backend/sample_data/`:
- `sap_fuel_export.csv` - Fuel/procurement data
- `utility_meters.csv` - Electricity consumption
- `travel_expenses.json` - Travel & flight data

## 🛠️ Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

### Code Quality
```bash
# Backend linting
flake8 .

# Frontend linting
npm run lint
```

### Building for Production
```bash
# Backend
docker build -t breathe-backend .

# Frontend
npm run build
```

## 📦 Deployment

### Using Railway

1. Connect GitHub repository
2. Set environment variables
3. Deploy backend and frontend services
4. Database: Add PostgreSQL plugin

### Using Heroku

```bash
heroku create breathe-esg
heroku addons:create heroku-postgresql:standard-0
git push heroku main
```

### Using Render

1. Create new Blueprint from `render.yaml`
2. Configure environment
3. Deploy

## 🤝 Contributing

1. Create feature branch
2. Make changes with tests
3. Submit pull request
4. Code review required

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

- **Issues**: GitHub Issues
- **Docs**: See ARCHITECTURE.md, DECISIONS.md, TRADEOFFS.md
- **Email**: support@breatheplatform.com

---

**Breathe ESG v0.1.0** | Making emissions data transparent and actionable
