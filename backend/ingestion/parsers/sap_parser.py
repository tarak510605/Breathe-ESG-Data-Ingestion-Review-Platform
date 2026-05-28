"""SAP CSV parser."""
import csv
from io import StringIO
from datetime import datetime


class SAPParser:
    """
    Parses SAP fuel/procurement CSV exports.
    Handles German column names, multiple date formats, mixed units.
    """
    
    # Mapping of German SAP columns to standardized names
    COLUMN_MAP = {
        'Datum': 'date',
        'Werk': 'plant_code',
        'Material': 'material',
        'Kostenart': 'cost_type',
        'Menge': 'quantity',
        'Einheit': 'unit',
        'Lieferant': 'vendor',
        'date': 'date',
        'plant': 'plant_code',
        'quantity': 'quantity',
        'unit': 'unit',
        'posting_date': 'date',
        'plant_code': 'plant_code',
        'material_desc': 'material',
    }
    
    def parse(self, file_content: str) -> list:
        """
        Parse CSV content.
        Returns list of dicts with normalized keys.
        """
        reader = csv.DictReader(StringIO(file_content))
        records = []
        
        for row in reader:
            # Map columns
            normalized_row = {}
            for key, value in row.items():
                normalized_key = self.COLUMN_MAP.get(key.strip(), key.strip())
                normalized_row[normalized_key] = value.strip() if isinstance(value, str) else value
            
            records.append(normalized_row)
        
        return records
