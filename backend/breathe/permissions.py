"""
Custom permissions for tenant isolation.
"""
import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsAuthenticatedAndSetOrganization(permissions.IsAuthenticated):
    """
    Custom permission that:
    1. Ensures user is authenticated
    2. Sets request.organization from user's organization FK
    
    This runs AFTER DRF authentication, so the user is guaranteed to be set.
    """
    
    def has_permission(self, request, view):
        # First check if authenticated (will call parent's has_permission)
        if not super().has_permission(request, view):
            return False
        
        # Now set the organization on the request
        try:
            org = request.user.organization
            request.organization = org
            request.organization_id = str(org.id)
            logger.info(f"Permission: User {request.user.username} org={org.id}")
        except (AttributeError, Exception) as e:
            request.organization = None
            request.organization_id = None
            logger.error(f"Permission: Failed to set org for user {request.user.username}: {e}")
            return False
        
        return True
