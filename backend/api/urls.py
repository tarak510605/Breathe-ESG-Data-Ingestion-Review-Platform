from django.urls import path, include
from rest_framework.routers import DefaultRouter
from organizations.views import OrganizationViewSet, UserViewSet
from data_sources.views import DataSourceViewSet, EmissionFactorViewSet
from ingestion.views import IngestionJobViewSet
from emissions.views import NormalizedEmissionRecordViewSet, AnomalyFlagViewSet
from audit.views import AuditLogViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'users', UserViewSet, basename='user')
router.register(r'data-sources', DataSourceViewSet, basename='data-source')
router.register(r'emission-factors', EmissionFactorViewSet, basename='emission-factor')
router.register(r'ingestion-jobs', IngestionJobViewSet, basename='ingestion-job')
router.register(r'emissions', NormalizedEmissionRecordViewSet, basename='emission-record')
router.register(r'anomalies', AnomalyFlagViewSet, basename='anomaly-flag')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
