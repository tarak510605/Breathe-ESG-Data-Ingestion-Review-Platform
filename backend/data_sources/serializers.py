from rest_framework import serializers
from data_sources.models import DataSource, EmissionFactor


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            'id',
            'organization',
            'name',
            'source_type',
            'is_active',
            'connection_config',
            'field_mappings',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = [
            'id',
            'organization',
            'source_unit',
            'target_unit',
            'factor_value',
            'factor_type',
            'description',
            'effective_from',
            'effective_to',
            'source_reference',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
