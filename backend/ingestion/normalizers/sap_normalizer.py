"""SAP fuel/procurement normalizer."""
from datetime import datetime, date
from decimal import Decimal
from data_sources.models import EmissionFactor


class SAPNormalizer:
    """
    Normalizes SAP records into standardized emission records.
    Handles unit conversions, date parsing, facility mapping.
    """
    
    # Unit conversion factors to kg
    UNIT_CONVERSIONS = {
        'liter': Decimal('1'),
        'liters': Decimal('1'),
        'l': Decimal('1'),
        'gallon': Decimal('3.78541'),
        'gallons': Decimal('3.78541'),
        'gal': Decimal('3.78541'),
        'kg': Decimal('1'),
        'metric_ton': Decimal('1000'),
        'metric_tons': Decimal('1000'),
        't': Decimal('1000'),
        'kwh': Decimal('1'),
        'm3': Decimal('1'),  # cubic meters
    }
    
    # SAP material to emission source mapping
    MATERIAL_TO_SOURCE = {
        'DIESEL': ('scope_1_fuel', 'Diesel Fuel'),
        'DIESEL-FUEL': ('scope_1_fuel', 'Diesel Fuel'),
        'GASOLINE': ('scope_1_fuel', 'Gasoline'),
        'PETROL': ('scope_1_fuel', 'Gasoline'),
        'NATURAL-GAS': ('scope_1_fuel', 'Natural Gas'),
        'LPG': ('scope_1_fuel', 'LPG'),
        'HEATING-OIL': ('scope_1_fuel', 'Heating Oil'),
    }
    
    # Emission factors by fuel type (kg CO2e per unit)
    # These would normally come from EmissionFactor table
    EMISSION_FACTORS = {
        'diesel': Decimal('2.68'),  # kg CO2e per liter
        'gasoline': Decimal('2.31'),
        'natural_gas': Decimal('2.04'),  # per m3
        'lpg': Decimal('1.55'),
        'heating_oil': Decimal('2.76'),
    }
    
    def normalize(self, raw_record: dict, organization, data_source) -> dict:
        """
        Convert raw SAP record to normalized emission record format.
        """
        # Parse date
        date_str = raw_record.get('date', '')
        period_start = self._parse_date(date_str)
        period_end = period_start
        
        # Get material type
        material = raw_record.get('material', '').upper()
        emission_category, emission_source = self.MATERIAL_TO_SOURCE.get(
            material,
            ('scope_1_fuel', 'Unknown Fuel')
        )
        
        # Parse quantity and unit
        quantity_str = raw_record.get('quantity', '0')
        unit_str = raw_record.get('unit', '').lower()
        
        quantity = Decimal(quantity_str)
        unit_normalized = unit_str.lower().strip()
        
        # Lookup emission factor
        factor = self._get_emission_factor(material, organization)
        
        # Calculate emissions
        if unit_normalized in self.UNIT_CONVERSIONS:
            quantity_kg = quantity * self.UNIT_CONVERSIONS[unit_normalized]
        else:
            quantity_kg = quantity
        
        emissions_co2e = quantity_kg * factor
        
        return {
            'emission_category': emission_category,
            'emission_source': emission_source,
            'quantity': quantity,
            'unit': 'liters' if unit_normalized in ['liter', 'liters', 'l'] else 'kg',
            'emissions_kg_co2e': emissions_co2e,
            'period_start': period_start,
            'period_end': period_end,
            'facility_code': raw_record.get('plant_code', ''),
            'source_reference_id': f"SAP-{raw_record.get('plant_code', '')}-{date_str}",
            'asset_id': raw_record.get('material', ''),
        }
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date in multiple formats."""
        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        # Default to today
        return datetime.now().date()
    
    def _get_emission_factor(self, material: str, organization) -> Decimal:
        """Get emission factor from database or defaults."""
        material_lower = material.lower()
        
        # Try to look up in database first
        try:
            if 'diesel' in material_lower:
                factor_type = 'fuel_type_diesel'
            elif 'gasoline' in material_lower or 'petrol' in material_lower:
                factor_type = 'fuel_type_gasoline'
            elif 'natural' in material_lower:
                factor_type = 'fuel_type_natural_gas'
            else:
                factor_type = 'fuel_type_other'
            
            emission_factor = EmissionFactor.objects.filter(
                organization=organization,
                factor_type=factor_type
            ).first()
            
            if emission_factor:
                return Decimal(str(emission_factor.factor_value))
        except:
            pass
        
        # Fall back to defaults
        return self.EMISSION_FACTORS.get(material_lower, Decimal('2.5'))
