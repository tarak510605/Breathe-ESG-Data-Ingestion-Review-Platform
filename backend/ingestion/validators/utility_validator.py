"""Utility CSV validator."""


class UtilityValidator:
    """
    Validates utility meter data records.
    """
    
    REQUIRED_FIELDS = ['meter_id', 'billing_start', 'billing_end', 'consumption_kwh']
    
    def validate(self, record: dict) -> tuple:
        """Validate utility record."""
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in record or not record[field]:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return (False, errors)
        
        # Validate consumption
        try:
            consumption = float(record['consumption_kwh'])
            if consumption < 0:
                errors.append(f"Consumption cannot be negative: {consumption}")
            if consumption > 500000:  # Suspiciously high
                errors.append(f"Consumption suspiciously high: {consumption} kWh")
        except (ValueError, TypeError):
            errors.append(f"Consumption must be numeric")
        
        # Validate meter ID
        meter_id = str(record.get('meter_id', ''))
        if not meter_id or len(meter_id) < 2:
            errors.append(f"Invalid meter ID: {meter_id}")
        
        return (len(errors) == 0, errors)
