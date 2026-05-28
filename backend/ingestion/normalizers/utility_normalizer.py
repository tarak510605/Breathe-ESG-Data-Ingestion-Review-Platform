"""Utility electricity normalizer."""
from datetime import datetime
from decimal import Decimal
from data_sources.models import EmissionFactor


class UtilityNormalizer:
    """
    Normalizes utility meter data into electricity emission records.
    Converts kWh to CO2e using regional grid factors.
    """
    
    # Default grid factors by region (kg CO2e per kWh)
    # In real system, these come from EmissionFactor table
    GRID_FACTORS = {
        'us_west': Decimal('0.345'),
        'us_midwest': Decimal('0.890'),
        'us_northeast': Decimal('0.405'),
        'us_southeast': Decimal('0.610'),
        'eu_average': Decimal('0.380'),
    }
    
    def normalize(self, raw_record: dict, organization, data_source) -> dict:
        """Convert utility record to normalized emission record."""
        
        # Parse billing period
        billing_start_str = raw_record.get('billing_start', raw_record.get('billing_period_start', ''))
        billing_end_str = raw_record.get('billing_end', raw_record.get('billing_period_end', ''))
        
        period_start = self._parse_date(billing_start_str)
        period_end = self._parse_date(billing_end_str)
        
        # Get consumption
        consumption_kwh = Decimal(raw_record.get('consumption_kwh', raw_record.get('consumption', '0')))
        
        # Get grid emission factor
        region = self._infer_region(raw_record)
        factor = self._get_grid_factor(region, organization)
        
        # Calculate emissions
        emissions_co2e = consumption_kwh * factor
        
        return {
            'emission_category': 'scope_2_electricity',
            'emission_source': 'Purchased Electricity',
            'quantity': consumption_kwh,
            'unit': 'kWh',
            'emissions_kg_co2e': emissions_co2e,
            'period_start': period_start,
            'period_end': period_end,
            'facility_code': raw_record.get('service_location', raw_record.get('meter_id', '')),
            'source_reference_id': f"UTIL-{raw_record.get('meter_id', '')}-{billing_start_str}",
            'asset_id': raw_record.get('meter_id', ''),
            'cost': self._try_decimal(raw_record.get('cost', None)),
            'currency': raw_record.get('currency', 'USD'),
        }
    
    def _parse_date(self, date_str: str):
        """Parse date from various formats."""
        if not date_str:
            return None
        
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d.%m.%Y',
            '%m-%d-%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _infer_region(self, record: dict) -> str:
        """Infer region from meter location or state."""
        location = record.get('service_location', '').upper()
        
        # Very simple heuristic
        west_states = ['CA', 'OR', 'WA', 'NV', 'AZ']
        midwest_states = ['IL', 'IN', 'OH', 'MI']
        
        for state in west_states:
            if state in location:
                return 'us_west'
        
        for state in midwest_states:
            if state in location:
                return 'us_midwest'
        
        return 'us_midwest'  # default
    
    def _get_grid_factor(self, region: str, organization) -> Decimal:
        """Get grid emission factor."""
        try:
            factor_type = f"grid_electricity_{region}"
            emission_factor = EmissionFactor.objects.filter(
                organization=organization,
                factor_type=factor_type
            ).first()
            
            if emission_factor:
                return Decimal(str(emission_factor.factor_value))
        except:
            pass
        
        return self.GRID_FACTORS.get(region, Decimal('0.5'))
    
    def _try_decimal(self, value):
        """Safely convert value to Decimal."""
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except:
            return None
