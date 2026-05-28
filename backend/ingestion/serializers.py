from rest_framework import serializers
from ingestion.models import IngestionJob, RawRecord


class IngestionJobSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    
    class Meta:
        model = IngestionJob
        fields = [
            'id',
            'organization',
            'data_source',
            'data_source_name',
            'status',
            'file_name',
            'file_size',
            'total_records',
            'valid_records',
            'invalid_records',
            'suspicious_records',
            'processed_at',
            'processing_error',
            'uploaded_by',
            'uploaded_by_email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'total_records',
            'valid_records',
            'invalid_records',
            'suspicious_records',
            'processed_at',
            'processing_error',
            'created_at',
            'updated_at'
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = [
            'id',
            'organization',
            'ingestion_job',
            'raw_data',
            'source_line_number',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
