from django.contrib import admin
from audit.models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'record_type', 'created_at')
    list_filter = ('action', 'record_type', 'created_at')
    search_fields = ('record_id',)
    readonly_fields = ('id', 'created_at', 'previous_value', 'new_value')
