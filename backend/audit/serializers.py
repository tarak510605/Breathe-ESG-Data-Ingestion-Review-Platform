from rest_framework import serializers
from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'organization',
            'user',
            'user_email',
            'record_id',
            'record_type',
            'action',
            'previous_value',
            'new_value',
            'change_reason',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
