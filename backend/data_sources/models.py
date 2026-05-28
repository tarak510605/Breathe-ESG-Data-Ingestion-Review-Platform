import uuid
from django.db import models
from organizations.models import Organization


class DataSource(models.Model):
    """Configuration for data ingestion sources."""
    SOURCE_TYPE_CHOICES = [
        ('sap_csv', 'SAP CSV Export'),
        ('utility_csv', 'Utility Portal CSV'),
        ('travel_api', 'Travel Expense API'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='data_sources')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    
    # Connection config stored as JSON for flexibility
    connection_config = models.JSONField(default=dict, blank=True)
    
    # Field mappings for CSV sources
    field_mappings = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_sources_datasource'
        unique_together = [['organization', 'name']]
        indexes = [
            models.Index(fields=['organization', 'source_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"


class EmissionFactor(models.Model):
    """Emission conversion factors with time-based versioning."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='emission_factors')
    
    source_unit = models.CharField(max_length=50)  # "liters", "kWh", "km", etc.
    target_unit = models.CharField(max_length=50, default='kg_co2e')
    
    # Factor value (e.g., 2.31 kg CO2e per liter of gasoline)
    factor_value = models.DecimalField(max_digits=12, decimal_places=6)
    
    # Classification
    factor_type = models.CharField(max_length=100)  # "fuel_type_diesel", "grid_electricity_us_west"
    description = models.TextField(blank=True)
    
    # Effective dates for versioning
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    # Source reference for transparency
    source_reference = models.CharField(max_length=255, blank=True)  # "EPA eGRID 2023", "DEFRA 2023"
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_sources_emission_factor'
        unique_together = [['organization', 'source_unit', 'factor_type', 'effective_from']]
        indexes = [
            models.Index(fields=['organization', 'factor_type', 'effective_from']),
        ]
    
    def __str__(self):
        return f"{self.factor_type}: {self.factor_value} {self.target_unit}/{self.source_unit}"
