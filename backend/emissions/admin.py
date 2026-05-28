from django.contrib import admin
from emissions.models import NormalizedEmissionRecord, AnomalyFlag

@admin.register(NormalizedEmissionRecord)
class NormalizedEmissionRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'emission_category', 'status', 'created_at')
    list_filter = ('status', 'emission_category', 'review_decision')
    search_fields = ('facility_code', 'source_reference_id')
    readonly_fields = ('id', 'original_value', 'created_at', 'updated_at')

@admin.register(AnomalyFlag)
class AnomalyFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'anomaly_type', 'severity', 'is_resolved')
    list_filter = ('anomaly_type', 'severity', 'is_resolved')
    readonly_fields = ('id', 'created_at')
