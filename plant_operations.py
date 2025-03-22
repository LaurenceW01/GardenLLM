import logging
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Tuple
from config import sheets_client, SPREADSHEET_ID, RANGE_NAME
from sheets_client import check_rate_limit, get_next_id

logger = logging.getLogger(__name__)

def get_all_plants() -> List[Dict]:
    """Get all plants from the Google Sheet"""
    try:
        check_rate_limit()
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        header = values[0] if values else []
        plants = []
        
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1
        location_idx = header.index('Location') if 'Location' in header else 3
        
        for row in values[1:]:
            if len(row) > max(name_idx, location_idx):
                raw_locations = row[location_idx].split(',')
                locations = [loc.strip().lower() for loc in raw_locations if loc.strip()]
                plants.append({
                    'name': row[name_idx],
                    'location': row[location_idx],
                    'locations': locations,
                    'frost_tolerance': row[5] if len(row) > 5 else '',
                    'watering_needs': row[6] if len(row) > 6 else ''
                })
        
        logger.info(f"Retrieved {len(plants)} plants from sheet")
        return plants
        
    except Exception as e:
        logger.error(f"Error getting plants: {e}")
        return []

def get_plant_data(plant_names=None) -> List[Dict]:
    """Get data for specified plants or all plants"""
    try:
        check_rate_limit()
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No plants found in the database"
            
        headers = values[0]
        plants_data = []
        
        print("\n=== DEBUG: Sheet Headers ===")
        print(f"Headers: {headers}")
        
        for row in values[1:]:
            row_data = row + [''] * (len(headers) - len(row))
            plant_dict = dict(zip(headers, row_data))
            
            if plant_names:
                if any(name.lower() in plant_dict['Plant Name'].lower() for name in plant_names):
                    plants_data.append(plant_dict)
                    print(f"\n=== DEBUG: Matching Plant Data ===")
                    print(f"Plant Name: {plant_dict['Plant Name']}")
                    for key, value in plant_dict.items():
                        print(f"{key}: {value}")
            else:
                plants_data.append(plant_dict)
                print(f"\n=== DEBUG: Plant Data ===")
                print(f"Plant Name: {plant_dict['Plant Name']}")
                for key, value in plant_dict.items():
                    print(f"{key}: {value}")
        
        return plants_data
        
    except Exception as e:
        print(f"Error getting plant data: {e}")
        return f"Error accessing plant database: {str(e)}"

def find_plant_by_id_or_name(identifier: str) -> Tuple[Optional[int], Optional[List]]:
    """Find a plant by ID or name"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1
        
        try:
            plant_id = str(int(identifier))
            for i, row in enumerate(values[1:], start=1):
                if row and row[0] == plant_id:
                    return i, row
        except ValueError:
            search_name = identifier.lower()
            for i, row in enumerate(values[1:], start=1):
                if row and len(row) > name_idx and row[name_idx].lower() == search_name:
                    return i, row
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error finding plant: {e}")
        return None, None

def update_plant(plant_data: Dict) -> bool:
    """Update or add a plant in the Google Sheet"""
    try:
        check_rate_limit()
        logger.info("Starting plant update process")
        logger.info(f"Plant data received: {plant_data}")
        
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        plant_name = plant_data.get('Plant Name')
        plant_row = None
        
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 1 and row[1].lower() == plant_name.lower():
                plant_row = i
                break
        
        photo_url = plant_data.get('Photo URL', '')
        photo_formula = f'=IMAGE("{photo_url}")' if photo_url else ''
        
        est = pytz.timezone('US/Eastern')
        timestamp = datetime.now(est).strftime('%Y-%m-%d %H:%M:%S')
        
        new_row = [
            str(len(values) if plant_row is None else values[plant_row][0]),
            plant_data.get('Plant Name', ''),
            plant_data.get('Description', ''),
            plant_data.get('Location', ''),
            plant_data.get('Light Requirements', ''),
            plant_data.get('Frost Tolerance', ''),
            plant_data.get('Watering Needs', ''),
            plant_data.get('Soil Preferences', ''),
            plant_data.get('Pruning Instructions', ''),
            plant_data.get('Mulching Needs', ''),
            plant_data.get('Fertilizing Schedule', ''),
            plant_data.get('Winterizing Instructions', ''),
            plant_data.get('Spacing Requirements', ''),
            plant_data.get('Care Notes', ''),
            photo_formula,
            timestamp
        ]
        
        try:
            if plant_row is not None:
                range_name = f'Plants!A{plant_row + 1}:P{plant_row + 1}'
                result = sheets_client.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body={'values': [new_row]}
                ).execute()
            else:
                result = sheets_client.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Plants!A1:P',
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body={'values': [new_row]}
                ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Sheet API error: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error updating plant: {e}")
        return False

def update_plant_field(plant_row: int, field_name: str, new_value: str) -> bool:
    """Update a specific field for a plant"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        header = result.get('values', [])[0]
        
        try:
            col_idx = header.index(field_name)
        except ValueError:
            logger.error(f"Field {field_name} not found in sheet")
            return False
            
        if field_name == 'Photo URL':
            formatted_value = f'=IMAGE("{new_value}")' if new_value else ''
        else:
            formatted_value = new_value
            
        range_name = f'Plants!{chr(65 + col_idx)}{plant_row + 1}'
        logger.info(f"Updating {field_name} at {range_name}")
        
        result = sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': [[formatted_value]]}
        ).execute()
        
        logger.info(f"Update result: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating plant field: {e}")
        return False 