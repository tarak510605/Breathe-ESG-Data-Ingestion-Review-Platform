# Breathe ESG - Testing Guide

This guide walks through testing all features of the Breathe ESG platform locally.

## Prerequisites

- Both servers running:
  - Backend: `python manage.py runserver 0.0.0.0:8000`
  - Frontend: `npm run dev` (on port 3001)
- Login credentials: `analyst@example.com` / `testpass123`

---

## 1. Authentication Testing

### Test 1.1: Login with Valid Credentials

1. Navigate to [http://localhost:3001/login](http://localhost:3001/login)
2. Enter:
   - Email: `analyst@example.com`
   - Password: `testpass123`
3. Click **Login**

**Expected:** Redirected to Dashboard, token stored in localStorage

### Test 1.2: Invalid Credentials

1. Try login with wrong password
2. Should see error: "Invalid credentials"

**Expected:** Still on login page, no token created

### Test 1.3: Token Refresh

1. Login successfully
2. Wait 15+ minutes
3. Access API (Dashboard will auto-refresh token)

**Expected:** Access continues without re-login (automatic refresh)

---

## 2. Dashboard Testing

### Test 2.1: View Metrics

1. After login, should see Dashboard with 4 metric cards:
   - **Total Records** (should show number from database)
   - **Approved** (count of status='approved')
   - **Pending Review** (count of status='pending_review')
   - **Failed/Rejected** (count of status='rejected')

2. Check recent jobs list below

**Expected:** 
- Numbers match database state
- Jobs list shows recent uploads with status

### Test 2.2: Verify Data Source Selection

Frontend should have loaded 3 DataSources:
- SAP Fuel Feed
- Utility Portal  
- Travel Expense API

**Expected:** All 3 visible in Ingestions page dropdown

---

## 3. File Upload & Ingestion Testing

### Test 3.1: Upload SAP CSV

1. Go to **Ingestions** page
2. Select **SAP Fuel Feed** from dropdown
3. Click **Choose File** and select a CSV with columns:
   ```
   posting_date, plant_code, material_desc, quantity, unit
   2024-01-15, PLANT001, Diesel Fuel, 500, liters
   2024-01-15, PLANT001, Natural Gas, 1000, m³
   ```
4. Click **Upload**

**Expected:**
- Success message shown
- Job appears in Recent Jobs list with status="processing"
- Records added to database

### Test 3.2: Verify Ingestion Pipeline

1. After upload, wait 1-2 seconds
2. Open browser DevTools → Network tab
3. When upload completes, should see API calls:
   - `POST /api/ingestion-jobs/upload/` - File uploaded
   - Job status becomes "completed"
   - Check Dashboard for updated metrics

**Expected:**
- 2 new records created
- Dashboard metrics updated
- Records in "pending_review" status

---

## 4. Review Queue Testing

### Test 4.1: Access Review Queue

1. Go to **Review Queue** page
2. Should see table of records with columns:
   - Emission Source (e.g., "Fuel")
   - Quantity (e.g., "500.00")
   - Unit (e.g., "liters")
   - Status (should be "pending_review")
   - Anomalies (may show flags like "outlier")

**Expected:** List of pending records from uploads

### Test 4.2: Approve a Record

1. Click on a record to expand detail panel
2. Review details (should show emission source, quantity, calculated CO2e)
3. Click **Approve** button
4. Optional: Add approval comment
5. Confirm

**Expected:**
- Record status changes to "approved" in table
- Detail panel closes
- Dashboard metrics update (Pending decreases, Approved increases)

### Test 4.3: Reject a Record

1. Click on a different record
2. Click **Reject** button  
3. Enter reason (e.g., "Data quality issue")
4. Confirm

**Expected:**
- Record status changes to "rejected"
- Reason saved in audit trail
- Dashboard metrics update

### Test 4.4: View Anomalies

Some uploaded records may show anomalies:
- **Red flag** on table row = anomaly detected
- Click to see anomaly details (e.g., "Value exceeds normal range by 3x")

**Expected:** Anomalies clearly visible, reviewers can use to assess risk

---

## 5. Audit Log Testing

### Test 5.1: View All Logs

1. Go to **Audit Logs** page
2. Should see table with:
   - Timestamp
   - User (analyst@example.com)
   - Action (upload, approve, reject)
   - Record ID  
   - Details (file name, reason, etc.)

**Expected:** Entries for login, uploads, approvals, rejections

### Test 5.2: Filter by Record

1. From Review Queue, note a record ID
2. Go to Audit Logs
3. Filter by record ID (if filter available)
4. Should see all actions on that record

**Expected:** 
- Upload action
- Approve/Reject action
- All with user and timestamp

---

## 6. Multi-Source Parsing Testing

### Test 6.1: Upload Utility Portal CSV

1. Go to Ingestions
2. Select **Utility Portal** from dropdown
3. Upload CSV with columns:
   ```
   meter_id, billing_start, billing_end, consumption_kwh
   METER001, 2024-01-01, 2024-01-31, 5000
   METER002, 2024-01-01, 2024-01-31, 8000
   ```
4. Upload

**Expected:**
- 2 records created
- Status: "pending_review"
- emission_source: "Electricity"

### Test 6.2: Upload Travel Expense JSON

1. Go to Ingestions
2. Select **Travel Expense API** from dropdown
3. Upload JSON file:
   ```json
   {
     "trips": [
       {
         "origin": "New York",
         "destination": "Boston",
         "distance_km": 350,
         "date": "2024-01-15"
       }
     ]
   }
   ```
4. Upload

**Expected:**
- 1 record created
- Status: "pending_review"
- emission_source: "Travel"

---

## 7. Organization Filtering Testing

### Test 7.1: Verify Data Isolation

1. In database shell:
   ```bash
   python manage.py shell
   from organizations.models import Organization
   from emissions.models import NormalizedEmissionRecord
   
   org = Organization.objects.first()
   records = NormalizedEmissionRecord.objects.filter(organization=org)
   print(f"Org {org.name} has {records.count()} records")
   ```

2. API should only return records for user's organization:
   - `GET /api/emissions/` - Only filtered records
   - `GET /api/data-sources/` - Only org's sources

**Expected:**
- All records filtered by organization
- No data leakage between orgs
- Queries include `filter(organization=request.organization)`

---

## 8. Error Handling Testing

### Test 8.1: Upload Invalid File

1. Go to Ingestions
2. Try uploading a file with missing required columns
3. Should show validation error

**Expected:** 
- Error message on upload
- No partial data saved
- Job status: "failed"

### Test 8.2: Network Error Recovery

1. Stop backend server
2. Try API call from frontend (e.g., refresh dashboard)
3. Start backend again
4. Retry

**Expected:**
- Error shown gracefully
- Auto-retry works when server back online
- No data corruption

### Test 8.3: Duplicate Upload

1. Upload same file twice
2. Both should create separate IngestionJobs

**Expected:**
- Different job IDs
- Both processed independently
- Dashboard shows both jobs

---

## 9. Performance Testing

### Test 9.1: Bulk Upload

1. Create CSV with 1000 records
2. Upload to SAP Fuel Feed
3. Monitor browser DevTools Network tab
4. Check completion time

**Expected:**
- Upload takes <30 seconds
- Dashboard updates correctly
- No timeout errors

### Test 9.2: Dashboard with Many Records

1. Upload multiple files to create 100+ records
2. Go to Dashboard
3. Check load time and responsiveness

**Expected:**
- Page loads in <2 seconds
- Metrics calculate correctly  
- No UI freezing

---

## 10. Database State Verification

### Test 10.1: Check Schema

```bash
cd backend
python manage.py dbshell

-- Check tables exist
.tables

-- Sample counts
SELECT COUNT(*) FROM emissions_normalizedemissionrecord;
SELECT COUNT(*) FROM ingestion_ingestionjob;
SELECT COUNT(*) FROM audit_auditlog;
SELECT COUNT(*) FROM emissions_anomalyflag;
```

**Expected:**
- All tables present
- Record counts match dashboard metrics
- Foreign keys intact

### Test 10.2: Verify FK Constraints

```python
from ingestion.models import IngestionJob
from emissions.models import NormalizedEmissionRecord

# Check relationships work
job = IngestionJob.objects.first()
records = job.rawrecord_set.all()
normalized = NormalizedEmissionRecord.objects.filter(ingestion_job=job)
print(f"Job {job.id} has {records.count()} raw and {normalized.count()} normalized")
```

**Expected:**
- Relationships load correctly
- No orphaned records

---

## Complete Feature Checklist

Use this to track testing progress:

- [ ] 1.1 Login with valid credentials
- [ ] 1.2 Invalid credentials show error
- [ ] 1.3 Token auto-refresh works
- [ ] 2.1 Dashboard shows correct metrics
- [ ] 2.2 All 3 data sources available
- [ ] 3.1 SAP CSV upload succeeds
- [ ] 3.2 Ingestion pipeline completes
- [ ] 4.1 Review Queue shows pending records
- [ ] 4.2 Approve action works
- [ ] 4.3 Reject action works with reason
- [ ] 4.4 Anomalies visible on records
- [ ] 5.1 Audit logs display all actions
- [ ] 5.2 Can filter logs by record
- [ ] 6.1 Utility Portal CSV parsed
- [ ] 6.2 Travel Expense JSON parsed
- [ ] 7.1 Data isolated by organization
- [ ] 8.1 Invalid file shows error
- [ ] 8.2 Network errors handled gracefully
- [ ] 8.3 Duplicate uploads work
- [ ] 9.1 Bulk upload performs well
- [ ] 9.2 Dashboard responsive with many records
- [ ] 10.1 Database schema intact
- [ ] 10.2 Foreign key relationships work

---

## Common Issues & Solutions

### Login Fails with "Connection refused"

**Cause:** Backend not running

**Solution:**
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

### Upload Shows "Invalid File Format"

**Cause:** CSV/JSON columns don't match expected

**Solution:** Check parser for column names in:
- `backend/ingestion/parsers/sap_parser.py`
- `backend/ingestion/parsers/utility_parser.py`
- `backend/ingestion/parsers/travel_parser.py`

### Dashboard Shows Old Data

**Cause:** Browser cache

**Solution:**
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Or clear localStorage in DevTools

### Anomalies Not Showing

**Cause:** Thresholds too permissive

**Solution:** Adjust in `backend/emissions/anomaly_detection.py`:
```python
OUTLIER_THRESHOLD = 1.5  # IQR multiplier
```

---

## Next Steps

After all tests pass:

1. **Load Testing:** Use Apache Bench or k6 to test at scale
2. **Security Testing:** Test SQL injection, XSS, CSRF protections
3. **Integration Testing:** Add pytest fixtures for automated testing
4. **Documentation:** Generate API docs with Swagger/OpenAPI
5. **Deployment:** Package with Docker for production

---

**Last Updated:** May 2026
