"""Travel expense normalizer."""
from datetime import datetime
from decimal import Decimal
from data_sources.models import EmissionFactor


class TravelNormalizer:
    """
    Normalizes travel expenses into emission records.
    Handles flights, hotels, ground transport separately.
    """
    
    # Flight distance estimation (rough great circle distances in km)
    # In real system, use geopy or similar
    AIRPORT_DISTANCES = {
        ('JFK', 'LAX'): 3944,
        ('LAX', 'JFK'): 3944,
        ('SFO', 'LAX'): 559,
        ('LAX', 'SFO'): 559,
        ('ORD', 'LAX'): 2015,
        ('LAX', 'ORD'): 2015,
        ('JFK', 'LHR'): 5570,
        ('LHR', 'JFK'): 5570,
    }
    
    # Emission factors
    FLIGHT_FACTORS = {
        'short_haul': Decimal('0.255'),  # kg CO2e per km (< 463 km)
        'medium_haul': Decimal('0.195'),  # 463-3700 km
        'long_haul': Decimal('0.186'),    # > 3700 km
    }
    
    CABIN_MULTIPLIERS = {
        'economy': Decimal('1.0'),
        'y': Decimal('1.0'),
        'business': Decimal('2.5'),
        'j': Decimal('2.5'),
        'first': Decimal('4.0'),
        'f': Decimal('4.0'),
    }
    
    HOTEL_FACTOR = Decimal('20')  # kg CO2e per night (US average)
    
    GROUND_FACTORS = {
        'taxi': Decimal('0.21'),
        'rideshare': Decimal('0.15'),
        'public_transit': Decimal('0.089'),
        'car': Decimal('0.196'),
    }
    
    def normalize(self, raw_record: dict, organization, data_source) -> dict:
        """
        Normalize travel expense record.
        Type of record depends on expense type.
        """
        expense_type = raw_record.get('type', raw_record.get('ExpenseTypeCode', '')).lower()
        
        if expense_type in ['flight']:
            return self._normalize_flight(raw_record)
        elif expense_type in ['hotel']:
            return self._normalize_hotel(raw_record)
        elif expense_type in ['ground_transport']:
            return self._normalize_ground(raw_record)
        else:
            raise ValueError(f"Unknown expense type: {expense_type}")
    
    def _normalize_flight(self, record: dict) -> dict:
        """Normalize flight expense."""
        origin = record.get('origin', record.get('Origin', '')).upper()
        destination = record.get('destination', record.get('Destination', '')).upper()
        
        # Estimate distance
        distance_km = self._get_distance(origin, destination)
        
        # Get cabin class multiplier
        cabin = record.get('cabin_class', record.get('CabinClass', 'economy')).lower()
        cabin_mult = self.CABIN_MULTIPLIERS.get(cabin, Decimal('1.0'))
        
        # Get number of passengers
        pax_count = int(record.get('pax_count', record.get('Passengers', 1)))
        
        # Determine haul distance
        if distance_km < 463:
            factor = self.FLIGHT_FACTORS['short_haul']
        elif distance_km < 3700:
            factor = self.FLIGHT_FACTORS['medium_haul']
        else:
            factor = self.FLIGHT_FACTORS['long_haul']
        
        # Calculate emissions
        total_emissions = Decimal(str(distance_km)) * factor * cabin_mult * Decimal(str(pax_count))
        
        trip_id = record.get('_trip_id', '')
        trip_start = record.get('_trip_start', '')
        
        return {
            'emission_category': 'scope_3_travel',
            'emission_source': 'Air Travel',
            'quantity': Decimal(str(distance_km)),
            'unit': 'km',
            'emissions_kg_co2e': total_emissions,
            'period_start': self._parse_date(trip_start),
            'period_end': self._parse_date(trip_start),
            'source_reference_id': f"TRAVEL-{trip_id}-{origin}-{destination}",
            'asset_id': f"{origin}-{destination}",
            'cost': self._try_decimal(record.get('cost', record.get('Cost'))),
            'currency': record.get('currency', record.get('Currency', 'USD')),
        }
    
    def _normalize_hotel(self, record: dict) -> dict:
        """Normalize hotel expense."""
        location = record.get('location', record.get('Location', ''))
        
        # Get nights
        checkin = record.get('checkindate', record.get('CheckinDate', ''))
        checkout = record.get('checkoutdate', record.get('CheckoutDate', ''))
        nights = int(record.get('nights', record.get('Nights', 1)))
        
        # Calculate emissions
        total_emissions = self.HOTEL_FACTOR * Decimal(str(nights))
        
        trip_id = record.get('_trip_id', '')
        trip_start = record.get('_trip_start', '')
        
        return {
            'emission_category': 'scope_3_travel',
            'emission_source': 'Hotel Accommodation',
            'quantity': Decimal(str(nights)),
            'unit': 'nights',
            'emissions_kg_co2e': total_emissions,
            'period_start': self._parse_date(trip_start),
            'period_end': self._parse_date(trip_start),
            'source_reference_id': f"TRAVEL-HOTEL-{trip_id}-{location}",
            'asset_id': location,
            'cost': self._try_decimal(record.get('cost', record.get('Cost'))),
            'currency': record.get('currency', record.get('Currency', 'USD')),
        }
    
    def _normalize_ground(self, record: dict) -> dict:
        """Normalize ground transport expense."""
        mode = record.get('mode', record.get('Mode', 'taxi')).lower()
        distance = self._try_decimal(record.get('distance_miles', record.get('Distance')))
        
        if distance is None:
            distance = Decimal('10')  # default
        
        # Convert miles to km if needed
        if 'miles' in str(record.get('unit', 'miles')).lower():
            distance_km = distance * Decimal('1.60934')
        else:
            distance_km = distance
        
        # Get factor
        factor = self.GROUND_FACTORS.get(mode, Decimal('0.15'))
        
        # Calculate emissions
        total_emissions = distance_km * factor
        
        trip_id = record.get('_trip_id', '')
        trip_start = record.get('_trip_start', '')
        
        return {
            'emission_category': 'scope_3_travel',
            'emission_source': f'Ground Transport ({mode.title()})',
            'quantity': distance_km,
            'unit': 'km',
            'emissions_kg_co2e': total_emissions,
            'period_start': self._parse_date(trip_start),
            'period_end': self._parse_date(trip_start),
            'source_reference_id': f"TRAVEL-GROUND-{trip_id}-{mode}",
            'asset_id': mode,
            'cost': self._try_decimal(record.get('cost', record.get('Cost'))),
            'currency': record.get('currency', record.get('Currency', 'USD')),
        }
    
    def _get_distance(self, origin: str, destination: str) -> float:
        """Estimate flight distance between airports."""
        key = (origin, destination)
        
        if key in self.AIRPORT_DISTANCES:
            return self.AIRPORT_DISTANCES[key]
        
        # Reverse
        if (destination, origin) in self.AIRPORT_DISTANCES:
            return self.AIRPORT_DISTANCES[(destination, origin)]
        
        # Default to medium-haul distance
        return 2000
    
    def _parse_date(self, date_str: str):
        """Parse date string."""
        if not date_str:
            return datetime.now().date()
        
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d.%m.%Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except:
                continue
        
        return datetime.now().date()
    
    def _try_decimal(self, value):
        """Safely convert to Decimal."""
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except:
            return None
