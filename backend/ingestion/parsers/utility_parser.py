"""Utility CSV parser."""
import csv
from io import StringIO


class UtilityParser:
    """
    Parses utility portal CSV exports.
    Standard columns: Meter_ID, Billing_Start, Billing_End, etc.
    """
    
    def parse(self, file_content: str) -> list:
        """
        Parse utility CSV content.
        Returns list of dicts.
        """
        reader = csv.DictReader(StringIO(file_content))
        records = []
        
        for row in reader:
            # Normalize keys (case-insensitive, strip whitespace)
            normalized_row = {k.strip().lower(): v.strip() for k, v in row.items()}
            records.append(normalized_row)
        
        return records
