"""
Middleware for tenant isolation and audit logging.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from organizations.models import Organization

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Scopes queries to current organization.
    Extracts org_id from JWT token or request headers.
    """
    
    def process_request(self, request):
        # Try to extract org_id from headers
        org_id = request.META.get('HTTP_X_ORG_ID')
        
        # If user is authenticated, use their organization
        if request.user and request.user.is_authenticated:
            try:
                # User has a direct FK to organization
                org = request.user.organization
                request.organization = org
                request.organization_id = str(org.id)
                logger.info(f"Middleware: User {request.user.username} org={org.id}")
            except (Organization.DoesNotExist, AttributeError) as e:
                request.organization = None
                request.organization_id = None
                logger.error(f"Middleware: Failed to get org for user {request.user.username}: {e}")
        else:
            request.organization = None
            request.organization_id = None
            logger.info(f"Middleware: User not authenticated")
        
        return None


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Logs request/response for audit trail.
    Can be extended to log data modifications.
    """
    
    def process_request(self, request):
        request.audit_data = {
            'method': request.method,
            'path': request.path,
            'user': request.user if request.user.is_authenticated else None,
        }
        return None
