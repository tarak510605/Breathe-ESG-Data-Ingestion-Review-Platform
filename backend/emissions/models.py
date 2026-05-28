import uuid
from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization
from data_sources.models import DataSource
from ingestion.models import IngestionJob, RawRecord

User = get_user_model()


class NormalizedEmissionRecord(models.Model):
    """Processed and reviewable emission record."""
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]
    
    EMISSION_CATEGORY_CHOICES = [
        ('scope_1_fuel', 'Scope 1 - Fuel Combustion'),
        ('scope_1_process', 'Scope 1 - Process Emissions'),
        ('scope_2_electricity', 'Scope 2 - Electricity'),
        ('scope_2_steam', 'Scope 2 - Steam/Heat'),
        ('scope_3_travel', 'Scope 3 - Travel'),
        ('scope_3_procurement', 'Scope 3 - Procurement'),
        ('scope_3_waste', 'Scope 3 - Waste'),
    ]
    
    REVIEW_DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='normalized_records')
    
    # Links to source data
    raw_record = models.OneToOneField(RawRecord, on_delete=models.PROTECT, related_name='normalized_record')
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='normalized_records')
    ingestion_job = models.ForeignKey(IngestionJob, on_delete=models.PROTECT, related_name='normalized_records')
    
    # Status and categorization
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    emission_category = models.CharField(max_length=50, choices=EMISSION_CATEGORY_CHOICES)
    emission_source = models.CharField(max_length=255)  # "Fleet Fuel", "Electricity", "Air Travel", etc.
    
    # Normalized values
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    unit = models.CharField(max_length=50)  # "kg_co2e", "kg", "kWh", "miles", etc.
    emissions_kg_co2e = models.DecimalField(max_digits=15, decimal_places=4)
    
    # Time period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Facility/Asset tracking
    facility_code = models.CharField(max_length=100, blank=True, null=True)
    source_reference_id = models.CharField(max_length=255, blank=True)  # Link back to source
    asset_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Financial tracking
    currency = models.CharField(max_length=10, blank=True, null=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Audit fields - capture state at creation
    original_value = models.JSONField()  # Snapshot of raw_record at creation
    edited_value = models.JSONField(null=True, blank=True)  # If analyst edited it
    
    # Review tracking
    review_notes = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False)  # Prevent edits after approval
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records')
    review_decision = models.CharField(max_length=20, choices=REVIEW_DECISION_CHOICES, default='pending')
    review_timestamp = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emissions_normalized_record'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'emission_category']),
            models.Index(fields=['organization', 'period_start', 'period_end']),
            models.Index(fields=['ingestion_job', 'status']),
            models.Index(fields=['facility_code', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.emission_source}: {self.quantity} {self.unit}"


class AnomalyFlag(models.Model):
    """Data quality flags for suspicious records."""
    ANOMALY_TYPE_CHOICES = [
        ('outlier', 'Statistical Outlier'),
        ('missing_field', 'Missing Required Field'),
        ('duplicate', 'Potential Duplicate'),
        ('invalid_format', 'Invalid Format'),
        ('suspicious_value', 'Suspicious Value'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.ForeignKey(
        NormalizedEmissionRecord,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='anomaly_flags')
    
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    description = models.TextField()
    
    # Context
    metric_name = models.CharField(max_length=100, blank=True)  # Field that triggered it
    threshold_value = models.CharField(max_length=255, blank=True, null=True)  # What threshold
    actual_value = models.CharField(max_length=255, blank=True, null=True)  # What was found
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    analyst_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emissions_anomaly_flag'
        indexes = [
            models.Index(fields=['organization', 'severity']),
            models.Index(fields=['normalized_record', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.anomaly_type} - {self.severity} ({self.description[:50]})"
