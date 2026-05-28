"""Travel expense validator."""


class TravelValidator:
    """
    Validates travel expense records.
    """
    
    VALID_EXPENSE_TYPES = ['flight', 'hotel', 'ground_transport', 'FLIGHT', 'HOTEL', 'GROUND_TRANSPORT']
    
    def validate(self, record: dict) -> tuple:
        """Validate travel expense record."""
        errors = []
        
        expense_type = record.get('type', record.get('ExpenseTypeCode', '')).lower()
        
        if not expense_type:
            errors.append("Missing expense type (type or ExpenseTypeCode)")
            return (False, errors)
        
        # Validate by type
        if expense_type in ['flight', 'flight']:
            errors.extend(self._validate_flight(record))
        elif expense_type in ['hotel', 'hotel']:
            errors.extend(self._validate_hotel(record))
        elif expense_type in ['ground_transport', 'ground_transport']:
            errors.extend(self._validate_ground(record))
        else:
            errors.append(f"Unknown expense type: {expense_type}")
        
        return (len(errors) == 0, errors)
    
    def _validate_flight(self, record: dict) -> list:
        """Validate flight expense."""
        errors = []
        
        origin = record.get('origin', record.get('Origin', ''))
        destination = record.get('destination', record.get('Destination', ''))
        
        if not origin:
            errors.append("Flight missing origin")
        if not destination:
            errors.append("Flight missing destination")
        
        return errors
    
    def _validate_hotel(self, record: dict) -> list:
        """Validate hotel expense."""
        errors = []
        
        location = record.get('location', record.get('Location', ''))
        if not location:
            errors.append("Hotel missing location")
        
        return errors
    
    def _validate_ground(self, record: dict) -> list:
        """Validate ground transport."""
        errors = []
        return errors
