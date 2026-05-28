from django.contrib import admin
from ingestion.models import IngestionJob, RawRecord

@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'data_source', 'status', 'created_at')
    list_filter = ('status', 'data_source')
    search_fields = ('file_name', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'ingestion_job', 'source_line_number', 'created_at')
    list_filter = ('ingestion_job',)
    readonly_fields = ('id', 'raw_data', 'created_at')
