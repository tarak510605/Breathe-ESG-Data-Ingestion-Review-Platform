import uuid
from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization

User = get_user_model()


class AuditLog(models.Model):
    """Immutable audit trail of all changes."""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
        ('comment_added', 'Comment Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    
    # Record being modified
    record_id = models.UUIDField()  # Generic record ID (can be EmissionRecord, DataSource, etc.)
    record_type = models.CharField(max_length=50)  # "NormalizedEmissionRecord", "DataSource", etc.
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Change tracking
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    change_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_audit_log'
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['record_id', 'record_type']),
            models.Index(fields=['user', 'action']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} on {self.created_at}"
