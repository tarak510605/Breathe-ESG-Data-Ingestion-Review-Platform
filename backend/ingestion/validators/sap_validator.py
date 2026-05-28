"""SAP CSV validator."""


class SAPValidator:
    """
    Validates SAP fuel/procurement records.
    Checks for required fields, valid formats, suspicious values.
    """
    
    REQUIRED_FIELDS = ['date', 'plant_code', 'material', 'quantity']
    
    def validate(self, record: dict) -> tuple:
        """
        Validate record.
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in record or not record[field]:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return (False, errors)
        
        # Validate quantity
        try:
            quantity = float(record['quantity'])
            if quantity <= 0:
                errors.append(f"Quantity must be positive, got {quantity}")
            if quantity > 1000000:  # Outlier threshold
                errors.append(f"Quantity suspiciously high: {quantity}")
        except (ValueError, TypeError):
            errors.append(f"Quantity must be numeric, got {record['quantity']}")
        
        # Validate plant code format
        plant = str(record.get('plant_code', ''))
        if not plant or len(plant) < 3:
            errors.append(f"Invalid plant code: {plant}")
        
        return (len(errors) == 0, errors)
