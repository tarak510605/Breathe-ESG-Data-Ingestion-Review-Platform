# Getting Started

## Quick Start (5 minutes)

### Option 1: Docker (Recommended)

```bash
cd breathe
docker-compose up
```

Then in another terminal:
```bash
docker-compose exec backend python manage.py shell < manage_commands/seed_data.py
```

Open http://localhost:3000 and login with:
- Email: `analyst@example.com`
- Password: `testpass123`

### Option 2: Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py shell < manage_commands/seed_data.py
python manage.py runserver
```

#### Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## File Structure

```
breathe/
├── backend/                 # Django application
│   ├── breathe/            # Project settings
│   ├── organizations/      # Orgs & users
│   ├── data_sources/       # Data source configs
│   ├── ingestion/          # File upload & parsing
│   │   ├── parsers/        # CSV/JSON parsers
│   │   ├── validators/     # Data quality checks
│   │   └── normalizers/    # Data transformation
│   ├── emissions/          # Records & review
│   ├── audit/              # Audit logging
│   ├── manage.py
│   ├── requirements.txt
│   └── sample_data/        # Test CSVs
│
├── frontend/               # React application
│   ├── src/
│   │   ├── api/           # API clients
│   │   ├── pages/         # Pages
│   │   ├── components/    # React components
│   │   ├── stores/        # Zustand state
│   │   └── index.tsx      # Entry point
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml      # Local development
├── Dockerfile              # Backend image
├── README.md               # Main docs
├── ARCHITECTURE.md         # System design
├── DECISIONS.md            # Design choices
├── TRADEOFFS.md            # Tradeoffs made
└── DEPLOYMENT.md           # Deployment guide

```

## First Steps

1. **Upload test data**
   - Go to Ingestions → New Upload
   - Select "SAP Fuel Feed"
   - Upload `backend/sample_data/sap_fuel_export.csv`
   - Watch as system parses, validates, and normalizes

2. **Review records**
   - Go to Review Queue
   - See pending emissions records
   - Click to view details and anomalies
   - Approve or reject

3. **Check audit trail**
   - Click any record
   - View complete change history
   - See who made changes when

## Key Concepts

### Multi-Tenant
- Each organization is completely isolated
- Users belong to one organization
- Data is scoped by `organization_id`

### Immutable Records
- `RawRecord` never modified (original data)
- `AuditLog` tracks all changes
- Locked after approval

### Role-Based Access
- **Admin**: Manage org & users
- **Analyst**: Upload & edit records
- **Reviewer**: Approve/reject records

### Emission Scopes
- **Scope 1**: Direct fuel combustion
- **Scope 2**: Purchased electricity
- **Scope 3**: Travel & indirect

## API Examples

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"testpass123"}'
```

### Upload File
```bash
curl -X POST http://localhost:8000/api/ingestion-jobs/upload/ \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@sample_data/sap_fuel_export.csv" \
  -F "data_source_id=<id>"
```

### Get Records
```bash
curl -X GET http://localhost:8000/api/emissions/?page=1 \
  -H "Authorization: Bearer TOKEN"
```

### Approve Record
```bash
curl -X POST http://localhost:8000/api/emissions/<id>/approve/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment":"Looks good"}'
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Reset database
python manage.py migrate --zero
python manage.py migrate
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
npm install
```

## Environment Variables

See `.env.example` for all available options:
- `DJANGO_SECRET_KEY` - Django secret
- `POSTGRES_PASSWORD` - Database password
- `DEBUG` - Debug mode (False in production)
- `ALLOWED_HOSTS` - Allowed domains
- `CORS_ALLOWED_ORIGINS` - Frontend URL

## Common Tasks

### Create Admin User
```bash
python manage.py createsuperuser
```

### Run Migrations
```bash
python manage.py migrate
```

### Load Sample Data
```bash
python manage.py shell < manage_commands/seed_data.py
```

### Access Django Admin
Visit http://localhost:8000/admin

## Next Steps

1. **Upload your data** - Try different CSV formats
2. **Configure emission factors** - Adjust for your region
3. **Set up team** - Add analyst and reviewer users
4. **Review records** - Build approval workflow
5. **Deploy** - See DEPLOYMENT.md for production setup

## Documentation

- **ARCHITECTURE.md** - System design & database schema
- **DECISIONS.md** - Why we chose each technology
- **TRADEOFFS.md** - Performance vs features
- **DEPLOYMENT.md** - Production deployment

## Support

- Check application logs: `docker-compose logs -f backend`
- Review API docs at `/api/schema/`
- Read docstrings in service layer
- Check test files for usage examples

---

Happy ingesting! 🌍
