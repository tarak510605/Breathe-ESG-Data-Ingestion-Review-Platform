import pytest
from decimal import Decimal
from ingestion.services import IngestionService
from data_sources.models import DataSource
from emissions.models import NormalizedEmissionRecord


@pytest.mark.django_db
def test_sap_parser(organization):
    """Test SAP CSV parsing"""
    from ingestion.parsers.sap_parser import parse_sap_csv
    import io
    
    csv_content = """Datum,Werk,Material,Kostenart,Menge,Einheit,Lieferant
2025-01-15,1000,DIESEL-FUEL,4200,500,Liter,Vendor-A
2025-01-15,2000,GASOLINE,4200,300,Gallons,Vendor-B"""
    
    file_obj = io.StringIO(csv_content)
    records = parse_sap_csv(file_obj)
    
    assert len(records) == 2
    assert records[0]['plant_code'] == '1000'
    assert records[0]['material'] == 'DIESEL-FUEL'
    assert records[0]['quantity'] == '500'


@pytest.mark.django_db
def test_sap_normalizer(organization):
    """Test SAP record normalization"""
    from ingestion.normalizers.sap_normalizer import normalize_sap_record
    
    raw_record = {
        'date': '2025-01-15',
        'plant_code': '1000',
        'material': 'DIESEL-FUEL',
        'quantity': 500,
        'unit': 'Liter',
    }
    
    normalized = normalize_sap_record(raw_record)
    
    assert normalized['emission_category'] == 'scope_1_fuel'
    assert normalized['emissions_kg_co2e'] > 0
    assert normalized['unit'] == 'kg'


@pytest.mark.django_db
def test_utility_validator(organization):
    """Test utility record validation"""
    from ingestion.validators.utility_validator import validate_utility_record
    
    valid_record = {
        'meter_id': 'EM-001',
        'billing_start': '2025-01-01',
        'billing_end': '2025-02-01',
        'consumption_kwh': 100000,
        'service_location': 'New York',
    }
    
    errors = validate_utility_record(valid_record)
    assert len(errors) == 0
    
    # Test high consumption flag
    suspicious_record = {**valid_record, 'consumption_kwh': 600000}
    errors = validate_utility_record(suspicious_record)
    assert any('suspicious' in str(e).lower() for e in errors)


@pytest.mark.django_db
def test_anomaly_detection(organization):
    """Test anomaly detection"""
    from emissions.anomaly_detection import AnomalyDetectionService
    
    service = AnomalyDetectionService(organization)
    
    # Create test records
    records = []
    for i in range(10):
        record = NormalizedEmissionRecord.objects.create(
            organization=organization,
            emission_category='scope_2_electricity',
            quantity=100 + i,
            unit='kWh',
            emissions_kg_co2e=Decimal(str(40 + i)),
            period_start='2025-01-01',
            period_end='2025-01-31',
        )
        records.append(record)
    
    # Test outlier detection
    outlier = NormalizedEmissionRecord.objects.create(
        organization=organization,
        emission_category='scope_2_electricity',
        quantity=5000,  # Outlier
        unit='kWh',
        emissions_kg_co2e=Decimal('2000'),
        period_start='2025-01-01',
        period_end='2025-01-31',
    )
    
    anomalies = service._check_outlier(outlier)
    assert len(anomalies) > 0
