"""Audit logging service."""
from django.utils import timezone
from audit.models import AuditLog


class AuditService:
    """Service for logging auditable actions."""
    
    @staticmethod
    def log_action(user, record_id, record_type, action, previous_value=None, new_value=None, change_reason=''):
        """
        Log an action to the audit trail.
        Always creates immutable records.
        """
        # Ensure organization is available
        organization_id = None
        if user and hasattr(user, 'organization_id'):
            organization_id = user.organization_id
        
        audit_log = AuditLog.objects.create(
            organization_id=organization_id,
            user=user,
            record_id=str(record_id),
            record_type=record_type,
            action=action,
            previous_value=previous_value,
            new_value=new_value,
            change_reason=change_reason,
        )
        
        return audit_log
    
    @staticmethod
    def get_record_history(organization_id, record_id):
        """Get complete change history for a record."""
        return AuditLog.objects.filter(
            organization_id=organization_id,
            record_id=str(record_id)
        ).order_by('-created_at')
