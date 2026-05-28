from rest_framework import serializers
from emissions.models import NormalizedEmissionRecord, AnomalyFlag


class AnomalyFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyFlag
        fields = [
            'id',
            'normalized_record',
            'anomaly_type',
            'severity',
            'description',
            'metric_name',
            'threshold_value',
            'actual_value',
            'is_resolved',
            'analyst_note',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NormalizedEmissionRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    anomalies = AnomalyFlagSerializer(many=True, read_only=True)
    
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'id',
            'emission_category',
            'emission_source',
            'quantity',
            'unit',
            'emissions_kg_co2e',
            'period_start',
            'period_end',
            'facility_code',
            'status',
            'review_decision',
            'anomalies',
            'is_locked',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'emissions_kg_co2e',
            'created_at'
        ]


class NormalizedEmissionRecordDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with audit trail."""
    anomalies = AnomalyFlagSerializer(many=True, read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True)
    
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'id',
            'raw_record',
            'data_source',
            'ingestion_job',
            'emission_category',
            'emission_source',
            'quantity',
            'unit',
            'emissions_kg_co2e',
            'period_start',
            'period_end',
            'facility_code',
            'source_reference_id',
            'asset_id',
            'currency',
            'cost',
            'status',
            'review_decision',
            'original_value',
            'edited_value',
            'review_notes',
            'is_locked',
            'reviewed_by',
            'reviewed_by_email',
            'review_timestamp',
            'review_comment',
            'anomalies',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'raw_record',
            'original_value',
            'created_at',
            'updated_at'
        ]


class NormalizedEmissionRecordEditSerializer(serializers.ModelSerializer):
    """Serializer for analyst edits."""
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'quantity',
            'unit',
            'emissions_kg_co2e',
            'facility_code',
            'asset_id',
            'cost',
            'currency',
            'review_notes'
        ]
    
    def update(self, instance, validated_data):
        # Capture edited value before update
        if not instance.edited_value:
            instance.edited_value = {
                'quantity': str(instance.quantity),
                'unit': instance.unit,
                'facility_code': instance.facility_code,
            }
        
        # Update fields
        for attr, value in validated_data.items():
            if attr != 'emissions_kg_co2e':
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class NormalizedEmissionRecordApproveSerializer(serializers.Serializer):
    """Serializer for approval action."""
    comment = serializers.CharField(required=False, allow_blank=True)


class NormalizedEmissionRecordRejectSerializer(serializers.Serializer):
    """Serializer for rejection action."""
    reason = serializers.CharField(required=True)
