"""Anomaly detection service."""
from decimal import Decimal
import statistics
from emissions.models import NormalizedEmissionRecord, AnomalyFlag


class AnomalyDetectionService:
    """
    Detects data quality issues in normalized records.
    Uses statistical methods and business rules.
    """
    
    def detect_anomalies(self, record: NormalizedEmissionRecord) -> list:
        """
        Detect anomalies in a record.
        Returns list of anomaly dicts ready for AnomalyFlag creation.
        """
        anomalies = []
        
        # Check for negative values
        if record.quantity < 0:
            anomalies.append({
                'anomaly_type': 'suspicious_value',
                'severity': 'critical',
                'description': 'Negative quantity value',
                'metric_name': 'quantity',
                'actual_value': str(record.quantity),
            })
        
        # Check for zero values
        if record.quantity == 0:
            anomalies.append({
                'anomaly_type': 'suspicious_value',
                'severity': 'warning',
                'description': 'Zero quantity',
                'metric_name': 'quantity',
                'actual_value': '0',
            })
        
        # Check for outliers using IQR method
        outlier_check = self._check_outlier(record)
        if outlier_check:
            anomalies.append(outlier_check)
        
        # Check for suspicious patterns
        pattern_check = self._check_pattern(record)
        if pattern_check:
            anomalies.append(pattern_check)
        
        # Check for duplicates
        duplicate_check = self._check_duplicates(record)
        if duplicate_check:
            anomalies.append(duplicate_check)
        
        return anomalies
    
    def _check_outlier(self, record: NormalizedEmissionRecord) -> dict:
        """
        Check if quantity is statistical outlier within organization/category.
        Uses IQR (Interquartile Range) method.
        """
        # Get similar records
        similar = NormalizedEmissionRecord.objects.filter(
            organization=record.organization,
            emission_category=record.emission_category,
            data_source=record.data_source,
            facility_code=record.facility_code,
        ).values_list('quantity', flat=True)
        
        if len(similar) < 5:
            return None  # Not enough data
        
        quantities = [float(q) for q in similar if q is not None]
        if len(quantities) < 5:
            return None
        
        try:
            q1 = statistics.quantiles(quantities, n=4)[0]
            q3 = statistics.quantiles(quantities, n=4)[2]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            quantity_float = float(record.quantity)
            
            if quantity_float < lower_bound or quantity_float > upper_bound:
                return {
                    'anomaly_type': 'outlier',
                    'severity': 'warning',
                    'description': f'Value outside normal range (IQR outlier)',
                    'metric_name': 'quantity',
                    'threshold_value': f"{lower_bound:.2f} - {upper_bound:.2f}",
                    'actual_value': str(quantity_float),
                }
        except:
            pass
        
        return None
    
    def _check_pattern(self, record: NormalizedEmissionRecord) -> dict:
        """Check for suspicious patterns."""
        # Electricity suspiciously high
        if record.emission_category == 'scope_2_electricity':
            if record.quantity > Decimal('500000'):  # > 500k kWh
                return {
                    'anomaly_type': 'suspicious_value',
                    'severity': 'warning',
                    'description': 'Suspiciously high electricity consumption',
                    'metric_name': 'quantity',
                    'threshold_value': '500000 kWh',
                    'actual_value': str(record.quantity),
                }
        
        return None
    
    def _check_duplicates(self, record: NormalizedEmissionRecord) -> dict:
        """Check for duplicate records."""
        duplicates = NormalizedEmissionRecord.objects.filter(
            organization=record.organization,
            data_source=record.data_source,
            facility_code=record.facility_code,
            period_start=record.period_start,
            emission_source=record.emission_source,
        ).exclude(id=record.id)
        
        if duplicates.exists():
            return {
                'anomaly_type': 'duplicate',
                'severity': 'critical',
                'description': f'Potential duplicate record (same facility, period, source)',
                'metric_name': 'record_identity',
                'actual_value': str(duplicates.first().id),
            }
        
        return None
