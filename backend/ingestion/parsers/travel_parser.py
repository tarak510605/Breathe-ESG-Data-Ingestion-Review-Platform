"""Travel expense API parser."""
import json


class TravelParser:
    """
    Parses travel expense platform JSON payloads (Concur-style).
    Handles flights, hotels, ground transport.
    """
    
    def parse(self, file_content: str) -> list:
        """
        Parse JSON travel expense payloads.
        Returns list of individual expense dicts (one record per expense).
        """
        # Try to parse as JSON
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError:
            # If not JSON, might be JSONL (one JSON per line)
            records = []
            for line in file_content.split('\n'):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return records
        
        # Flatten expense structure
        # If data is a list of trips, extract expenses
        if isinstance(data, list):
            all_expenses = []
            for trip in data:
                trip_expenses = self._extract_expenses_from_trip(trip)
                all_expenses.extend(trip_expenses)
            return all_expenses
        
        # If single trip object
        elif isinstance(data, dict):
            return self._extract_expenses_from_trip(data)
        
        return []
    
    def _extract_expenses_from_trip(self, trip: dict) -> list:
        """Extract individual expenses from a trip object."""
        trip_id = trip.get('trip_id', trip.get('ReportKey', ''))
        employee_id = trip.get('employee_id', trip.get('EmployeeID', ''))
        trip_start = trip.get('trip_start', trip.get('ReportDate', ''))
        
        expenses = trip.get('expenses', trip.get('Expenses', []))
        
        result = []
        for exp in expenses:
            # Enrich with trip context
            exp['_trip_id'] = trip_id
            exp['_employee_id'] = employee_id
            exp['_trip_start'] = trip_start
            result.append(exp)
        
        return result
