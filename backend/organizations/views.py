from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from organizations.models import Organization, User
from organizations.serializers import OrganizationSerializer, UserSerializer, UserCreateSerializer, UserDetailSerializer
from breathe.permissions import IsAuthenticatedAndSetOrganization


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Organizations (tenants).
    Only authenticated users can view their own organization.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Organization.objects.filter(users=self.request.user)
        return Organization.objects.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's organization."""
        if hasattr(request, 'organization') and request.organization:
            serializer = self.get_serializer(request.organization)
            return Response(serializer.data)
        return Response({'detail': 'No organization found.'}, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ModelViewSet):
    """
    Users scoped to organization.
    """
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            return User.objects.filter(organization=self.request.organization)
        return User.objects.none()
    
    def perform_create(self, serializer):
        """Only admins can create users."""
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can create users.")
        serializer.save(organization=self.request.organization)
