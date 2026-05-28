# Architecture Tradeoffs & Limitations

## Performance Tradeoffs

### 1. **Synchronous Processing vs Async Jobs**

**Chosen:** Synchronous inline processing

**Pros:**
- Simple implementation
- Immediate feedback (job status in response)
- Easy debugging (stack traces in sync code)
- Works for files < 10MB

**Cons:**
- Request can timeout if file is large (10K+ records)
- Database writes block subsequent uploads
- No progress indicator for users

**When to Change:**
- File sizes regularly > 50MB
- > 10 concurrent uploads/minute
- Analysts complain about timeout

**How to Implement Async (Without Rewriting):**
```
1. Create IngestionJob immediately (status=pending)
2. Return job_id to client
3. Enqueue Celery task to process_job(job_id)
4. Frontend polls GET /api/ingestion/jobs/{id}/ for status
5. Service layer doesn't know if execution is sync or async
```

**Recommendation:** Start sync, add async when load testing shows bottleneck.

---

### 2. **PostgreSQL Full-Table Scans vs Indexes**

**Chosen:** Minimal indexes initially (PK, FK, org_id)

**Pros:**
- Simpler schema
- Writes faster
- Maintenance burden is low
- PostgreSQL query planner is smart

**Cons:**
- Queries on `email`, `facility_code`, `period_start` are slow at scale
- No text search on audit logs

**When to Add Indexes:**
- Query logs show sequential scans > 1 sec
- Dashboard metrics queries timeout
- Audit log search is unusable

**Indexes to Add Later:**
```sql
CREATE INDEX idx_normalized_records_facility_code ON emissions_normalizedemissionrecord(organization_id, facility_code);
CREATE INDEX idx_normalized_records_period ON emissions_normalizedemissionrecord(organization_id, period_start, period_end);
CREATE INDEX idx_audit_logs_timestamp ON audit_auditlog(organization_id, created_at DESC);
```

---

### 3. **Heuristic Anomaly Detection vs Machine Learning**

**Chosen:** Rule-based heuristics (IQR outliers, format validation)

**Pros:**
- Explainable ("Why did you flag this record?")
- No training data required
- Runs instantly during ingestion
- Easy for analysts to override
- No model drift risk

**Cons:**
- Cannot detect contextual anomalies ("This company's emissions are 10x their peers")
- Cannot detect seasonal patterns
- High false-positive rate possible
- Requires manual tuning of thresholds

**When to Upgrade to ML:**
- Sufficient labeled data (> 10K flagged records)
- Repeated patterns in what analysts flag
- Business case: saves X hours per analyst

**Potential Approach:**
```
1. Collect labeled historical data (approved vs rejected)
2. Train isolation forest for outlier detection
3. Keep rule-based system as first filter
4. Use ML confidence score as secondary check
5. A/B test with analysts
```

---

### 4. **Single Database for All Tenants vs Per-Tenant Databases**

**Chosen:** Single PostgreSQL database, filtered by `organization_id`

**Pros:**
- Simple operations (one DB to backup, patch, monitor)
- Data easy to join across orgs (if audit needed)
- Cheaper than N databases
- Easier development experience

**Cons:**
- A SQL injection could expose all tenants
- One tenant's slow query affects others
- Harder to isolate resource usage per tenant
- Database migration affects all tenants at once

**Risk Mitigation:**
- Parametrized queries (Django ORM prevents SQL injection)
- Connection pooling to prevent runaway connections
- Monitoring per-org query patterns
- Prepared statements

**When to Split to Per-Tenant DBs:**
- > 100 organizations
- Security/compliance requires data isolation
- One org has significantly higher volume
- Need per-org backups with different retention

---

## Architectural Tradeoffs

### 5. **Service Layer Abstraction vs Thin Views**

**Chosen:** Service layer (IngestionService, ReviewQueueService, etc.)

**Pros:**
- Business logic reusable (can call from API or CLI)
- Easier to test (mock services)
- Decoupled from Django (could swap framework)
- Clear separation of concerns

**Cons:**
- Extra indirection (views → services → ORM)
- More classes to navigate
- Junior devs might find it confusing

**Alternative (Django Way):**
```python
# Thin views, logic in model managers
class IngestionJobQuerySet(QuerySet):
    def pending(self):
        return self.filter(status='pending')
    def process_all(self):
        for job in self:
            job.process()
```

**Recommendation:** Service layer is worth it here. Keeps business logic testable and organized.

---

### 6. **Flexible JSONB vs Rigid Schema**

**Chosen:** `RawRecord.raw_data` is JSONB (flexible), `NormalizedEmissionRecord` has rigid fields

**Pros:**
- Raw data accepts any CSV/JSON format without schema changes
- Can add new source types without migration
- Storage efficient for sparse data

**Cons:**
- JSONB not as queryable as columns
- No type checking at DB level
- Duplicate data (snapshots in `original_value`)

**When to Normalize:**
- If majority of raw data follows same pattern
- If queries on raw data become common

---

### 7. **Enum Fields vs Foreign Keys**

**Chosen:** Enums for `status`, `emission_category`, `anomaly_type`, `review_decision`

**Rationale:**
- These are stable reference data (not changing per-org)
- Simpler queries ("emissions WHERE emission_category = 'scope_1_fuel'")
- No lookups needed
- PostgreSQL ENUM type is efficient

**Exceptions:**
- `EmissionFactor` is FK (organization-specific)
- `DataSource` is FK (per-org configuration)
- `User` is FK (per-org users)

---

### 8. **Immutable Audit Logs vs Updateable History**

**Chosen:** Immutable `AuditLog` (write-once)

**Pros:**
- Cannot be tampered with
- Compliance (regulators like immutable trails)
- Simple (no versioning)

**Cons:**
- Cannot correct mistakes in audit log
- Bloats table if logging too much

**Alternative:**
```
Updateable audit logs with meta-audit
- AuditLog can be updated (with reason)
- MetaAuditLog tracks changes to AuditLog
- More complex, diminishing ROI
```

**Recommendation:** Keep immutable. Mistakes are rare, and they're useful to track anyway.

---

## Data Quality Tradeoffs

### 9. **Analyst Edit Permission vs Immutable Records**

**Chosen:** Analysts can edit after normalized validation fails, but approved records lock

**Pros:**
- Handles data entry errors (typo in facility code)
- Analysts not blocked by bad data
- Still auditable (change logged)

**Cons:**
- Analysts might bypass validation
- Could silently fix data quality issues
- Less discipline in source systems

**How to Prevent Abuse:**
```
1. Log every edit with reason
2. Approval required for edits (different person)
3. Dashboard shows "edited records" separately
4. PM reviews edited records monthly
```

**Alternative:**
- Reject invalid records, force reupload
- More disciplined but slower workflow

---

### 10. **Duplicate Detection Within Job vs Across Jobs**

**Chosen:** Detect duplicates only within a single job (not across time)

**Pros:**
- Simpler logic (only check uploaded data)
- No false positives from legitimate recurring records (same facility, monthly electricity)
- Faster detection (single job in memory)

**Cons:**
- Miss true duplicates if analyst uploads same file twice
- No cross-time dedup

**How to Improve Later:**
```python
# Flag if (organization, source, facility, period_start) uploaded twice in N days
def find_potential_resubmissions(record, days=30):
    similar = NormalizedEmissionRecord.objects.filter(
        organization=record.organization,
        data_source=record.data_source,
        facility_code=record.facility_code,
        period_start=record.period_start,
        created_at__gte=record.created_at - timedelta(days=days)
    ).exclude(id=record.id)
    return similar
```

**Trade-off:** Start simple, add cross-time dedup when needed.

---

## Feature Scope Tradeoffs

### 11. **No Bulk Approval Workflow**

**Not Implemented:** "Select 50 records and approve all at once"

**Rationale:**
- Most analysts review a few records at a time
- Batch approvals are risky (easy to approve wrong record)
- Single record API is cleaner

**When to Add:**
- Analytics show analysts batch-approving > 100 records/day
- Workflow becomes bottleneck

**Implementation:**
```
POST /api/emissions/bulk-approve/
{
  "record_ids": [id1, id2, ...],
  "require_individual_reason": false,
  "common_reason": "Spot checked, looks good"
}
```

---

### 12. **No Workflow States (Just Approved/Rejected/Pending)**

**Not Implemented:** "Needs More Info", "Re-reviewing", etc.

**Pros:**
- Simple state machine
- Easy to implement
- Works for typical flows

**Cons:**
- Analyst must choose between approve/reject
- No "put this back for analyst to fix" state

**Better Alternative:**
- If validation fails → analyst can edit (already have this)
- Edited records re-enter review queue automatically
- Simpler than adding intermediate states

---

### 13. **No Fine-Grained Permissions**

**Not Implemented:** "Analyst X can only approve records from source Y"

**Rationale:**
- Smaller teams (internship project)
- Permission rules would explode complexity
- Can add when org structure demands it

**If Needed:**
```python
class PermissionModel(models.Model):
    user = ForeignKey(User)
    organization = ForeignKey(Organization)
    
    can_upload = BooleanField()
    can_review = BooleanField()
    can_approve = BooleanField()
    
    # Fine-grained
    allowed_sources = JSONField()  # ["source_1", "source_2"]
    allowed_scopes = JSONField()   # ["scope_1", "scope_3"]
```

---

### 14. **No Time-Based Access Control**

**Not Implemented:** "User access revoked 30 days after hire date"

**Rationale:**
- HR system should manage this
- Can add if integrating with LDAP/Active Directory

---

## Deployment Tradeoffs

### 15. **Docker Compose for Local Dev, Not Production**

**Chosen:** docker-compose.yml works locally, but Dockerfile targets single process

**Pros:**
- Development env mirrors production structure
- Can test with PostgreSQL locally
- Portable

**Cons:**
- Not optimized for K8s or container orchestration
- No separate worker/scheduler containers

**Production Deployment:**
```
Option 1: Render or Railway (PaaS)
- Platform handles scaling
- Docker image builds automatically
- Environment variables via dashboard

Option 2: AWS ECS/EKS
- More control
- More complexity
```

---

### 16. **No Background Task Queue Initially**

**Chosen:** Synchronous processing

**Trade-off:** See #1 above (Performance Tradeoffs)

---

### 17. **No Analytics/Metrics Database**

**Not Implemented:** Separate OLAP database for reporting

**Rationale:**
- Single PostgreSQL sufficient for dashboard queries
- Reports are mostly status counts (fast)
- Can migrate to BigQuery later if needed

**If Reporting Becomes Bottleneck:**
```
1. Export records nightly to BigQuery
2. Dashboard queries BigQuery instead of PostgreSQL
3. OLTP/OLAP separation
```

---

## Data Modeling Tradeoffs

### 18. **No Versioning of Normalized Records**

**Current Design:** Edit updates record, AuditLog tracks change

**Alternative:** Keep versions (v1, v2, v3 of same record)

**Pros (Current):**
- Simpler schema
- Clearer what "approved" state is
- Less storage

**Cons (Current):**
- Can't see intermediate states if edited multiple times
- AuditLog is source of truth for history

**If Needed:**
```python
class NormalizedEmissionRecordVersion(models.Model):
    record = ForeignKey(NormalizedEmissionRecord)
    version_number = IntegerField()
    normalized_data = JSONField()
    edited_at = DateTimeField()
    edited_by = ForeignKey(User)
```

---

### 19. **Emission Factors Are Organization-Scoped**

**Chosen:** `EmissionFactor` has `organization_id` (each org can override factors)

**Pros:**
- Companies have different grid mix (electricity factor varies by region)
- Companies can use proprietary factors
- Allows white-label product

**Cons:**
- More storage (duplicated default factors)
- Requires maintenance (which org has outdated factors?)

**Alternative:**
- Global default factors + org-level overrides
- More complex (lookup hierarchy)

---

## Security Tradeoffs

### 20. **No Encryption at Rest**

**Chosen:** PostgreSQL stores data unencrypted

**Pros:**
- Simpler deployment
- Better query performance
- Standard for internship projects

**Cons:**
- If database stolen, all data exposed
- Regulatory requirements might demand encryption

**When to Add:**
- Healthcare/financial data (HIPAA/PCI)
- Handling PII (GDPR)

**Implementation:**
- PostgreSQL pgcrypto extension (field-level encryption)
- AWS RDS encryption (storage-level)
- Application-level encryption (slower, more flexible)

---

### 21. **No Rate Limiting**

**Chosen:** No rate limits on API endpoints

**Pros:**
- Simpler API
- Analysts won't be throttled
- No complexity

**Cons:**
- Brute force attacks possible
- Someone could hammer upload endpoint

**When to Add:**
- Deployed to public internet
- Seeing abuse in logs

**Implementation:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='POST')
def upload_file(request):
    ...
```

---

## What We Didn't Implement & Why

| Feature | Reason Not Included |
|---------|-------------------|
| OAuth2 / SAML | Corporate auth, can add with django-oauth-toolkit |
| Multi-language UI | Assume English-speaking teams |
| Dark mode | Nice-to-have, not core |
| Offline support | Not needed for analyst dashboard |
| Mobile app | Web app is sufficient |
| Batch edit UI | Single-record workflow is cleaner |
| Custom dashboards | Fixed dashboard sufficient initially |
| Data export to Data Lake | Add if needed later |
| Automated approvals | Humans should decide |
| ML anomaly detection | Start with rules |
| Cost tracking as core feature | Secondary to emissions |
| Travel distance API | Hardcoded estimated distances |
| Real-time collaboration | Unlikely to happen simultaneously |
| GraphQL | REST is simpler, no N+1 problems here |

---

## Recommendations for Extension

### Short-term (After MVP Works)
1. Add API documentation (Swagger/OpenAPI)
2. Add integration tests for each source type
3. Add pagination tests for edge cases
4. Performance baseline (load test)

### Medium-term (When Scale Increases)
1. Async job processing (Celery + Redis)
2. Full-text search on audit logs
3. Batch approve workflow
4. Per-org custom emission factors
5. Data export to CSV/Excel

### Long-term (When Product Matures)
1. Machine learning anomaly detection
2. Time-series analysis (trend detection)
3. Predictive analytics (forecast emissions)
4. Integration with ERP systems (live feeds vs batch uploads)
5. Benchmarking against industry peers
6. Custom reporting dashboards

---

## Questions to Answer with Stakeholders

1. **Data Retention:** How long to keep raw uploads? 7 years (legal)? Indefinitely?

2. **Audit Access:** Can analysts search audit logs? Or admin-only?

3. **Deletion:** Once a job is processed, can it be deleted? What about approved records?

4. **Multi-facility records:** Can one record represent multiple facilities (rolled-up)?

5. **Currency:** Should we track cost of carbon offsets in same system?

6. **Scope 4:** Do we need "avoided emissions" (e.g., renewable energy installed)?

7. **Seasonal adjustment:** Should we flag seasonal anomalies differently?

8. **Materiality threshold:** Is a 1 kg CO2e record material enough to track?

---

## Conclusion

This architecture prioritizes:
1. **Clarity** over cleverness
2. **Auditability** over performance
3. **Simplicity** over feature completeness
4. **Maintainability** over flexibility

The design is intentionally pared down for an internship project, but structured to scale to enterprise needs when required.
