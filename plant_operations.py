import logging
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Tuple
from config import sheets_client, SPREADSHEET_ID, RANGE_NAME
from sheets_client import check_rate_limit, get_next_id
import re

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
            
            # Debug log the photo URLs
            print(f"\n=== DEBUG: Photo URLs for {plant_dict.get('Plant Name', 'Unknown Plant')} ===")
            print(f"Photo URL (formula): {plant_dict.get('Photo URL', '')}")
            print(f"Raw Photo URL: {plant_dict.get('Raw Photo URL', '')}")
            
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
        
        # Handle photo URLs - store both the IMAGE formula and raw URL
        photo_url = plant_data.get('Photo URL', '')
        photo_formula = f'=IMAGE("{photo_url}")' if photo_url else ''
        raw_photo_url = photo_url  # Store the raw URL directly
        
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
            photo_formula,  # Photo URL as image formula
            raw_photo_url,  # Raw Photo URL stored directly
            timestamp
        ]
        
        try:
            if plant_row is not None:
                range_name = f'Plants!A{plant_row + 1}:Q{plant_row + 1}'
                result = sheets_client.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body={'values': [new_row]}
                ).execute()
            else:
                result = sheets_client.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Plants!A1:Q',
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
            # Update both Photo URL and Raw Photo URL columns
            formatted_value = f'=IMAGE("{new_value}")' if new_value else ''
            
            # Update Photo URL column with IMAGE formula
            range_name = f'Plants!{chr(65 + col_idx)}{plant_row + 1}'
            logger.info(f"Updating {field_name} at {range_name}")
            sheets_client.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [[formatted_value]]}
            ).execute()
            
            # Update Raw Photo URL column with raw URL
            try:
                raw_url_col_idx = header.index('Raw Photo URL')
                raw_range_name = f'Plants!{chr(65 + raw_url_col_idx)}{plant_row + 1}'
                logger.info(f"Updating Raw Photo URL at {raw_range_name}")
                sheets_client.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=raw_range_name,
                    valueInputOption='RAW',
                    body={'values': [[new_value]]}
                ).execute()
            except ValueError:
                logger.error("Raw Photo URL column not found")
                return False
        else:
            formatted_value = new_value
            range_name = f'Plants!{chr(65 + col_idx)}{plant_row + 1}'
            logger.info(f"Updating {field_name} at {range_name}")
            sheets_client.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [[formatted_value]]}
            ).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating plant field: {e}")
        return False

def migrate_photo_urls():
    """
    Migrates photo URLs from the Photo URL column (which may contain IMAGE formulas)
    to the Raw Photo URL column.
    
    Returns a status message indicating the number of URLs migrated and any errors.
    """
    try:
        # Get all values from the sheet
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No data found in sheet"
            
        # Find the column indices
        headers = values[0]
        try:
            photo_url_col = headers.index('Photo URL')
            raw_photo_url_col = headers.index('Raw Photo URL')
        except ValueError:
            return "Required columns 'Photo URL' and/or 'Raw Photo URL' not found"
            
        # Process each row
        updates = []
        migrated_count = 0
        error_count = 0
        
        for row_idx, row in enumerate(values[1:], start=2):  # Start from 2 to account for 1-based indexing and header row
            try:
                # Skip if row doesn't have enough columns
                if len(row) <= max(photo_url_col, raw_photo_url_col):
                    continue
                    
                photo_url = row[photo_url_col] if photo_url_col < len(row) else ''
                
                # Skip if no photo URL or if raw URL already exists
                if not photo_url or (raw_photo_url_col < len(row) and row[raw_photo_url_col]):
                    continue
                    
                # Extract URL from IMAGE formula if present
                url = None
                if photo_url.startswith('=IMAGE("'):
                    match = re.search(r'=IMAGE\("([^"]+)"\)', photo_url)
                    if match:
                        url = match.group(1)
                else:
                    # If not a formula, use the URL directly
                    url = photo_url if photo_url.startswith('http') else None
                    
                if url:
                    # Prepare the update
                    cell_range = f"{RANGE_NAME.split('!')[0]}!{chr(65 + raw_photo_url_col)}{row_idx}"
                    updates.append({
                        'range': cell_range,
                        'values': [[url]]
                    })
                    migrated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing row {row_idx}: {str(e)}")
                
        # Apply all updates in a single batch
        if updates:
            body = {
                'valueInputOption': 'RAW',
                'data': updates
            }
            sheets_client.values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            
        return f"Migration complete. {migrated_count} URLs migrated. {error_count} errors encountered."
        
    except Exception as e:
        return f"Migration failed: {str(e)}"

def add_test_photo_url():
    """
    Adds a test photo URL to the first plant to verify the migration process.
    """
    from sheets_client import sheets_client, SPREADSHEET_ID
    
    try:
        # Add a test IMAGE formula to the Photo URL column of the first plant
        test_url = "https://example.com/test-hibiscus.jpg"
        image_formula = f'=IMAGE("{test_url}")'
        
        # Update the Photo URL column for the first plant (row 2, since row 1 is header)
        range_name = 'Plants!N2'  # Assuming Photo URL is column N
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body={'values': [[image_formula]]}
        ).execute()
        
        return "Test photo URL added successfully"
        
    except Exception as e:
        return f"Failed to add test photo URL: {str(e)}" 