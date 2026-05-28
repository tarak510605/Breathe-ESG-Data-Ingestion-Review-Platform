"""
Core business logic for ingestion processing.
"""
import csv
import json
import logging
from decimal import Decimal
from datetime import datetime
from django.core.files.storage import default_storage
from ingestion.models import IngestionJob, RawRecord
from emissions.models import NormalizedEmissionRecord, AnomalyFlag
from ingestion.parsers.sap_parser import SAPParser
from ingestion.parsers.utility_parser import UtilityParser
from ingestion.parsers.travel_parser import TravelParser
from ingestion.validators.sap_validator import SAPValidator
from ingestion.validators.utility_validator import UtilityValidator
from ingestion.validators.travel_validator import TravelValidator
from ingestion.normalizers.sap_normalizer import SAPNormalizer
from ingestion.normalizers.utility_normalizer import UtilityNormalizer
from ingestion.normalizers.travel_normalizer import TravelNormalizer
from emissions.anomaly_detection import AnomalyDetectionService
from audit.services import AuditService

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates the entire ingestion pipeline."""
    
    PARSER_MAP = {
        'sap_csv': SAPParser,
        'utility_csv': UtilityParser,
        'travel_api': TravelParser,
    }
    
    VALIDATOR_MAP = {
        'sap_csv': SAPValidator,
        'utility_csv': UtilityValidator,
        'travel_api': TravelValidator,
    }
    
    NORMALIZER_MAP = {
        'sap_csv': SAPNormalizer,
        'utility_csv': UtilityNormalizer,
        'travel_api': TravelNormalizer,
    }
    
    def __init__(self):
        self.anomaly_service = AnomalyDetectionService()
        self.audit_service = AuditService()
    
    def process_job(self, job: IngestionJob) -> None:
        """
        Main orchestration method.
        Parses file, validates, normalizes, detects anomalies.
        """
        try:
            job.status = 'processing'
            job.save()
            
            source_type = job.data_source.source_type
            
            # Get file
            file_content = default_storage.open(job.file_path).read()
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse
            parser_class = self.PARSER_MAP.get(source_type)
            if not parser_class:
                raise ValueError(f"Unknown source type: {source_type}")
            
            parser = parser_class()
            raw_records_data = parser.parse(file_content)
            
            # Create raw records in DB
            raw_records = []
            for idx, raw_data in enumerate(raw_records_data, 1):
                raw_record = RawRecord.objects.create(
                    organization=job.organization,
                    ingestion_job=job,
                    raw_data=raw_data,
                    source_line_number=idx
                )
                raw_records.append(raw_record)
            
            job.total_records = len(raw_records)
            job.save()
            
            # Validate, normalize, detect anomalies
            validator_class = self.VALIDATOR_MAP.get(source_type)
            normalizer_class = self.NORMALIZER_MAP.get(source_type)
            
            validator = validator_class()
            normalizer = normalizer_class()
            
            invalid_count = 0
            suspicious_count = 0
            valid_count = 0
            
            for raw_record in raw_records:
                try:
                    # Validate
                    is_valid, validation_errors = validator.validate(raw_record.raw_data)
                    
                    if not is_valid:
                        invalid_count += 1
                        logger.warning(f"Validation failed for record {raw_record.source_line_number}: {validation_errors}")
                        continue
                    
                    # Normalize
                    normalized_data = normalizer.normalize(
                        raw_record.raw_data,
                        job.organization,
                        job.data_source
                    )
                    
                    # Create normalized record
                    normalized_record = NormalizedEmissionRecord.objects.create(
                        organization=job.organization,
                        raw_record=raw_record,
                        data_source=job.data_source,
                        ingestion_job=job,
                        **normalized_data,
                        original_value=raw_record.raw_data,
                        status='pending_review',
                        review_decision='pending'
                    )
                    
                    # Detect anomalies
                    anomalies = self.anomaly_service.detect_anomalies(normalized_record)
                    
                    if anomalies:
                        suspicious_count += 1
                        for anomaly_data in anomalies:
                            AnomalyFlag.objects.create(
                                normalized_record=normalized_record,
                                organization=job.organization,
                                **anomaly_data
                            )
                    
                    valid_count += 1
                    
                except Exception as e:
                    invalid_count += 1
                    logger.error(f"Error processing record {raw_record.source_line_number}: {str(e)}")
            
            # Update job
            job.valid_records = valid_count
            job.invalid_records = invalid_count
            job.suspicious_records = suspicious_count
            job.status = 'completed'
            job.processed_at = datetime.now()
            job.save()
            
            logger.info(f"Job {job.id} completed: {valid_count} valid, {invalid_count} invalid, {suspicious_count} suspicious")
        
        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}")
            job.status = 'failed'
            job.processing_error = str(e)
            job.save()
