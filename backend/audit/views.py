from rest_framework import viewsets, permissions
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from breathe.permissions import IsAuthenticatedAndSetOrganization


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only audit log.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            queryset = AuditLog.objects.filter(
                organization=self.request.organization
            )
            
            # Filter by action
            action = self.request.query_params.get('action')
            if action:
                queryset = queryset.filter(action=action)
            
            # Filter by record type
            record_type = self.request.query_params.get('record_type')
            if record_type:
                queryset = queryset.filter(record_type=record_type)
            
            # Filter by user
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            return queryset.order_by('-created_at')
        
        return AuditLog.objects.none()
