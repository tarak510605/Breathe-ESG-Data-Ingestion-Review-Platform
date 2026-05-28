from rest_framework import viewsets, permissions
from data_sources.models import DataSource, EmissionFactor
from data_sources.serializers import DataSourceSerializer, EmissionFactorSerializer
from breathe.permissions import IsAuthenticatedAndSetOrganization
import logging

logger = logging.getLogger(__name__)


class DataSourceViewSet(viewsets.ModelViewSet):
    """
    Data source configurations.
    """
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_queryset(self):
        logger.info(f"User: {self.request.user}, Has org attr: {hasattr(self.request, 'organization')}")
        if hasattr(self.request, 'organization'):
            logger.info(f"Organization: {self.request.organization}")
        qs = DataSource.objects.all()
        logger.info(f"Total DataSources in DB: {qs.count()}")
        if hasattr(self.request, 'organization') and self.request.organization:
            qs = qs.filter(organization=self.request.organization)
            logger.info(f"Filtered by org {self.request.organization}: {qs.count()}")
            return qs
        logger.warning("No organization set on request!")
        return DataSource.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class EmissionFactorViewSet(viewsets.ModelViewSet):
    """
    Emission conversion factors.
    """
    serializer_class = EmissionFactorSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            return EmissionFactor.objects.filter(organization=self.request.organization)
        return EmissionFactor.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)
