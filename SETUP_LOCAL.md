# Breathe ESG - Local Setup (No Docker)

## Quick Start

Run the project without Docker using Python and Node.js directly.

### Prerequisites

- **Python 3.12+** (or 3.8+)
- **Node.js 18+** with npm
- **SQLite** (included with Python)
- **Git** (for version control)

### System Check

```bash
python3 --version  # Should be 3.8+
node --version     # Should be 18+
npm --version      # Should be 9+
```

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

**Time:** ~2-3 minutes for dependencies

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work fine):
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Load Test Data

```bash
python manage.py shell < manage_commands/seed_data.py
```

This creates:
- **Organization:** Test Organization
- **User:** analyst@example.com / testpass123
- **3 DataSources:** SAP Fuel Feed, Utility Portal, Travel Expense API
- **Sample Files:** For testing ingestion

### 7. Start Backend Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Expected output:
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

**Time:** ~1-2 minutes

### 3. Start Development Server

```bash
npm run dev
```

Expected output:
```
➜ Local:   http://localhost:3001/
```

---

## Access the Application

Once both servers are running:

**Frontend:** [http://localhost:3001](http://localhost:3001)

**Backend API:** [http://localhost:8000/api](http://localhost:8000/api)

**Django Admin:** [http://localhost:8000/admin](http://localhost:8000/admin)

### Login Credentials

```
Email:    analyst@example.com
Password: testpass123
```

---

## Project Features

### 1. **Authentication** ✅
- Custom User model with UUID primary keys
- JWT-based authentication (15min access, 7day refresh tokens)
- Email as username field
- Custom login endpoint: `POST /api/auth/login/`

### 2. **Multi-Tenant Organization** ✅
- Organizations with unique slugs
- Users belong to single organization
- User roles: admin, analyst, reviewer
- All data filtered by organization automatically

### 3. **File Upload & Ingestion** ✅
- Upload CSV/JSON files from 3 data sources:
  - **SAP Fuel Feed** (CSV with fuel consumption data)
  - **Utility Portal** (CSV with electricity usage)
  - **Travel Expense API** (JSON with travel distances)
- Files stored in `media/uploads/{org_id}/{filename}`
- Automatic ingestion pipeline triggers on upload

### 4. **Data Processing Pipeline** ✅
- **Parse:** Extract records from various file formats
- **Validate:** Check required fields and data quality
- **Normalize:** Convert to standard emission units
- **Detect Anomalies:** Flag suspicious values (outliers, negative quantities)
- **Audit Log:** Track all actions with user/timestamp/reason

### 5. **Review & Approval** ✅
- Pending emission records queued for review
- Reviewers can approve/reject with comments
- Status tracking: pending_review → approved/rejected
- Audit trail for all decisions

### 6. **Dashboard & Analytics** ✅
- Real-time metrics: Total records, approved, pending, failed counts
- Recent ingestion jobs list
- Anomaly flag summaries
- Audit log viewer

---

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/refresh/` - Refresh access token

### Data Sources
- `GET /api/data-sources/` - List configured data sources
- `GET /api/data-sources/{id}/` - Get specific source

### Ingestion
- `GET /api/ingestion-jobs/` - List upload jobs
- `POST /api/ingestion-jobs/upload/` - Upload new file
  - Form data: `file`, `data_source_id`

### Emissions Review
- `GET /api/emissions/` - List all emission records
- `GET /api/emissions/review-queue/` - Pending records for review
- `POST /api/emissions/{id}/approve/` - Approve record
- `POST /api/emissions/{id}/reject/` - Reject record with reason
- `GET /api/emissions/{id}/` - Get record details

### Audit
- `GET /api/audit-logs/` - View all audit logs
- `GET /api/audit-logs/?record_id={id}` - Logs for specific record

---

## Database

### SQLite (Default)

Uses SQLite by default for simplicity. Database file: `backend/db.sqlite3`

**To reset database:**
```bash
rm db.sqlite3
python manage.py migrate
python manage.py shell < manage_commands/seed_data.py
```

### PostgreSQL (Optional)

To use PostgreSQL instead:

1. Install PostgreSQL and create database:
   ```bash
   createdb breathe_esg
   ```

2. Update `.env`:
   ```
   USE_SQLITE=False
   DATABASE_URL=postgresql://user:password@localhost/breathe_esg
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

---

## Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'django'"**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**"Connection refused" when accessing `/api/`**
- Ensure backend is running: `python manage.py runserver 0.0.0.0:8000`
- Check port 8000 is not in use: `lsof -i :8000`

**Database locked errors**
- Delete `db.sqlite3` and rerun migrations if corrupted

### Frontend Issues

**"Cannot GET /api/..."**
- Ensure backend server is running on port 8000
- Check Vite proxy config in `vite.config.ts`

**"localhost:3001 refused connection"**
- Run `npm run dev` in frontend directory
- Check port 3001 is not in use: `lsof -i :3001`

### CORS Errors

Verify `CORS_ALLOWED_ORIGINS` in `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]
```

---

## Development Workflow

### Making Changes

1. **Backend:** Edit files in `backend/breathe/`, `backend/ingestion/`, etc.
   - No restart needed for Django (uses auto-reload)
   - Check console for errors

2. **Frontend:** Edit files in `frontend/src/`
   - Vite HMR auto-reloads on save
   - Check browser console for errors

### Running Tests

```bash
cd backend
pytest tests/
```

### Database Queries

```bash
cd backend
python manage.py shell
```

Example:
```python
from organizations.models import User, Organization
from emissions.models import NormalizedEmissionRecord

# Check user
user = User.objects.get(email='analyst@example.com')
print(f"User: {user.email}, Org: {user.organization.name}")

# Check records
records = NormalizedEmissionRecord.objects.filter(organization=user.organization)
print(f"Total records: {records.count()}")
```

---

## Project Structure

```
breathe/
├── backend/
│   ├── breathe/              # Django config & settings
│   ├── organizations/        # User & org models
│   ├── ingestion/           # File upload & parsing
│   ├── emissions/           # Record review & approval
│   ├── data_sources/        # Data source configs
│   ├── audit/               # Audit logging
│   ├── manage.py
│   ├── db.sqlite3           # SQLite database
│   ├── requirements.txt
│   └── venv/                # Virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # Reusable UI components
│   │   ├── api/             # API client code
│   │   ├── stores/          # Zustand state management
│   │   └── App.tsx
│   ├── vite.config.ts
│   ├── package.json
│   └── node_modules/
│
└── README.md
```

---

## Next Steps

### Basic Usage Flow

1. **Login:** Use analyst@example.com / testpass123
2. **View Dashboard:** See ingestion metrics
3. **Upload File:** Go to Ingestions → Select data source → Upload CSV/JSON
4. **Review Records:** Go to Review Queue → Approve/Reject pending records
5. **View Audit Trail:** Check Audit Logs for all actions

### Extend the Platform

1. **Add New Data Source:**
   - Create parser in `backend/ingestion/parsers/`
   - Create validator in `backend/ingestion/validators/`
   - Create normalizer in `backend/ingestion/normalizers/`
   - Register in `IngestionService.process_job()`

2. **Custom Anomaly Detection:**
   - Extend `AnomalyDetectionService` in `backend/emissions/anomaly_detection.py`
   - Configure thresholds and rules

3. **Frontend Customization:**
   - All pages in `frontend/src/pages/`
   - Styling with TailwindCSS (see `tailwind.config.js`)
   - API client in `frontend/src/api/`

---

## Performance Notes

- **SQLite:** Good for development and single-user scenarios; not for production
- **Ingestion:** Currently processes files synchronously; use Celery for async processing
- **Caching:** Consider Redis for caching frequently accessed data
- **Database Indexes:** Currently all indexed for standard queries; add custom for specific workflows

---

## Support

For issues or questions:

1. Check `troubleshooting` section above
2. Review Django/React error messages in console
3. Check database state: `python manage.py dbshell`
4. View API responses: Use browser DevTools or `curl`

---

**Last Updated:** May 2026
**Version:** 1.0.0
**Python:** 3.12
**Django:** 4.2.11
**React:** 18.2.0
