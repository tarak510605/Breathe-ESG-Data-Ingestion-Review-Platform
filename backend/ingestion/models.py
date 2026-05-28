import uuid
from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization
from data_sources.models import DataSource

User = get_user_model()


class IngestionJob(models.Model):
    """Batch ingestion unit tracking."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ingestion_jobs')
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='ingestion_jobs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)  # S3 or local path
    file_size = models.BigIntegerField()  # bytes
    
    # Counters
    total_records = models.IntegerField(default=0)
    valid_records = models.IntegerField(default=0)
    invalid_records = models.IntegerField(default=0)
    suspicious_records = models.IntegerField(default=0)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_jobs')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ingestion_ingestion_job'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['data_source', 'status']),
        ]
    
    def __str__(self):
        return f"Job {self.id} - {self.file_name}"


class RawRecord(models.Model):
    """Immutable raw data as received from source."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='raw_records')
    ingestion_job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='raw_records')
    
    # Original unparsed data - NEVER UPDATED
    raw_data = models.JSONField()
    
    # Metadata
    source_line_number = models.IntegerField()  # Line number in source file
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ingestion_raw_record'
        indexes = [
            models.Index(fields=['organization', 'ingestion_job']),
        ]
    
    def __str__(self):
        return f"RawRecord {self.id} from {self.ingestion_job.file_name}"
