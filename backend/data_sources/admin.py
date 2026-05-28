from django.contrib import admin
from data_sources.models import DataSource, EmissionFactor

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'source_type', 'is_active')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name',)

@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ('factor_type', 'organization', 'factor_value', 'effective_from')
    list_filter = ('factor_type', 'effective_from')
    search_fields = ('factor_type',)
