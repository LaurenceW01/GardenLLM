from dotenv import load_dotenv
import os
from click import prompt
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource  # Add type hint import
from datetime import datetime, timedelta
import json
from openai import OpenAI
import logging
import traceback
import pytz
import requests
from typing import List, Dict, Optional, Any
import math
import time
from time import sleep

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Debug log the API key (first few chars)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    logger.info(f"API Key loaded (first 10 chars): {api_key[:10]}...")
else:
    logger.error("No API key found!")

# Google Sheets Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '1zmKVuDTbgColGuoHJDF0ZJxXB6N2WfwLkp7LZ0vqOag'
SHEET_GID = '828349954'
RANGE_NAME = 'Plants!A1:P'

# Add these variables near the top of the file
SHEETS_REQUESTS = {}  # Track API requests
MAX_REQUESTS_PER_MINUTE = 30  # Reduce from 60 to 30 to be safer
RATE_LIMIT_SLEEP = 2  # Increase sleep time from 1 to 2 seconds
QUOTA_RESET_INTERVAL = 60  # Seconds to wait when quota is exceeded

def check_rate_limit():
    """Check if we're approaching API rate limits and sleep if necessary"""
    global SHEETS_REQUESTS
    
    # Clean old requests from tracking
    current_time = datetime.now()
    SHEETS_REQUESTS = {
        timestamp: count 
        for timestamp, count in SHEETS_REQUESTS.items() 
        if current_time - timestamp < timedelta(minutes=1)
    }
    
    # Count recent requests
    recent_requests = sum(SHEETS_REQUESTS.values())
    
    # If approaching limit, sleep
    if recent_requests >= MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Rate limit reached. Sleeping for {QUOTA_RESET_INTERVAL} seconds")
        sleep(QUOTA_RESET_INTERVAL)  # Sleep for full minute when quota is reached
        SHEETS_REQUESTS.clear()  # Clear the requests after sleeping
    
    # Track this request
    SHEETS_REQUESTS[current_time] = SHEETS_REQUESTS.get(current_time, 0) + 1

def setup_sheets_client() -> Optional[Resource]:
    """Set up and return Google Sheets client"""
    try:
        # First try environment variable for cloud deployment
        creds_json = os.getenv('GOOGLE_CREDENTIALS')
        if creds_json:
            # Create temporary credentials file from environment variable
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(creds_json)
                temp_creds_path = f.name
            
            try:
                creds = service_account.Credentials.from_service_account_file(
                    temp_creds_path, scopes=SCOPES)
            finally:
                os.unlink(temp_creds_path)  # Clean up temporary file
        else:
            # Fall back to local file for development
            local_creds_path = os.path.join(os.path.dirname(__file__), 'gardenllm-5607a1d9d8f3.json')
            if not os.path.exists(local_creds_path):
                logger.error(f"Service account file not found: {local_creds_path}")
                return None
            creds = service_account.Credentials.from_service_account_file(
                local_creds_path, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        sheets = service.spreadsheets()
        
        # Test the connection
        sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        logger.info("Successfully connected to Google Sheets API")
        return sheets
        
    except Exception as e:
        logger.error(f"Error setting up sheets client: {e}")
        logger.error(traceback.format_exc())
        return None

# Initialize Sheets client with retry logic
max_retries = 3
retry_count = 0
sheets_client = None

while retry_count < max_retries and sheets_client is None:
    try:
        sheets_client = setup_sheets_client()
        if sheets_client:
            logger.info("Successfully initialized Google Sheets client")
            break
    except Exception as e:
        retry_count += 1
        logger.error(f"Attempt {retry_count} failed to initialize Google Sheets client: {e}")
        if retry_count < max_retries:
            time.sleep(1)  # Wait 1 second before retrying

if sheets_client is None:
    logger.error("Failed to initialize Google Sheets client after all retries")
    raise RuntimeError("Could not initialize Google Sheets client")

# Initialize OpenAI client with API key from environment
try:
    if not api_key:  # Verify API key exists
        raise ValueError("No OpenAI API key found in environment variables")  # Raise error if missing
        
    # Create httpx client without proxies for direct connection
    import httpx  # Import for HTTP client
    http_client = httpx.Client(  # Create HTTP client
        timeout=60.0,  # Set timeout to 60 seconds
        follow_redirects=True  # Enable redirect following
    )
        
    client = OpenAI(  # Initialize OpenAI client
        api_key=api_key,  # Set API key
        http_client=http_client,  # Set custom HTTP client
        base_url="https://api.openai.com/v1",  # Set API base URL
        max_retries=2  # Set maximum retry attempts
    )

    # Test the OpenAI connection
    logger.info("Testing OpenAI connection...")  # Log connection test
    test_response = client.chat.completions.create(  # Send test request
        model="gpt-3.5-turbo",  # Use GPT-3.5 Turbo model
        messages=[{"role": "user", "content": "test"}],  # Simple test message
        max_tokens=5  # Request small response
    )
    logger.info(f"OpenAI connection successful. Test response: {test_response}")  # Log successful test
except Exception as e:
    logger.error(f"OpenAI connection failed: {str(e)}")  # Log connection failure
    logger.error(traceback.format_exc())  # Log full error traceback
    raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")  # Raise runtime error

def initialize_sheet(start_cli=False):
    """Initialize the Google Sheet with headers and formatting
    
    Args:
        start_cli (bool): Whether to start CLI after initialization
    """
    print("Initializing sheet with new headers including ID...")  # Log initialization start
    # Get the spreadsheet metadata to find the sheet ID
    spreadsheet = sheets_client.get(spreadsheetId=SPREADSHEET_ID).execute()  # Retrieve spreadsheet metadata
    
    # Use the correct sheet ID from the URL
    sheet_id = int(SHEET_GID)  # Convert sheet GID to integer
    
    # Define column headers for the sheet
    headers = [
        'ID',  # Unique identifier for each plant
        'Plant Name',  # Name of the plant
        'Description',  # Plant description
        'Location',  # Plant location(s)
        'Light Requirements',  # Light needs
        'Frost Tolerance',  # Cold tolerance
        'Watering Needs',  # Watering requirements
        'Soil Preferences',  # Soil preferences
        'Pruning Instructions',  # Pruning guidance
        'Mulching Needs',  # Mulching requirements
        'Fertilizing Schedule',  # Fertilization timing
        'Winterizing Instructions',  # Winter care
        'Spacing Requirements',  # Spacing needs
        'Care Notes',  # Additional care notes
        'Photo URL',  # Plant photo URL
        'Last Updated'  # Last modification timestamp
    ]
    
    # Check if headers already exist
    result = sheets_client.values().get(  # Get existing headers
        spreadsheetId=SPREADSHEET_ID,
        range='Plants!A1:P1'
    ).execute()
    
    if not result.get('values'):  # Check if headers are missing
        # Create headers only if they don't exist
        sheets_client.values().update(  # Add headers to sheet
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
    
    # Format headers and set column/row dimensions
    requests = [{
        'updateSheetProperties': {  # Freeze top row
            'properties': {
                'sheetId': sheet_id,
                'gridProperties': {
                    'frozenRowCount': 1
                }
            },
            'fields': 'gridProperties.frozenRowCount'
        }
    }, {
        'repeatCell': {  # Format header row
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {  # Set light gray background
                        'red': 0.95,
                        'green': 0.95,
                        'blue': 0.95
                    }
                }
            },
            'fields': 'userEnteredFormat(backgroundColor)'
        }
    }, {
        # Set column width for Photo URL column
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': 14,  # Photo URL column (0-based index)
                'endIndex': 15
            },
            'properties': {
                'pixelSize': 200  # Set width to 200 pixels
            },
            'fields': 'pixelSize'
        }
    }, {
        # Set row height for all rows to accommodate images
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 1  # Start from first data row
            },
            'properties': {
                'pixelSize': 150  # Set height to 150 pixels
            },
            'fields': 'pixelSize'
        }
    }]
    
    # Apply formatting requests
    sheets_client.batchUpdate(  # Send batch update request
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("Sheet initialized successfully!")  # Log successful initialization
    
    if start_cli:  # Check if CLI should be started
        print("GardenBot is ready! Type 'exit' to end the conversation.")  # Display CLI ready message
        print(">>>")  # Display prompt

# Initialize the sheet
initialize_sheet()  # Call initialization function

def get_all_plants():
    """Get all plants from the Google Sheet
    
    Returns:
        list: List of dictionaries containing plant information
    """
    try:
        check_rate_limit()  # Add rate limiting
        # Retrieve all values from the sheet
        result = sheets_client.values().get(  # Get all plant data
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])  # Get values or empty list if none
        header = values[0] if values else []  # Get header row
        plants = []  # Initialize plants list
        
        # Find the indices for name and location columns
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1  # Get plant name column index
        location_idx = header.index('Location') if 'Location' in header else 3  # Get location column index
        
        for row in values[1:]:  # Process each data row (skip header)
            if len(row) > max(name_idx, location_idx):  # Ensure row has required columns
                # Get all locations as a list, convert to lowercase for consistency
                raw_locations = row[location_idx].split(',')  # Split locations by comma
                locations = [loc.strip().lower() for loc in raw_locations if loc.strip()]  # Clean and normalize locations
                plants.append({  # Add plant data to list
                    'name': row[name_idx],  # Plant name
                    'location': row[location_idx],  # Original location string
                    'locations': locations,  # Processed location list
                    'frost_tolerance': row[5] if len(row) > 5 else '',  # Frost tolerance
                    'watering_needs': row[6] if len(row) > 6 else ''  # Watering needs
                })
                if len(locations) > 1:  # Log plants with multiple locations
                    logger.info(f"Multi-location plant: {row[name_idx]} in {row[location_idx]}")
        
        logger.info(f"Retrieved {len(plants)} plants from sheet")  # Log total plants retrieved
        # Log examples of plants with multiple locations
        multi_loc_plants = [p for p in plants if len(p['locations']) > 1]  # Get plants with multiple locations
        for plant in sorted(multi_loc_plants, key=lambda x: len(x['locations']), reverse=True)[:5]:  # Log top 5
            logger.info(f"Plant in {len(plant['locations'])} locations: {plant['name']} in {plant['location']}")
        
        return plants  # Return list of plants
    except Exception as e:
        logger.error(f"Error getting plants: {e}")  # Log error
        logger.error(traceback.format_exc())  # Log full error traceback
        return []  # Return empty list on error

def update_system_prompt():
    """Update the system prompt with current plant list and locations"""
    global conversation_history
    
    plants = get_all_plants()
    
    # Create a reverse lookup from plant name to locations
    plant_locations = {}
    for plant in plants:
        name = plant['name']
        locations = plant['locations']
        plant_locations[name] = locations
    
    # Group plants by location (case-insensitive)
    plants_by_location = {}
    for plant in plants:
        for location in plant['locations']:
            if location not in plants_by_location:
                plants_by_location[location] = []
            plants_by_location[location].append(plant['name'])
    
    # Create location-based plant list
    location_list = []
    original_locations = {loc.lower(): loc for plant in plants 
                        for loc in plant['location'].split(',') if loc.strip()}
    
    for location_lower, plant_names in plants_by_location.items():
        original_location = original_locations.get(location_lower, location_lower.title())
        plant_bullets = [f"- {name}" for name in sorted(set(plant_names))]
        location_list.append(f"### {original_location}\n" + "\n".join(plant_bullets))
    
    location_text = "\n\n".join(location_list)
    
    # Add examples of multi-location plants
    multi_location_examples = [
        f"- {name}: {', '.join(locs)}"
        for name, locs in sorted(plant_locations.items(), key=lambda x: len(x[1]), reverse=True)
        if len(locs) > 1
    ][:5]
    
    # Enhanced system prompt with stronger emphasis on listing ALL matches
    system_prompt = (
        "You are a helpful gardening assistant that helps manage a plant journal for a garden in Houston, Texas.\n\n"
        f"Current plants in the garden:\n{location_text}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. When asked about specific types of plants (e.g., 'cypress trees', 'roses'), "
        "you MUST list ALL plants that match the query. For example, if asked about cypress trees "
        "and there are both 'Italian Cypress' and 'Leyland Cypress' in the database, you MUST mention BOTH.\n\n"
        "2. Plants can be in ANY NUMBER of locations. When asked about plants in a specific location, "
        "check for that location in the comma-separated location list for each plant.\n\n"
        "3. When listing plants in a location:\n"
        "   - Include ALL plants that have that location in their list\n"
        "   - Use bullet points (-) for each plant\n"
        "   - Example: If asked 'What plants are in the middle bed?', list every plant that has 'middle bed' "
        "in its location list, even if it's also in other locations\n\n"
        "4. When asked about a plant's location:\n"
        "   - List ALL locations where the plant appears\n"
        "   - Format as a comma-separated list\n"
        "   - Example: 'These plants are located in: Location1, Location2, Location3, etc.'\n\n"
        "5. For watering queries:\n"
        "   - Group plants by watering needs using ** categories\n\n"
        "Here are some examples of plants in multiple locations:\n"
        f"{chr(10).join(multi_location_examples)}\n\n"
        "Only reference plants that are in the current plant list. If asked about a plant not in the list, "
        "mention that it's not currently in the garden database."
    )

    # Update the system prompt in conversation history
    conversation_history[0]['content'] = system_prompt

# Initialize conversation history with system prompt
conversation_history = [  # Initialize conversation history
    {
        "role": "system",  # Set system role
        "content": ""  # Empty content to be updated by update_system_prompt()
    }
]

# Update the system prompt initially
update_system_prompt()  # Perform initial system prompt update

def get_next_id():
    """Get next available ID from sheet
    
    Returns:
        str: Next available ID number as string, or None if error occurs
    """
    try:
        # Get all values from sheet's ID column
        values = sheets_client.values().get(  # Retrieve all IDs
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:A'  # Get all IDs from first column
        ).execute()
        
        # Extract existing IDs, skipping header row
        ids = [row[0] for row in values.get('values', [])[1:] if row and row[0]]  # Get non-empty IDs
        
        if not ids:  # Check if no IDs exist
            return "1"  # Start with 1 if no existing IDs
            
        # Convert existing IDs to integers for comparison
        numeric_ids = []  # Initialize list for numeric IDs
        for id_str in ids:  # Process each ID string
            try:
                numeric_ids.append(int(id_str))  # Convert to integer
            except ValueError:  # Skip invalid numeric strings
                continue
                
        if not numeric_ids:  # Check if no valid numeric IDs
            return "1"  # Start with 1 if no valid numeric IDs
            
        # Calculate and return next available ID
        return str(max(numeric_ids) + 1)  # Increment highest existing ID
        
    except Exception as e:
        print(f"Error getting next ID: {e}")  # Log error
        return None  # Return None on error

def log_plant_to_sheets(plant_data):
    """Add or update plant data in Google Sheets
    
    Args:
        plant_data (dict): Dictionary containing plant information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("\n=== Starting log_plant_to_sheets ===")  # Log function start
        date = datetime.now().strftime("%Y-%m-%d")  # Get current date
        
        # Get next available ID
        next_id = get_next_id()  # Generate new ID
        if not next_id:  # Verify ID generation
            print("Could not generate ID")  # Log error
            return False  # Return failure
        
        # Handle photo URL formatting
        photo_url = plant_data.get('Photo URL', '')  # Get photo URL if exists
        if photo_url:  # Check if URL provided
            photo_url = f'=IMAGE("{photo_url}")'  # Create Google Sheets image formula
            
        # Create row with all fields
        row = [  # Create list of values for new row
            str(next_id),  # Plant ID
            plant_data.get('Plant Name', ''),  # Plant name
            plant_data.get('Description', ''),  # Description
            plant_data.get('Location', ''),  # Location
            plant_data.get('Light Requirements', ''),  # Light needs
            plant_data.get('Frost Tolerance', ''),  # Frost tolerance
            plant_data.get('Watering Needs', ''),  # Watering needs
            plant_data.get('Soil Preferences', ''),  # Soil preferences
            plant_data.get('Pruning Instructions', ''),  # Pruning info
            plant_data.get('Mulching Needs', ''),  # Mulching needs
            plant_data.get('Fertilizing Schedule', ''),  # Fertilizing schedule
            plant_data.get('Winterizing Instructions', ''),  # Winter care
            plant_data.get('Spacing Requirements', ''),  # Spacing needs
            plant_data.get('Care Notes', ''),  # Care notes
            photo_url,  # Photo URL formula
            date  # Last updated date
        ]
        
        print("\nRow to be written:", row)  # Log row data
        
        # Append the row to sheet
        result = sheets_client.values().append(  # Add new row
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()
        
        # Verify write operation
        print("\nAPI Response:", result)  # Log API response
        if 'updates' in result:  # Check if update info exists
            print(f"Updated range: {result['updates'].get('updatedRange')}")  # Log updated range
            print(f"Updated rows: {result['updates'].get('updatedRows')}")  # Log row count
            print(f"Updated cells: {result['updates'].get('updatedCells')}")  # Log cell count
            
            if result['updates'].get('updatedRows', 0) > 0:  # Verify rows updated
                print("Write verified successfully!")  # Log success
                return True  # Return success
            else:
                print("Write verification failed - no rows updated")  # Log failure
                return False  # Return failure
        else:
            print("No update information in response")  # Log missing update info
            return False  # Return failure
            
    except Exception as e:
        print(f"Error in log_plant_to_sheets: {e}")  # Log error
        print("Full traceback:")  # Log error details
        import traceback
        traceback.print_exc()  # Print full error traceback
        return False  # Return failure

def find_plant_by_id_or_name(identifier):
    """Find a plant by ID or name
    
    Args:
        identifier (str): Plant ID or name to search for
        
    Returns:
        tuple: (row_index, row_data) or (None, None) if not found
    """
    try:
        # Get current sheet values
        result = sheets_client.values().get(  # Retrieve all plant data
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])  # Get values or empty list
        header = values[0] if values else []  # Get header row
        
        # Find name column index
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1  # Get name column index
        
        # Try to find by ID first
        try:
            plant_id = str(int(identifier))  # Convert identifier to numeric ID
            for i, row in enumerate(values[1:], start=1):  # Search rows (skip header)
                if row and row[0] == plant_id:  # Check ID match
                    return i, row  # Return row index and data
        except ValueError:  # Handle non-numeric identifiers
            # Search by name if ID search fails
            search_name = identifier.lower()  # Convert to lowercase for comparison
            for i, row in enumerate(values[1:], start=1):  # Search rows (skip header)
                if row and len(row) > name_idx and row[name_idx].lower() == search_name:  # Check name match
                    return i, row  # Return row index and data
        
        return None, None  # Return None if not found
        
    except Exception as e:
        logger.error(f"Error finding plant: {e}")  # Log error
        logger.error(traceback.format_exc())  # Log full error traceback
        return None, None  # Return None on error

def update_plant_field(plant_row, field_name, new_value):
    """Update a specific field for a plant"""
    try:
        # Get header to find column index
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
            
        # Format value based on field type
        if field_name == 'Photo URL':
            formatted_value = f'=IMAGE("{new_value}")' if new_value else ''
        else:
            formatted_value = new_value
            
        # Update the specific cell
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
        logger.error(traceback.format_exc())
        return False

def get_plant_data(plant_names=None):
    """Get data for specified plants or all plants if none specified
    
    Args:
        plant_names (list, optional): List of plant names to retrieve data for
        
    Returns:
        list/str: List of plant dictionaries or error message string
    """
    try:
        check_rate_limit()  # Add rate limiting
        # Get all values from sheet
        result = sheets_client.values().get(  # Retrieve all plant data
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P'  # Get all columns
        ).execute()
        
        values = result.get('values', [])  # Get values or empty list
        if not values:  # Check if sheet is empty
            return "No plants found in the database"  # Return error message
            
        headers = values[0]  # Get column headers
        plants_data = []  # Initialize list for plant data
        
        # Convert sheet rows to list of dictionaries
        for row in values[1:]:  # Skip header row
            # Pad row with empty strings if shorter than headers
            row_data = row + [''] * (len(headers) - len(row))  # Ensure row matches header length
            plant_dict = dict(zip(headers, row_data))  # Create dictionary from row data
            
            # Filter by plant names if specified
            if plant_names:  # Check if specific plants requested
                if any(name.lower() in plant_dict['Plant Name'].lower() for name in plant_names):  # Case-insensitive name match
                    plants_data.append(plant_dict)  # Add matching plant
            else:
                plants_data.append(plant_dict)  # Add all plants if no filter
        
        return plants_data  # Return list of plant dictionaries
        
    except Exception as e:
        print(f"Error getting plant data: {e}")  # Log error
        return f"Error accessing plant database: {str(e)}"  # Return error message

def find_similar_plants(search_name):
    """
    Find plants with names similar to the search term, including partial matches.
    Args:
        search_name (str): The name to search for
    Returns:
        list: List of matching plant names
    """
    # Normalize the search term
    search_term = search_name.lower().strip()
    
    # Get all plants from the sheet
    plants = get_all_plants()
    matches = []
    
    for plant in plants:
        plant_name = plant['name'].lower()
        
        # Exact match
        if plant_name == search_term:
            matches.append(plant['name'])
            continue
            
        # Check if search term is a substring of plant name
        if search_term in plant_name:
            matches.append(plant['name'])
            continue
            
        # Check if any word in the search term matches any word in the plant name
        search_words = set(search_term.split())
        plant_words = set(plant_name.split())
        
        # If any word matches (e.g., "cypress" matches both "Italian cypress" and "Leyland cypress")
        if search_words & plant_words:  # Using set intersection
            matches.append(plant['name'])

    # Remove duplicates while preserving order
    return list(dict.fromkeys(matches))

def verify_plant_name(plant_name):
    """Use LLM to verify plant name spelling
    
    Args:
        plant_name (str): Plant name to verify
        
    Returns:
        str: Corrected plant name or None if invalid
    """
    try:
        # Set up messages for OpenAI query
        messages = [  # Create message list
            {"role": "system", "content": "You are a gardening expert. Verify if this plant name is spelled correctly. If it's misspelled, suggest the correct spelling. Only respond with the correct spelling or 'invalid' if it's not a real plant name."},  # System role
            {"role": "user", "content": f"Is '{plant_name}' spelled correctly?"}  # User query
        ]
        
        # Get response from OpenAI
        response = client.chat.completions.create(  # Send request to OpenAI
            model="gpt-4",  # Use GPT-4 model
            messages=messages  # Pass messages
        )
        
        # Process response
        suggested_name = response.choices[0].message.content.strip()  # Get suggested name
        return suggested_name if suggested_name.lower() != 'invalid' else None  # Return name or None
        
    except Exception as e:
        print(f"Error verifying plant name: {e}")  # Log error
        return plant_name  # Return original name on error

def find_plant_id_by_name(plant_name):
    """Find a plant's ID by its name with intelligent matching
    
    Args:
        plant_name (str): Name of plant to find
        
    Returns:
        str: Plant ID, error message, or list of possible matches
    """
    try:
        # First verify the plant name with LLM
        verified_name = verify_plant_name(plant_name)  # Get verified name
        if not verified_name:  # Check if name is invalid
            return f"'{plant_name}' doesn't appear to be a valid plant name."  # Return error
        
        if verified_name != plant_name:  # Check if name was corrected
            print(f"Suggested spelling: {verified_name}")  # Log correction
        
        # Find similar plants
        matches = find_similar_plants(verified_name)  # Search for matches
        
        if not matches:  # Check if no matches found
            return f"No plants found matching '{verified_name}'"  # Return error
        
        if len(matches) == 1:  # Check if single match
            return matches[0]  # Return ID
        
        # Multiple matches found - format response
        response = "Multiple matching plants found:\n"  # Start response
        for i, match in enumerate(matches, 1):  # Process each match
            response += f"{i}. {match}\n"  # Add match info
        response += "\nPlease specify which plant using its ID (e.g., 'update 3 location: patio')"  # Add instructions
        return response  # Return formatted response
        
    except Exception as e:
        print(f"Error in find_plant_id_by_name: {e}")  # Log error
        return None  # Return None on error

def get_chat_response(message):
    """Get a chat response from OpenAI's API"""
    global conversation_history, client
    
    try:
        # Check if this is an image-related query
        image_keywords = ['look like', 'show me', 'picture', 'pictures', 'photo', 'photos', 'image', 'images']
        is_image_query = any(keyword in message.lower() for keyword in image_keywords)
        
        if is_image_query:
            # Get plant data
            plants_data = get_plant_data()
            if isinstance(plants_data, str):  # Error message
                return plants_data
            
            # Extract search terms
            msg_lower = message.lower()
            search_text = ''
            
            if 'look like' in msg_lower:
                search_text = msg_lower.split('look like')[0].strip()
            elif 'show me' in msg_lower:
                search_text = msg_lower.split('show me')[1].strip()
            elif any(phrase in msg_lower for phrase in ['picture of', 'photo of']):
                for phrase in ['picture of', 'photo of']:
                    if phrase in msg_lower:
                        search_text = msg_lower.split(phrase)[1].strip()
                        break
            
            # Clean up search text
            stop_words = ['what', 'does', 'do', 'a', 'the', 'an', 'pictures', 'picture', 'photos', 'photo', 'images', 'image', 'trees', 'tree', 'or', 'of']
            search_terms = [term for term in search_text.split() if term not in stop_words]
            
            # Find matching plants - using stricter matching criteria
            matching_plants = []
            search_term = ' '.join(search_terms).lower()  # Combine search terms
            
            for plant in plants_data:
                plant_name = plant.get('Plant Name', '').lower()
                
                # Only match if search term is a complete word in the plant name
                plant_words = set(plant_name.split())
                if search_term in plant_words:  # Exact word match
                    photo_url = plant.get('Photo URL', '').strip()
                    description = plant.get('Description', '').strip()
                    location = plant.get('Location', '').strip()
                    
                    # Extract URL from IMAGE formula
                    url = ''
                    if photo_url:
                        if '=IMAGE("' in photo_url:
                            try:
                                # Extract URL from IMAGE formula
                                url_start = photo_url.find('=IMAGE("') + 8
                                url_end = photo_url.find('")', url_start)
                                if url_start > 7 and url_end > url_start:
                                    url = photo_url[url_start:url_end]
                                    
                                    # Modify Google Photos URL for public access
                                    if 'googleusercontent.com' in url:
                                        # Remove any existing parameters
                                        base_url = url.split('?')[0]
                                        # Add required parameters for public access
                                        url = f"{base_url}?authuser=0"
                                        
                            except Exception as e:
                                logger.error(f"Error extracting URL from IMAGE formula: {e}")
                        else:
                            url = photo_url.strip('="')  # Remove any remaining formula characters
                            if 'googleusercontent.com' in url:
                                # Remove any existing parameters
                                base_url = url.split('?')[0]
                                # Add required parameters for public access
                                url = f"{base_url}?authuser=0"
                    
                    # Log URL processing
                    logger.info(f"Plant: {plant.get('Plant Name')}")
                    logger.info(f"Original Photo URL: {photo_url}")
                    logger.info(f"Processed URL: {url}")
                    
                    matching_plants.append({
                        'name': plant.get('Plant Name', ''),
                        'location': location,
                        'url': url,
                        'description': description,
                        'has_photo': bool(url and url.strip() and not url.startswith('=IMAGE'))
                    })
            
            if matching_plants:
                response = []
                response.append("Here are the matching plants in the garden:\n")
                
                # Show plants with photos
                plants_with_photos = [p for p in matching_plants if p.get('has_photo')]
                plants_without_photos = [p for p in matching_plants if not p.get('has_photo')]
                
                if plants_with_photos:
                    for plant in plants_with_photos:
                        response.append(f"**{plant['name']}**")
                        if plant['location']:
                            response.append(f"Located in: {plant['location']}")
                        if plant['description']:
                            response.append(f"{plant['description']}")
                        response.append(f"![{plant['name']}]({plant['url']})\n")
                
                # Mention plants without photos
                if plants_without_photos:
                    if plants_with_photos:
                        response.append("\nAdditionally, I found these matching plants (no photos available):")
                    else:
                        response.append("I found these matching plants, but they don't have photos yet:")
                    for plant in plants_without_photos:
                        response.append(f"- **{plant['name']}** (Located in: {plant['location']})")
                        if plant['description']:
                            response.append(f"  {plant['description']}")
                
                return "\n".join(response)
            else:
                return f"I couldn't find any plants matching '{search_term}' in the garden database."
            
        # Regular chat functionality remains unchanged
        # ... rest of the existing function ...
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        logger.error(traceback.format_exc())
        return "I apologize, but I encountered an error. Please try again in a moment."

def update_plant_url(plant_id, new_url):
    """Update a plant's photo URL in the Google Sheet
    
    Args:
        plant_id (str): ID of the plant to update
        new_url (str): New photo URL to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Log start of update process
        logger.info(f"Starting URL update for plant ID: {plant_id}")
        
        # Get current sheet values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        # Find photo URL column index
        photo_idx = header.index('Photo URL') if 'Photo URL' in header else 14
        logger.info(f"Photo URL column index: {photo_idx}")
        
        # Find the plant row by ID
        plant_row = None
        for i, row in enumerate(values[1:], start=1):  # Skip header row
            if row and len(row) > 0 and row[0] == plant_id:
                plant_row = i
                logger.info(f"Found plant at row {i + 1}")
                break
        
        if plant_row is None:
            # Plant not found
            logger.error(f"Plant ID {plant_id} not found in sheet")
            return False
            
        # Create image formula for Google Sheets
        photo_formula = f'=IMAGE("{new_url}")'
        logger.info(f"Created image formula: {photo_formula}")
        
        # Update only the photo URL column
        range_name = f'Plants!{chr(65 + photo_idx)}{plant_row + 1}'
        logger.info(f"Updating cell at {range_name}")
        
        # Execute update request
        result = sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': [[photo_formula]]}
        ).execute()
        
        logger.info(f"Update result: {result}")
        return True
        
    except Exception as e:
        # Handle errors
        logger.error(f"Error updating plant URL: {e}")
        logger.error(traceback.format_exc())
        return False

def remove_plant_from_locations(plant_name: str, locations_to_remove: List[str]) -> str:
    """Remove a plant from specified locations
    
    Args:
        plant_name (str): Name of the plant to update
        locations_to_remove (List[str]): List of locations to remove
        
    Returns:
        str: Status message describing the result
    """
    try:
        # Get current sheet values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        # Find column indices
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1
        location_idx = header.index('Location') if 'Location' in header else 3
        
        # Find the plant row
        plant_row = None
        current_locations = []
        for i, row in enumerate(values[1:], start=1):
            if row and len(row) > name_idx and row[name_idx].lower() == plant_name.lower():
                plant_row = i
                current_locations = [loc.strip() for loc in row[location_idx].split(',') if loc.strip()]
                break
        
        if plant_row is None:
            return f"Plant '{plant_name}' not found in database"
            
        # Convert locations to remove to lowercase for case-insensitive comparison
        locations_to_remove = [loc.lower() for loc in locations_to_remove]
        
        # Handle removing all locations
        if '*' in locations_to_remove:
            new_location = ''
            removed = set(current_locations)
        else:
            # Filter out locations to remove
            remaining_locations = [loc for loc in current_locations if loc.lower() not in locations_to_remove]
            
            if len(remaining_locations) == len(current_locations):
                return f"None of the specified locations were found for plant '{plant_name}'"
            
            new_location = ', '.join(remaining_locations)
            removed = set(current_locations) - set(remaining_locations)
        
        # Update the location field
        range_name = f'Plants!{chr(65 + location_idx)}{plant_row + 1}'
        
        # Execute update request
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body={'values': [[new_location]]}
        ).execute()
        
        # Return appropriate status message
        if removed:
            if new_location:
                return f"Removed plant '{plant_name}' from locations: {', '.join(removed)}. Still present in: {new_location}"
            else:
                return f"Removed plant '{plant_name}' from all locations. Plant remains in database with no location."
        else:
            return f"No locations were removed for plant '{plant_name}'"
        
    except Exception as e:
        # Handle errors
        logger.error(f"Error removing plant from locations: {e}")
        logger.error(traceback.format_exc())
        return f"Error removing plant from locations: {str(e)}"

def parse_care_guide(response_text):
    """Parse the OpenAI response to extract plant care details"""
    try:
        # Extract sections from the response
        sections = {}
        current_section = None
        current_text = []
        
        for line in response_text.split('\n'):
            if line.startswith('**') and line.endswith('**'):
                if current_section:
                    sections[current_section] = '\n'.join(current_text).strip()
                current_section = line.strip('*').strip(':')
                current_text = []
            elif current_section:
                current_text.append(line)
        
        # Add the last section
        if current_section:
            sections[current_section] = '\n'.join(current_text).strip()
        
        # Map sections to spreadsheet columns
        details = {
            'Description': sections.get('Description', ''),
            'Light Requirements': sections.get('Light', ''),
            'Soil Preferences': sections.get('Soil', ''),
            'Watering Needs': sections.get('Watering', ''),
            'Frost Tolerance': '',  # Will be set based on Temperature info
            'Pruning Instructions': sections.get('Pruning', ''),
            'Mulching Needs': sections.get('Mulching', ''),
            'Fertilizing Schedule': sections.get('Fertilizing', ''),
            'Winterizing Instructions': sections.get('Winter Care', ''),
            'Spacing Requirements': sections.get('Spacing', ''),
            'Care Notes': response_text  # Keep full response
        }
        
        # Special handling for frost tolerance based on temperature info
        temp_info = sections.get('Temperature', '').lower()
        if 'frost' in temp_info or 'freezing' in temp_info:
            if 'protect' in temp_info or 'sensitive' in temp_info:
                details['Frost Tolerance'] = 'Low - Protect from frost'
            elif 'hardy' in temp_info or 'resistant' in temp_info:
                details['Frost Tolerance'] = 'High - Frost hardy'
            else:
                details['Frost Tolerance'] = 'Medium - Some frost tolerance'
        
        # Clean up the extracted text
        for key in details:
            if isinstance(details[key], str):
                # Remove bullet points and extra whitespace
                cleaned = details[key].replace('- ', '').strip()
                # Remove any remaining markdown
                cleaned = cleaned.replace('*', '')
                details[key] = cleaned
        
        return details
    except Exception as e:
        logger.error(f"Error parsing care guide: {e}")
        logger.error(traceback.format_exc())
        # Return empty strings for all fields except Care Notes
        return {
            'Description': '',
            'Light Requirements': '',
            'Soil Preferences': '',
            'Watering Needs': '',
            'Frost Tolerance': '',
            'Pruning Instructions': '',
            'Mulching Needs': '',
            'Fertilizing Schedule': '',
            'Winterizing Instructions': '',
            'Spacing Requirements': '',
            'Care Notes': response_text  # Keep the original response
        }

def gardenbot_response(message):
    """Get a response from the chatbot"""
    try:
        # Check if this is a weather-related query
        weather_keywords = ['weather', 'forecast', 'temperature', 'rain', 'humidity', 'tomorrow', 'today']
        is_weather_query = any(keyword in message.lower() for keyword in weather_keywords)
        
        if is_weather_query:
            logger.info("Processing weather-related query")
            return handle_weather_query(message)
            
        # Handle add plant command
        if message.lower().startswith('add plant '):
            try:
                # Split by 'location' keyword to separate plant name and locations
                parts = message.split(' location ')
                if len(parts) != 2:
                    return "Please specify the plant name and location(s). Format: add plant [name] location [location1], [location2], ..."
                
                # Extract plant name by removing 'add plant' prefix and cleaning
                plant_name = parts[0].lower().replace('add plant', '', 1).strip()
                # Properly capitalize the plant name
                plant_name = ' '.join(word.capitalize() for word in plant_name.split())
                
                # Process locations
                locations = [loc.strip() for loc in parts[1].split(',') if loc.strip()]
                if not locations:
                    return "Please specify at least one location for the plant."
                
                # Create plant info request
                prompt = (
                    f"Create a detailed plant care guide for {plant_name} in Houston, TX. "
                    "Include care requirements, growing conditions, and maintenance tips. "
                    "Focus on practical advice for the specified locations: " + 
                    ', '.join(locations) + "\n\n" +
                    "Please include sections for:\n" +
                    "**Description:**\n" +
                    "**Light:**\n" +
                    "**Soil:**\n" +
                    "**Watering:**\n" +
                    "**Temperature:**\n" +
                    "**Pruning:**\n" +
                    "**Mulching:**\n" +
                    "**Fertilizing:**\n" +
                    "**Winter Care:**\n" +
                    "**Spacing:**"
                )
                
                # Get plant care information from OpenAI
                response = get_chat_response(prompt)
                
                # Parse the care guide to extract details
                care_details = parse_care_guide(response)
                if not care_details:
                    care_details = {'Care Notes': response}
                
                # Add plant to spreadsheet with all details
                plant_data = {
                    'Plant Name': plant_name,  # Use the properly formatted plant name
                    'Location': ', '.join(locations),
                    'Description': care_details.get('Description', ''),
                    'Light Requirements': care_details.get('Light Requirements', ''),
                    'Soil Preferences': care_details.get('Soil Preferences', ''),
                    'Watering Needs': care_details.get('Watering Needs', ''),
                    'Frost Tolerance': care_details.get('Frost Tolerance', ''),
                    'Pruning Instructions': care_details.get('Pruning Instructions', ''),
                    'Mulching Needs': care_details.get('Mulching Needs', ''),
                    'Fertilizing Schedule': care_details.get('Fertilizing Schedule', ''),
                    'Winterizing Instructions': care_details.get('Winterizing Instructions', ''),
                    'Spacing Requirements': care_details.get('Spacing Requirements', ''),
                    'Care Notes': care_details.get('Care Notes', response)
                }
                
                if update_plant(plant_data):
                    return f"Added plant '{plant_name}' to locations: {', '.join(locations)}\n\nCare guide:\n{response}"
                else:
                    return f"Error adding plant '{plant_name}' to database"
                
            except Exception as e:
                logger.error(f"Error adding plant: {e}")
                return f"Error adding plant: {str(e)}"
            
        # Handle remove commands
        lower_msg = message.lower().strip()
        if lower_msg.startswith(('remove plant ', 'remove ')):
            parts = message.split()
            start_idx = 2 if lower_msg.startswith('remove plant ') else 1
            
            # Find the 'from' keyword that separates plant name from locations
            try:
                from_idx = parts.index('from', start_idx)
                plant_name = ' '.join(parts[start_idx:from_idx])
                locations = [loc.strip() for loc in ' '.join(parts[from_idx + 1:]).split(',')]
                
                if not plant_name or not locations:
                    return "Please specify both plant name and locations. Example: 'remove plant Tomato from Garden Bed 1, Patio'"
                
                return remove_plant_from_locations(plant_name, locations)
                
            except ValueError:
                # If 'from' not found, assume removing from all locations
                plant_name = ' '.join(parts[start_idx:])
                if not plant_name:
                    return "Please specify the plant name to remove"
                return remove_plant_from_locations(plant_name, ['*'])  # '*' indicates all locations
            
        # Handle update commands - must start with these exact phrases
        lower_msg = message.lower().strip()
        
        # Only treat as commands if they start with these exact phrases
        is_update_command = lower_msg.startswith(('update plant ', 'update '))
        is_add_command = lower_msg.startswith('add plant ')
        
        if is_update_command:
            # Extract identifier (ID or name)
            parts = message.split()
            start_idx = 2 if lower_msg.startswith('update plant ') else 1
            
            # Find the first keyword after identifier
            keywords = ['url', 'location', 'locations']
            field_start_idx = len(parts)  # Default to end of parts
            field_type = None
            
            # Find the first keyword in parts
            for i, part in enumerate(parts):
                if part.lower() in keywords:
                    field_start_idx = i
                    field_type = part.lower()
                    break
            
            if not field_type:
                return "Please specify what to update (url or location)"
                
            # Extract identifier (everything between start_idx and field_start_idx)
            identifier = ' '.join(parts[start_idx:field_start_idx])
            if not identifier:
                return "Invalid format. Use: update [plant ID/name] [field] [new value]"
            
            # Extract new values for each field type
            updates = {}
            
            # Check for location
            if 'location' in lower_msg:
                loc_start = lower_msg.find('location') + 9
                url_pos = lower_msg.find(' url ')
                if url_pos != -1:
                    location = message[loc_start:url_pos].strip()
                else:
                    location = message[loc_start:].strip()
                if location:
                    updates['Location'] = location
            
            # Check for URL
            if 'url' in lower_msg:
                url_start = lower_msg.find('url') + 4
                url = message[url_start:].strip()
                if url:
                    updates['Photo URL'] = url
            
            if not updates:
                return "No valid updates provided"
            
            # Find the plant
            plant_row, plant_data = find_plant_by_id_or_name(identifier)
            if not plant_row:
                return f"Plant '{identifier}' not found"
            
            # Apply all updates
            success = True
            for field, value in updates.items():
                if not update_plant_field(plant_row, field, value):
                    success = False
                    logger.error(f"Failed to update {field}")
            
            if success:
                fields = ', '.join(updates.keys())
                return f"Successfully updated {fields} for plant {identifier}"
            else:
                return f"Failed to update some fields for plant {identifier}"
                
        # Regular chat response - anything that's not a command
        else:
            response = get_chat_response(message)
            return response

    except Exception as e:
        logger.error(f"Error in gardenbot_response: {e}")
        logger.error(traceback.format_exc())
        return f"An error occurred: {str(e)}"

def update_plant_photo(plant_name, photo_url):
    try:
        # Get current values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P'  # Include all columns
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print("No data found in sheet")
            return False
            
        # Find the plant
        plant_row = None
        for i, row in enumerate(values):
            if row[0].lower() == plant_name.lower():  # Compare plant names
                plant_row = i
                break
                
        if plant_row is None:
            print(f"Plant '{plant_name}' not found")
            return False
            
        # Wrap the URL in IMAGE() function
        image_formula = f'=IMAGE("{photo_url}")'
        
        # Update the photo URL (column N, index 13)
        range_name = f'Plants!N{plant_row + 1}'
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': [[image_formula]]}
        ).execute()
        
        print(f"Updated photo URL for {plant_name}")
        return True
        
    except Exception as e:
        print(f"Error updating photo: {e}")
        return False

def update_plant(plant_data):
    """Update or add a plant in the Google Sheet
    
    Args:
        plant_data (dict): Dictionary containing plant information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        check_rate_limit()  # Add rate limiting
        # Log start of update process
        logger.info("Starting plant update process")
        logger.info(f"Plant data received: {plant_data}")
        
        # Get current sheet values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        logger.info(f"Retrieved {len(values)} rows from sheet")
        
        # Find if plant already exists
        plant_name = plant_data.get('Plant Name')
        logger.info(f"Looking for existing plant: {plant_name}")
        plant_row = None
        
        # Search for existing plant by name
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 1 and row[1].lower() == plant_name.lower():
                plant_row = i
                logger.info(f"Found existing plant at row {i + 1}")
                break  # Exit loop after finding the plant
        
        # Format photo URL as image formula if URL exists
        photo_url = plant_data.get('Photo URL', '')
        if photo_url:
            photo_formula = f'=IMAGE("{photo_url}")'
            logger.info(f"Created image formula: {photo_formula}")
        else:
            photo_formula = ''
            
        # Get current timestamp in EST
        est = pytz.timezone('US/Eastern')
        timestamp = datetime.now(est).strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert plant_data to row format
        new_row = [
            str(len(values) if plant_row is None else values[plant_row][0]),  # ID
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
            timestamp  # Last Updated
        ]
        logger.info(f"Prepared row data: {new_row}")
        
        try:
            if plant_row is not None:
                # Update existing plant
                range_name = f'Plants!A{plant_row + 1}:P{plant_row + 1}'
                logger.info(f"Updating existing plant at {range_name}")
                result = sheets_client.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body={'values': [new_row]}
                ).execute()
                logger.info(f"Update result: {result}")
            else:
                # Add new plant at the end
                logger.info("Adding new plant")
                result = sheets_client.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Plants!A1:P',
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body={'values': [new_row]}
                ).execute()
                logger.info(f"Append result: {result}")
            
            return True
            
        except Exception as e:
            # Handle Sheet API errors
            logger.error(f"Sheet API error: {e}")
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        # Handle general errors
        logger.error(f"Error updating plant: {e}")
        logger.error(traceback.format_exc())
        return False

def get_weather_forecast() -> List[Dict]:
    """Get 5-day weather forecast for Houston using OpenWeatherMap API
    
    Returns:
        List[Dict]: List of daily forecasts with weather details
    """
    try:
        # Get API key from environment
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            logger.error("OpenWeather API key not found in environment variables")
            return []

        # Set Houston coordinates
        lat = 29.7604  # Houston latitude
        lon = -95.3698  # Houston longitude

        # Build API request URL
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=imperial&appid={api_key}"
        logger.info(f"Requesting weather data from: {url}")
        
        # Make API request
        response = requests.get(url)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Weather API error: {response.status_code} - {response.text}")
            return []

        # Parse response data
        data = response.json()
        
        # Process 3-hour forecasts into daily forecasts
        daily_forecasts = {}
        
        for item in data['list']:
            # Convert timestamp to date
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    'date': date,
                    'temp_max': float('-inf'),
                    'temp_min': float('inf'),
                    'humidity': [],
                    'rain': 0,
                    'wind_speed': [],
                    'descriptions': set(),
                    'uvi': 0  # UV index placeholder
                }
            
            # Update daily values
            daily_forecasts[date]['temp_max'] = max(daily_forecasts[date]['temp_max'], item['main']['temp_max'])
            daily_forecasts[date]['temp_min'] = min(daily_forecasts[date]['temp_min'], item['main']['temp_min'])
            daily_forecasts[date]['humidity'].append(item['main']['humidity'])
            daily_forecasts[date]['wind_speed'].append(item['wind']['speed'])
            daily_forecasts[date]['rain'] += float(item.get('rain', {}).get('3h', 0))
            daily_forecasts[date]['descriptions'].add(item['weather'][0]['description'])

        # Convert daily_forecasts to list format
        forecast = []
        for date, data in daily_forecasts.items():
            # Create forecast entry with averaged/formatted values
            forecast.append({
                'date': date,
                'temp_max': round(data['temp_max'], 1),
                'temp_min': round(data['temp_min'], 1),
                'humidity': round(sum(data['humidity']) / len(data['humidity'])),
                'rain': round(data['rain'], 2),
                'wind_speed': round(sum(data['wind_speed']) / len(data['wind_speed']), 1),
                'description': ', '.join(data['descriptions']),
                'uvi': 0
            })
        
        # Sort forecast by date
        forecast.sort(key=lambda x: x['date'])
        logger.info(f"Successfully retrieved forecast for {len(forecast)} days")
        
        # Log sample forecast data
        if forecast:
            logger.info(f"Sample forecast for {forecast[0]['date']}: "
                       f"High: {forecast[0]['temp_max']}°F, "
                       f"Low: {forecast[0]['temp_min']}°F, "
                       f"Rain: {forecast[0]['rain']} inches\n"
                       f"Humidity: {forecast[0]['humidity']}%\n"
                       f"Wind: {forecast[0]['wind_speed']} mph")
        
        return forecast
        
    except Exception as e:
        # Handle errors
        logger.error(f"Error getting weather forecast: {e}")
        logger.error(traceback.format_exc())
        return []

def analyze_forecast_for_plants(forecast: List[Dict]) -> str:
    """Analyze weather forecast and generate plant care advice
    
    Args:
        forecast (List[Dict]): List of daily weather forecasts
        
    Returns:
        str: Formatted plant care advice based on weather conditions
    """
    try:
        # Validate forecast data
        if not forecast:
            return "Unable to get weather forecast. Please check plants according to regular care schedule."

        # Get plant data for context
        plants = get_all_plants()
        advice = []  # Initialize advice list
        
        # Initialize condition tracking lists
        frost_days = []  # Days with freezing temperatures
        hot_days = []    # Days with high temperatures
        dry_days = []    # Days with low humidity
        rainy_days = []  # Days with significant rain
        humid_days = []  # Days with high humidity
        high_uv_days = [] # Days with high UV index
        windy_days = []  # Days with strong winds
        
        # Analyze each day's forecast
        for day in forecast:
            date = day['date']
            conditions = []  # Track conditions for this day
            
            # Check temperature conditions
            if day['temp_min'] <= 32:  # Freezing temperature
                frost_days.append(date)
                conditions.append('frost')
            if day['temp_max'] >= 90:  # Hot temperature
                hot_days.append(date)
                conditions.append('heat')
            
            # Check moisture conditions
            if day['rain'] > 0.1:  # Significant rain
                rainy_days.append(date)
                conditions.append('rain')
            elif day['humidity'] < 50:  # Low humidity
                dry_days.append(date)
                conditions.append('dry')
            
            # Check humidity levels
            if day['humidity'] > 80:  # High humidity
                humid_days.append(date)
                conditions.append('humid')
            
            # Check UV index
            if day['uvi'] > 8:  # High UV
                high_uv_days.append(date)
                conditions.append('high UV')
            
            # Check wind conditions
            if day['wind_speed'] > 15:  # Strong winds
                windy_days.append(date)
                conditions.append('windy')
            
            # Log conditions for this day
            if conditions:
                logger.info(f"Date: {date} - Conditions: {', '.join(conditions)}")

        # Generate frost advice if needed
        if frost_days:
            advice.append("\n🌡️ Frost Alert:")
            frost_sensitive = [p['name'] for p in plants if p.get('frost_tolerance', '').lower().strip() in ['low', 'poor', 'sensitive']]
            if frost_sensitive:
                advice.append(f"- Protect these frost-sensitive plants on {', '.join(frost_days)}:")
                advice.extend(f"  • {plant}" for plant in sorted(frost_sensitive))
                advice.append("- Consider using frost cloth or moving potted plants indoors")
                advice.append("- Water plants before freezing temperatures to help protect roots")

        # Generate heat advice if needed
        if hot_days:
            advice.append("\n☀️ Heat Alert:")
            advice.append(f"- High temperatures expected on {', '.join(hot_days)}")
            heat_sensitive = [p['name'] for p in plants if 'shade' in p.get('light_requirements', '').lower()]
            if heat_sensitive:
                advice.append("- These plants may need extra shade or protection:")
                advice.extend(f"  • {plant}" for plant in sorted(heat_sensitive))
            advice.append("- Water deeply in the early morning")
            advice.append("- Consider using shade cloth during peak heat")
            advice.append("- Monitor for signs of heat stress (wilting, leaf scorch)")

        # Generate UV advice if needed
        if high_uv_days:
            advice.append("\n☀️ High UV Alert:")
            advice.append(f"- Strong sun exposure on {', '.join(high_uv_days)}")
            advice.append("- Consider these protective measures:")
            advice.append("  • Use shade cloth for sensitive plants")
            advice.append("  • Water in early morning to prepare plants")
            advice.append("  • Monitor leaf burn on exposed plants")

        # Generate drought advice if needed
        if len(dry_days) >= 2:
            advice.append("\n💧 Drought Alert:")
            high_water_needs = [p['name'] for p in plants if 'high' in p.get('watering_needs', '').lower()]
            if high_water_needs:
                advice.append("- These plants need extra attention during dry period:")
                advice.extend(f"  • {plant}" for plant in sorted(high_water_needs))
            advice.append("- Consider these actions:")
            advice.append("  • Water deeply but less frequently to encourage deep root growth")
            advice.append("  • Apply or refresh mulch to retain moisture")
            advice.append("  • Check soil moisture before watering")

        # Generate rain advice if needed
        if rainy_days:
            advice.append("\n🌧️ Rain Alert:")
            advice.append(f"- Rain expected on {', '.join(rainy_days)}")
            advice.append("- Actions to take:")
            advice.append("  • Hold off on additional watering")
            advice.append("  • Check and clear drainage in plant beds")
            advice.append("  • Remove any debris that could block water flow")
            if humid_days:
                advice.append("  • Monitor plants for fungal issues due to high humidity")

        # Generate wind advice if needed
        if windy_days:
            advice.append("\n💨 Wind Alert:")
            advice.append(f"- High winds expected on {', '.join(windy_days)}")
            advice.append("- Recommended actions:")
            advice.append("  • Secure or move lightweight potted plants")
            advice.append("  • Check stakes and supports on tall plants")
            advice.append("  • Consider temporary wind barriers for sensitive plants")

        # Add seasonal advice based on current month
        current_month = datetime.now().month
        if current_month in [3, 4, 5]:  # Spring months
            advice.append("\n🌱 Spring Care Tips:")
            advice.append("- Begin fertilizing as new growth appears")
            advice.append("- Start pruning winter damage")
            advice.append("- Watch for early pest issues")
        elif current_month in [6, 7, 8]:  # Summer months
            advice.append("\n☀️ Summer Care Tips:")
            advice.append("- Maintain regular watering schedule")
            advice.append("- Monitor for heat stress")
            advice.append("- Continue pest monitoring")
        elif current_month in [9, 10, 11]:  # Fall months
            advice.append("\n🍂 Fall Care Tips:")
            advice.append("- Reduce watering frequency")
            advice.append("- Begin preparing for winter")
            advice.append("- Consider winter protection needs")
        else:  # Winter months
            advice.append("\n❄️ Winter Care Tips:")
            advice.append("- Reduce watering frequency")
            advice.append("- Protect sensitive plants from frost")
            advice.append("- Monitor for winter damage")

        # Add general daily care advice
        advice.append("\n📋 Daily Monitoring:")
        advice.append("- Check soil moisture levels")
        advice.append("- Look for signs of pest issues")
        advice.append("- Remove any dead or damaged growth")
        advice.append("- Ensure proper air circulation")
        
        return "\n".join(advice)
    except Exception as e:
        # Handle errors
        logger.error(f"Error analyzing forecast: {e}")
        logger.error(traceback.format_exc())
        return "Error generating plant care advice. Please check plants according to regular care schedule."

def display_weather_advice():
    """Display weather forecast and plant care advice to the user"""
    try:
        # Log start of advice generation
        logger.info("Getting weather forecast and generating plant care advice...")
        
        # Get weather data and generate advice
        forecast = get_weather_forecast()
        advice = analyze_forecast_for_plants(forecast)
        
        # Display formatted advice
        print("\n=== 🌿 10-Day Plant Care Forecast 🌿 ===")
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nBased on the weather forecast for Houston, here are your plant care recommendations:")
        print(advice)
        print("\n=====================================")
        
    except Exception as e:
        # Handle errors
        logger.error(f"Error displaying weather advice: {e}")
        print("\nUnable to generate weather-based plant care advice.")
        print("Please follow regular plant care schedule.")

def handle_weather_query(message: str) -> str:
    """Handle weather-related queries and return formatted response
    
    Args:
        message (str): User's weather-related query
        
    Returns:
        str: Formatted response with weather forecast and plant care advice
    """
    try:
        # Get weather forecast
        logger.info("Getting weather forecast...")
        forecast = get_weather_forecast()
        if not forecast:
            return "I'm sorry, I couldn't retrieve the weather forecast at this time."

        # Determine forecast period based on query
        days_to_show = 1  # Default to tomorrow
        if 'week' in message.lower():
            days_to_show = 5  # Show full week
        elif 'today' in message.lower():
            days_to_show = 1  # Show today only
        elif 'tomorrow' in message.lower():
            days_to_show = 2  # Show today and tomorrow
        else:
            days_to_show = 3  # Default to next few days

        # Get plant care advice
        advice = analyze_forecast_for_plants(forecast)
        
        # Format the response
        response = "🌿 Weather Forecast and Plant Care Advice 🌿\n\n"
        
        # Add forecast summary
        response += "Weather Forecast:\n"
        for day in forecast[:days_to_show]:
            # Format each day's forecast
            response += f"\n📅 {day['date']}:\n"
            response += f"• Temperature: {day['temp_min']}°F to {day['temp_max']}°F\n"
            response += f"• Conditions: {day['description']}\n"
            response += f"• Rain: {day['rain']} inches\n"
            response += f"• Humidity: {day['humidity']}%\n"
            response += f"• Wind: {day['wind_speed']} mph\n"
        
        # Add plant care advice section
        response += "\n🌱 Plant Care Recommendations:\n"
        
        # Get current plants for context
        plants = get_all_plants()
        plant_names = [p['name'] for p in plants]
        
        # Add context about current plants
        if plant_names:
            response += f"\nBased on your {len(plant_names)} plants in the garden, here are specific recommendations:\n"
        
        # Add the generated advice
        response += advice
        
        return response
    except Exception as e:
        # Handle errors
        logger.error(f"Error handling weather query: {e}")
        logger.error(traceback.format_exc())
        return "I'm sorry, I encountered an error while processing the weather information."

# Remove the automatic weather advice display
# display_weather_advice()  # Only run when called from CLI

def get_photo_url_from_album(photo_url):
    """Convert Google Photos URL to publicly accessible format"""
    try:
        if 'photos.google.com' in photo_url:
            # If it's a sharing link, ensure it has the correct parameters
            if '?share=' not in photo_url:
                if '?' in photo_url:
                    photo_url += '&share=true'
                else:
                    photo_url += '?share=true'
            
            # Add necessary parameters for public access
            if '&key=' not in photo_url:
                photo_url += '&key=public'
                
            logger.info(f"Formatted photo URL: {photo_url}")
            return photo_url
        return photo_url
    except Exception as e:
        logger.error(f"Error formatting photo URL: {e}")
        return photo_url