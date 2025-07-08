import logging
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Tuple, Union
from config import sheets_client, SPREADSHEET_ID, RANGE_NAME
from sheets_client import check_rate_limit, get_next_id
from field_config import get_canonical_field_name, get_all_field_names, is_valid_field
import re
import time

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
        
        # Use field_config to get canonical field names
        plant_name_field = get_canonical_field_name('Plant Name')
        location_field = get_canonical_field_name('Location')
        
        name_idx = header.index(plant_name_field) if plant_name_field in header else 1
        location_idx = header.index(location_field) if location_field in header else 3
        
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

def _normalize_plant_name(name: Optional[str]) -> str:
    """
    Normalize plant name for basic matching (handle plurals, common variations).
    
    Args:
        name (str): Plant name to normalize
    
    Returns:
        str: Normalized plant name
    """
    if not name:
        return ""
    
    name = name.lower().strip()
    
    # Common plural to singular mappings
    plural_to_singular = {
        'roses': 'rose',
        'tomatoes': 'tomato',
        'basils': 'basil',
        'lettuces': 'lettuce',
        'herbs': 'herb',
        'vegetables': 'vegetable',
        'fruits': 'fruit',
        'flowers': 'flower',
        'shrubs': 'shrub',
        'trees': 'tree',
        'vines': 'vine',
        'grasses': 'grass',
        'ferns': 'fern',
        'cacti': 'cactus',
        'cactuses': 'cactus',
        'succulents': 'succulent',
        'annuals': 'annual',
        'perennials': 'perennial',
        'bulbs': 'bulb',
        'seeds': 'seed',
        'seedlings': 'seedling',
        'cuttings': 'cutting',
        'plants': 'plant'
    }
    
    # Check if the name is a known plural
    if name in plural_to_singular:
        return plural_to_singular[name]
    
    # Handle common plural patterns
    if name.endswith('s'):
        # Remove 's' and check if it's a valid singular form
        singular = name[:-1]
        # Add back common endings that might have been removed
        if singular.endswith('ie'):  # tomatoes -> tomato
            return singular
        elif singular.endswith('e'):  # roses -> rose
            return singular
        elif len(singular) > 2:  # general case
            return singular
    
    return name

def _plant_names_match(search_name: str, plant_name: str) -> bool:
    """
    Check if a search name matches a plant name using simple normalization.
    
    This function is now simplified since the AI handles intelligent matching.
    It only does basic normalization (plurals, case) and exact matching.
    
    Args:
        search_name (str): The name being searched for (from AI analysis)
        plant_name (str): The plant name in the database
    
    Returns:
        bool: True if names match after normalization
    """
    search_normalized = _normalize_plant_name(search_name)
    plant_normalized = _normalize_plant_name(plant_name)
    
    # Simple exact match after normalization
    return search_normalized == plant_normalized

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
            return []
            
        headers = values[0]
        plants_data = []
        
        print("\n=== DEBUG: Sheet Headers ===")
        print(f"Headers: {headers}")
        
        for row in values[1:]:
            row_data = row + [''] * (len(headers) - len(row))
            plant_dict = dict(zip(headers, row_data))
            
            # Debug log the photo URLs using field_config
            photo_url_field = get_canonical_field_name('Photo URL')
            raw_photo_url_field = get_canonical_field_name('Raw Photo URL')
            
            print(f"\n=== DEBUG: Photo URLs for {plant_dict.get(get_canonical_field_name('Plant Name'), 'Unknown Plant')} ===")
            print(f"Photo URL (formula): {plant_dict.get(photo_url_field, '')}")
            print(f"Raw Photo URL: {plant_dict.get(raw_photo_url_field, '')}")
            
            if plant_names:
                # Use improved matching that handles plurals
                plant_name = plant_dict.get(get_canonical_field_name('Plant Name'), '')
                if plant_name and any(_plant_names_match(name, plant_name) for name in plant_names):
                    plants_data.append(plant_dict)
                    print(f"\n=== DEBUG: Matching Plant Data ===")
                    print(f"Plant Name: {plant_dict[get_canonical_field_name('Plant Name')]}")
                    for key, value in plant_dict.items():
                        print(f"{key}: {value}")
            else:
                plants_data.append(plant_dict)
                print(f"\n=== DEBUG: Plant Data ===")
                print(f"Plant Name: {plant_dict[get_canonical_field_name('Plant Name')]}")
                for key, value in plant_dict.items():
                    print(f"{key}: {value}")
        
        return plants_data
        
    except Exception as e:
        print(f"Error getting plant data: {e}")
        return []

def find_plant_by_id_or_name(identifier: str) -> Tuple[Optional[int], Optional[List]]:
    """Find a plant by ID or name"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        # Use field_config to get canonical field name
        plant_name_field = get_canonical_field_name('Plant Name')
        name_idx = header.index(plant_name_field) if plant_name_field in header else 1
        
        try:
            plant_id = str(int(identifier))
            for i, row in enumerate(values[1:], start=1):
                if row and row[0] == plant_id:
                    return i, row
        except ValueError:
            search_name = identifier.lower()
            
            # First try exact match
            for i, row in enumerate(values[1:], start=1):
                if row and len(row) > name_idx and row[name_idx].lower() == search_name:
                    return i, row
            
            # If no exact match, try partial matching
            # Split the search name into words and look for plants that contain all words
            search_words = search_name.split()
            best_match = None
            best_score = 0
            
            for i, row in enumerate(values[1:], start=1):
                if row and len(row) > name_idx and row[name_idx]:
                    plant_name = row[name_idx].lower()
                    plant_words = plant_name.split()
                    
                    # Count how many search words are found in the plant name
                    matches = sum(1 for word in search_words if any(word in plant_word for plant_word in plant_words))
                    score = matches / len(search_words) if search_words else 0
                    
                    if score > best_score and score >= 0.5:  # At least 50% of words must match
                        best_score = score
                        best_match = (i, row)
            
            if best_match:
                return best_match
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error finding plant: {e}")
        return None, None

def update_plant_legacy(plant_data: Dict) -> bool:
    """Update or add a plant in the Google Sheet (legacy function)"""
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
        
        # Use field_config to get canonical field names
        plant_name_field = get_canonical_field_name('Plant Name')
        plant_name = plant_data.get(plant_name_field)
        plant_row = None
        
        if plant_name:
            for i, row in enumerate(values[1:], start=1):
                if len(row) > 1 and row[1].lower() == plant_name.lower():
                    plant_row = i
                    break
        
        # Handle photo URLs - store both the IMAGE formula and raw URL
        photo_url_field = get_canonical_field_name('Photo URL')
        photo_url = plant_data.get(photo_url_field, '')
        photo_formula = f'=IMAGE("{photo_url}")' if photo_url else ''
        raw_photo_url = photo_url  # Store the raw URL directly
        
        est = pytz.timezone('US/Eastern')
        timestamp = datetime.now(est).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build new row using field_config to get all field names
        field_names = get_all_field_names()
        new_row = []
        
        for field_name in field_names:
            if field_name == get_canonical_field_name('ID'):
                new_row.append(str(len(values) if plant_row is None else values[plant_row][0]))
            elif field_name == photo_url_field:
                new_row.append(photo_formula)  # Photo URL as image formula
            elif field_name == get_canonical_field_name('Raw Photo URL'):
                new_row.append(raw_photo_url)  # Raw Photo URL stored directly
            elif field_name == get_canonical_field_name('Last Updated'):
                new_row.append(timestamp)
            else:
                new_row.append(plant_data.get(field_name, ''))
        
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
            
            # Phase 2: Invalidate cache after plant update
            invalidate_plant_list_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Sheet API error: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error updating plant: {e}")
        return False

def update_plant(plant_id: Union[int, str], update_data: Dict) -> Dict[str, Union[bool, str]]:
    """
    Update a plant in the database by ID.
    
    Args:
        plant_id (Union[int, str]): ID of the plant to update
        update_data (Dict): Dictionary of field names and new values
        
    Returns:
        Dict[str, Union[bool, str]]: Result with success status and message
    """
    try:
        plant_id = str(plant_id)
        
        # Find the plant row
        plant_row, plant_data = find_plant_by_id_or_name(plant_id)
        if not plant_row:
            return {"success": False, "error": "Plant not found"}
        
        # Update each field
        for field_name, new_value in update_data.items():
            # Validate field name using field_config
            if not is_valid_field(field_name):
                logger.warning(f"Invalid field name: {field_name}")
                continue
            
            success = update_plant_field(plant_row, field_name, str(new_value))
            if not success:
                return {"success": False, "error": f"Failed to update field {field_name}"}
        
        # Invalidate cache
        invalidate_plant_list_cache()
        
        plant_name = plant_data[0][1] if plant_data and len(plant_data[0]) > 1 else "Unknown"
        logger.info(f"Successfully updated plant: {plant_name}")
        return {"success": True, "message": f"Updated {plant_name}"}
        
    except Exception as e:
        logger.error(f"Error updating plant {plant_id}: {e}")
        return {"success": False, "error": str(e)}

def update_plant_field(plant_row: int, field_name: str, new_value: str) -> bool:
    """Update a specific field for a plant"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        header = result.get('values', [])[0]
        
        # Use field_config to validate and get canonical field name
        canonical_field_name = get_canonical_field_name(field_name)
        if not canonical_field_name:
            logger.error(f"Field {field_name} not found in field configuration")
            return False
        
        try:
            col_idx = header.index(canonical_field_name)
        except ValueError:
            logger.error(f"Field {canonical_field_name} not found in sheet")
            return False
            
        if canonical_field_name == get_canonical_field_name('Photo URL'):
            # Update both Photo URL and Raw Photo URL columns
            formatted_value = f'=IMAGE("{new_value}")' if new_value else ''
            
            # Update Photo URL column with IMAGE formula
            range_name = f'Plants!{chr(65 + col_idx)}{plant_row + 1}'
            logger.info(f"Updating {canonical_field_name} at {range_name}")
            sheets_client.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [[formatted_value]]}
            ).execute()
            
            # Update Raw Photo URL column with raw URL
            try:
                raw_photo_url_field = get_canonical_field_name('Raw Photo URL')
                raw_url_col_idx = header.index(raw_photo_url_field)
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
            logger.info(f"Updating {canonical_field_name} at {range_name}")
            sheets_client.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [[formatted_value]]}
            ).execute()
        
        # Phase 2: Invalidate cache after field update
        invalidate_plant_list_cache()
        
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

# Public API functions for web.py compatibility
def get_plants() -> List[Dict]:
    """
    Get all plants from the database (alias for get_all_plants).
    
    Returns:
        List[Dict]: List of plant dictionaries
    """
    return get_all_plants()

def add_plant(plant_name: str, description: str = "", location: str = "", photo_url: str = "") -> Dict[str, Union[bool, str]]:
    """
    Add a new plant to the database.
    
    Args:
        plant_name (str): Name of the plant
        description (str): Plant description
        location (str): Plant location
        photo_url (str): URL to plant photo
        
    Returns:
        Dict[str, Union[bool, str]]: Result with success status and message
    """
    try:
        # Get next available ID
        next_id = get_next_id()
        if not next_id:
            return {"success": False, "error": "Could not generate plant ID"}
        
        # Prepare plant data using field_config
        plant_data = {
            get_canonical_field_name('ID'): next_id,
            get_canonical_field_name('Plant Name'): plant_name,
            get_canonical_field_name('Description'): description,
            get_canonical_field_name('Location'): location,
            get_canonical_field_name('Photo URL'): photo_url,
            get_canonical_field_name('Last Updated'): datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add empty values for all other fields
        all_fields = get_all_field_names()
        for field in all_fields:
            if field not in plant_data:
                plant_data[field] = ""
        
        # Convert to list format for Google Sheets
        headers = get_all_field_names()
        row_data = [plant_data.get(field, "") for field in headers]
        
        # Add to sheet
        check_rate_limit()
        sheets_client.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            body={'values': [row_data]}
        ).execute()
        
        # Invalidate cache
        invalidate_plant_list_cache()
        
        logger.info(f"Successfully added plant: {plant_name}")
        return {"success": True, "message": f"Added {plant_name} to garden"}
        
    except Exception as e:
        logger.error(f"Error adding plant {plant_name}: {e}")
        return {"success": False, "error": str(e)}

def delete_plant(plant_id: Union[int, str]) -> Dict[str, Union[bool, str]]:
    """
    Delete a plant from the database by ID.
    
    Args:
        plant_id (Union[int, str]): ID of the plant to delete
        
    Returns:
        Dict[str, Union[bool, str]]: Result with success status and message
    """
    try:
        plant_id = str(plant_id)
        
        # Find the plant row
        plant_row, plant_data = find_plant_by_id_or_name(plant_id)
        if not plant_row:
            return {"success": False, "error": "Plant not found"}
        
        # Delete the row
        check_rate_limit()
        sheets_client.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f'Plants!A{plant_row}:Q{plant_row}'
        ).execute()
        
        # Invalidate cache
        invalidate_plant_list_cache()
        
        plant_name = plant_data[0][1] if plant_data and len(plant_data[0]) > 1 else "Unknown"
        logger.info(f"Successfully deleted plant: {plant_name}")
        return {"success": True, "message": f"Deleted {plant_name}"}
        
    except Exception as e:
        logger.error(f"Error deleting plant {plant_id}: {e}")
        return {"success": False, "error": str(e)}

def search_plants(query: str) -> List[Dict]:
    """
    Search plants by name or other criteria.
    
    Args:
        query (str): Search query
        
    Returns:
        List[Dict]: List of matching plant dictionaries
    """
    try:
        # Get all plants
        all_plants = get_plant_data()
        
        if not query.strip():
            return all_plants
        
        query_lower = query.lower().strip()
        matching_plants = []
        
        for plant in all_plants:
            # Search in plant name
            plant_name = plant.get(get_canonical_field_name('Plant Name'), '').lower()
            if query_lower in plant_name:
                matching_plants.append(plant)
                continue
            
            # Search in description
            description = plant.get(get_canonical_field_name('Description'), '').lower()
            if query_lower in description:
                matching_plants.append(plant)
                continue
            
            # Search in location
            location = plant.get(get_canonical_field_name('Location'), '').lower()
            if query_lower in location:
                matching_plants.append(plant)
                continue
        
        logger.info(f"Search for '{query}' found {len(matching_plants)} plants")
        return matching_plants
        
    except Exception as e:
        logger.error(f"Error searching plants for '{query}': {e}")
        return []

# Phase 2: Plant List Caching System
_plant_list_cache = {
    'names': [],
    'last_updated': 0,
    'cache_duration': 300  # 5 minutes cache duration
}

def get_plant_names_from_database() -> List[str]:
    """
    Get a list of all plant names from the database.
    
    This function uses caching to improve performance and reduce API calls.
    The cache is invalidated when plants are added or updated.
    
    Returns:
        List[str]: List of plant names currently in the database
    """
    # Import here to avoid circular imports
    from plant_operations import _plant_list_cache
    
    current_time = time.time()
    cache_duration = 300  # 5 minutes
    
    # Check if cache is still valid
    if (_plant_list_cache['names'] and 
        _plant_list_cache['last_updated'] and 
        current_time - _plant_list_cache['last_updated'] < cache_duration):
        logger.info(f"Returning cached plant list with {len(_plant_list_cache['names'])} plants")
        return _plant_list_cache['names'].copy()
    
    try:
        logger.info("Cache expired, fetching fresh plant list from database")
        check_rate_limit()
        
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) <= 1:
            logger.warning("No plants found in database or only header row present")
            _plant_list_cache['names'] = []
            _plant_list_cache['last_updated'] = current_time
            return []
        
        headers = values[0]
        # Use field_config to get canonical field name
        plant_name_field = get_canonical_field_name('Plant Name')
        name_idx = headers.index(plant_name_field) if plant_name_field in headers else 1
        
        # Extract plant names from all rows except header
        plant_names = []
        for row in values[1:]:
            if len(row) > name_idx and row[name_idx]:
                plant_name = row[name_idx].strip()
                if plant_name:  # Only add non-empty names
                    plant_names.append(plant_name)
        
        # Update cache
        _plant_list_cache['names'] = plant_names
        _plant_list_cache['last_updated'] = current_time
        
        logger.info(f"Updated plant list cache with {len(plant_names)} plants")
        return plant_names.copy()
        
    except Exception as e:
        logger.error(f"Error fetching plant names from database: {e}")
        # Return cached data if available, otherwise empty list
        if _plant_list_cache['names']:
            logger.info("Returning cached plant list due to database error")
            return _plant_list_cache['names'].copy()
        return []

def invalidate_plant_list_cache():
    """
    Invalidate the plant list cache to force a fresh fetch on next request.
    
    This should be called when plants are added, updated, or removed from the database.
    """
    global _plant_list_cache
    _plant_list_cache['last_updated'] = 0
    logger.info("Plant list cache invalidated")

def get_plant_list_cache_info() -> Dict:
    """
    Get information about the current plant list cache status.
    
    Returns:
        Dict: Cache information including count, last updated, and cache duration
    """
    global _plant_list_cache
    current_time = time.time()
    age = current_time - _plant_list_cache['last_updated']
    is_valid = age < _plant_list_cache['cache_duration']
    
    return {
        'plant_count': len(_plant_list_cache['names']),
        'last_updated': _plant_list_cache['last_updated'],
        'cache_age_seconds': age,
        'is_valid': is_valid,
        'cache_duration_seconds': _plant_list_cache['cache_duration']
    } 

def get_location_names_from_database() -> List[str]:
    """
    Get a list of unique location names from the database.
    
    This function extracts all unique location values from the database
    to support location-based queries like "what plants are in the arboretum".
    
    Returns:
        List[str]: List of unique location names from the database
    """
    try:
        check_rate_limit()
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return []
            
        headers = values[0]
        # Use field_config to get canonical field name
        location_field = get_canonical_field_name('Location')
        location_idx = headers.index(location_field) if location_field in headers else 3
        
        # Extract all location values
        locations = set()
        for row in values[1:]:
            if len(row) > location_idx and row[location_idx]:
                # Split by comma and clean up each location
                location_parts = row[location_idx].split(',')
                for part in location_parts:
                    location = part.strip()
                    if location:  # Only add non-empty locations
                        locations.add(location)
        
        location_list = sorted(list(locations))
        logger.info(f"Retrieved {len(location_list)} unique locations from database")
        return location_list
        
    except Exception as e:
        logger.error(f"Error getting location names from database: {e}")
        return []

def get_plants_by_location(location_names: List[str]) -> List[Dict]:
    """
    Get plants that are located in any of the specified locations (exact match only).
    Args:
        location_names (List[str]): List of location names to search for
    Returns:
        List[Dict]: List of plant data dictionaries for plants in the specified locations
    """
    try:
        check_rate_limit()
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        if not values:
            return []
        headers = values[0]
        location_idx = headers.index('Location') if 'Location' in headers else 3
        matching_plants = []
        location_names_lower = [loc.lower().strip() for loc in location_names]
        for row in values[1:]:
            if len(row) > location_idx and row[location_idx]:
                plant_locations = [loc.strip().lower() for loc in row[location_idx].split(',') if loc.strip()]
                if any(loc in location_names_lower for loc in plant_locations):
                    row_data = row + [''] * (len(headers) - len(row))
                    plant_dict = dict(zip(headers, row_data))
                    matching_plants.append(plant_dict)
        logger.info(f"Found {len(matching_plants)} plants in locations: {location_names}")
        return matching_plants
    except Exception as e:
        logger.error(f"Error getting plants by location: {e}")
        return [] 