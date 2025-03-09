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
    if not api_key:
        raise ValueError("No OpenAI API key found in environment variables")
        
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        timeout=60.0,
        max_retries=2
    )

    # Test the client with a simple request
    logger.info("Testing OpenAI connection...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    logger.info("OpenAI connection successful")
except Exception as e:
    logger.error(f"OpenAI connection failed: {str(e)}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")

def initialize_sheet(start_cli=False):
    """Initialize the sheet and optionally start the CLI"""
    print("Initializing sheet with new headers including ID...")
    # First, get the spreadsheet metadata to find the sheet ID
    spreadsheet = sheets_client.get(spreadsheetId=SPREADSHEET_ID).execute()
    
    # Use the correct sheet ID from the URL
    sheet_id = int(SHEET_GID)
    
    # Remove the clear operation
    # sheets_client.values().clear(
    #     spreadsheetId=SPREADSHEET_ID,
    #     range='Plants!A:Z'  # Clear all columns
    # ).execute()
    
    headers = [
        'ID',
        'Plant Name',
        'Description',
        'Location',
        'Light Requirements',
        'Frost Tolerance',
        'Watering Needs',
        'Soil Preferences',
        'Pruning Instructions',
        'Mulching Needs',
        'Fertilizing Schedule',
        'Winterizing Instructions',
        'Spacing Requirements',
        'Care Notes',
        'Photo URL',
        'Last Updated'
    ]
    
    # Only create headers if the sheet is empty
    result = sheets_client.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Plants!A1:P1'
    ).execute()
    
    if not result.get('values'):
        # Create headers only if they don't exist
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
    
    # Format headers and set column/row dimensions
    requests = [{
        'updateSheetProperties': {
            'properties': {
                'sheetId': sheet_id,
                'gridProperties': {
                    'frozenRowCount': 1
                }
            },
            'fields': 'gridProperties.frozenRowCount'
        }
    }, {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {
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
    
    sheets_client.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("Sheet initialized successfully!")
    
    if start_cli:
        print("GardenBot is ready! Type 'exit' to end the conversation.")
        print(">>>")

# Initialize the sheet
initialize_sheet()

def get_all_plants():
    """Get all plants from the Google Sheet"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        header = values[0] if values else []  # Get header row
        plants = []
        
        # Find the indices for name and location columns
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1
        location_idx = header.index('Location') if 'Location' in header else 3
        
        for row in values[1:]:  # Skip header row
            if len(row) > max(name_idx, location_idx):  # Ensure row has enough columns
                # Get all locations as a list, convert to lowercase for consistency
                raw_locations = row[location_idx].split(',')
                locations = [loc.strip().lower() for loc in raw_locations if loc.strip()]
                plants.append({
                    'name': row[name_idx],
                    'location': row[location_idx],
                    'locations': locations,  # Store lowercase locations
                    'frost_tolerance': row[5] if len(row) > 5 else '',
                    'watering_needs': row[6] if len(row) > 6 else ''
                })
                if len(locations) > 1:
                    logger.info(f"Multi-location plant: {row[name_idx]} in {row[location_idx]}")
        
        logger.info(f"Retrieved {len(plants)} plants from sheet")
        # Log examples of plants with multiple locations
        multi_loc_plants = [p for p in plants if len(p['locations']) > 1]
        for plant in sorted(multi_loc_plants, key=lambda x: len(x['locations']), reverse=True)[:5]:
            logger.info(f"Plant in {len(plant['locations'])} locations: {plant['name']} in {plant['location']}")
        
        return plants
    except Exception as e:
        logger.error(f"Error getting plants: {e}")
        logger.error(traceback.format_exc())
        return []

def update_system_prompt():
    """Update the system prompt with current plant list"""
    global conversation_history
    
    plants = get_all_plants()
    
    # Create a reverse lookup from plant name to locations
    plant_locations = {}
    for plant in plants:
        name = plant['name']
        locations = plant['locations']  # These are already lowercase from get_all_plants
        plant_locations[name] = locations
    
    # Group plants by location (case-insensitive)
    plants_by_location = {}
    for plant in plants:
        for location in plant['locations']:  # Locations are already lowercase
            if location not in plants_by_location:
                plants_by_location[location] = []
            plants_by_location[location].append(plant['name'])
    
    # Create location-based plant list, preserving original location capitalization
    location_list = []
    original_locations = {loc.lower(): loc for plant in plants for loc in plant['location'].split(',') if loc.strip()}
    
    for location_lower, plant_names in plants_by_location.items():
        original_location = original_locations.get(location_lower, location_lower.title())
        plant_bullets = [f"- {name}" for name in sorted(set(plant_names))]
        location_list.append(f"### {original_location}\n" + "\n".join(plant_bullets))
    
    location_text = "\n\n".join(location_list)
    
    # Add examples of multi-location plants, sorted by number of locations
    multi_location_examples = [
        f"- {name}: {', '.join(locs)}"
        for name, locs in sorted(plant_locations.items(), key=lambda x: len(x[1]), reverse=True)
        if len(locs) > 1
    ][:5]  # Show top 5 plants with most locations
    
    system_prompt = (
        "You are a helpful gardening assistant that helps manage a plant journal for a garden in Houston, Texas.\n\n"
        f"Current plants in the garden:\n{location_text}\n\n"
        "IMPORTANT INSTRUCTIONS:\n"
        "1. Plants can be in ANY NUMBER of locations. When asked about plants in a specific location, "
        "check for that location in the comma-separated location list for each plant.\n\n"
        "2. When listing plants in a location:\n"
        "   - Include ALL plants that have that location in their list\n"
        "   - Use bullet points (-) for each plant\n"
        "   - Example: If asked 'What plants are in the middle bed?', list every plant that has 'middle bed' "
        "in its location list, even if it's also in other locations\n\n"
        "3. When asked about a plant's location:\n"
        "   - List ALL locations where the plant appears\n"
        "   - Format as a comma-separated list\n"
        "   - Example: 'This plant is located in: Location1, Location2, Location3, etc.'\n\n"
        "4. For watering queries:\n"
        "   - Group plants by watering needs using ** categories\n\n"
        "Here are some examples of plants in multiple locations:\n"
        f"{chr(10).join(multi_location_examples)}\n\n"
        "Only reference plants that are in the current plant list. If asked about a plant not in the list, "
        "mention that it's not currently in the garden database."
    )

    # Update the system prompt
    conversation_history[0]['content'] = system_prompt

# Initialize conversation history with system prompt
conversation_history = [
    {
        "role": "system",
        "content": ""  # Will be updated by update_system_prompt()
    }
]

# Update the system prompt initially
update_system_prompt()

def get_next_id():
    """Get next available ID from sheet"""
    try:
        # Get all values from sheet
        values = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:A'  # Get all IDs from first column
        ).execute()
        
        # Skip header row and get IDs from first column
        ids = [row[0] for row in values.get('values', [])[1:] if row and row[0]]
        
        if not ids:
            return "1"  # Start with 1 if no existing IDs
            
        # Convert existing IDs to integers and find max
        numeric_ids = []
        for id_str in ids:
            try:
                numeric_ids.append(int(id_str))
            except ValueError:
                continue
                
        if not numeric_ids:
            return "1"
            
        # Return next available ID
        return str(max(numeric_ids) + 1)
        
    except Exception as e:
        print(f"Error getting next ID: {e}")
        return None

def log_plant_to_sheets(plant_data):
    """Add or update plant data in Google Sheets"""
    try:
        print("\n=== Starting log_plant_to_sheets ===")
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Get next available ID
        next_id = get_next_id()
        if not next_id:
            print("Could not generate ID")
            return False
        
        # Handle photo URL
        photo_url = plant_data.get('Photo URL', '')
        if photo_url:
            photo_url = f'=IMAGE("{photo_url}")'
            
        # Create row with all fields
        row = [
            str(next_id),
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
            photo_url,  # Use the formatted photo URL
            date
        ]
        
        print("\nRow to be written:", row)
        
        # Append the row
        result = sheets_client.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()
        
        print("\nAPI Response:", result)
        if 'updates' in result:
            print(f"Updated range: {result['updates'].get('updatedRange')}")
            print(f"Updated rows: {result['updates'].get('updatedRows')}")
            print(f"Updated cells: {result['updates'].get('updatedCells')}")
            
            if result['updates'].get('updatedRows', 0) > 0:
                print("Write verified successfully!")
                return True
            else:
                print("Write verification failed - no rows updated")
                return False
        else:
            print("No update information in response")
            return False
            
    except Exception as e:
        print(f"Error in log_plant_to_sheets: {e}")
        print("Full traceback:")
        import traceback
        traceback.print_exc()
        return False

def find_plant_by_id_or_name(identifier):
    """Find a plant by ID or name"""
    try:
        # Get current values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        # Find indices
        name_idx = header.index('Plant Name') if 'Plant Name' in header else 1
        
        # Try to find by ID first
        try:
            plant_id = str(int(identifier))  # Check if it's a valid number
            for i, row in enumerate(values[1:], start=1):
                if row and row[0] == plant_id:
                    return i, row
        except ValueError:
            # If not an ID, search by name
            search_name = identifier.lower()
            for i, row in enumerate(values[1:], start=1):
                if row and len(row) > name_idx and row[name_idx].lower() == search_name:
                    return i, row
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error finding plant: {e}")
        logger.error(traceback.format_exc())
        return None, None

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
    """Get data for specified plants or all plants if none specified"""
    try:
        # Get all values from sheet
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No plants found in the database"
            
        headers = values[0]
        plants_data = []
        
        # Convert sheet rows to list of dictionaries
        for row in values[1:]:  # Skip header row
            # Pad row with empty strings if it's shorter than headers
            row_data = row + [''] * (len(headers) - len(row))
            plant_dict = dict(zip(headers, row_data))
            
            # If specific plants requested, only include those
            if plant_names:
                if any(name.lower() in plant_dict['Plant Name'].lower() for name in plant_names):
                    plants_data.append(plant_dict)
            else:
                plants_data.append(plant_dict)
        
        return plants_data
        
    except Exception as e:
        print(f"Error getting plant data: {e}")
        return f"Error accessing plant database: {str(e)}"

def find_similar_plants(search_name):
    """Find plants with similar names"""
    try:
        # Get all values from sheet
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:B'  # Get ID and Name columns
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return []
            
        matches = []
        search_name = search_name.lower()
        
        # Look for exact and partial matches
        for row in values[1:]:  # Skip header
            if len(row) > 1:
                plant_name = row[1].lower()
                if plant_name == search_name:  # Exact match
                    matches.insert(0, {'id': row[0], 'name': row[1], 'exact': True})
                elif search_name in plant_name or plant_name in search_name:  # Partial match
                    matches.append({'id': row[0], 'name': row[1], 'exact': False})
                # Check for word-level matches
                elif any(word in plant_name.split() for word in search_name.split()):
                    matches.append({'id': row[0], 'name': row[1], 'exact': False})
        
        return matches
        
    except Exception as e:
        print(f"Error finding similar plants: {e}")
        return []

def verify_plant_name(plant_name):
    """Use LLM to verify plant name spelling"""
    try:
        messages = [
            {"role": "system", "content": "You are a gardening expert. Verify if this plant name is spelled correctly. If it's misspelled, suggest the correct spelling. Only respond with the correct spelling or 'invalid' if it's not a real plant name."},
            {"role": "user", "content": f"Is '{plant_name}' spelled correctly?"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        suggested_name = response.choices[0].message.content.strip()
        return suggested_name if suggested_name.lower() != 'invalid' else None
        
    except Exception as e:
        print(f"Error verifying plant name: {e}")
        return plant_name  # Return original name if verification fails

def find_plant_id_by_name(plant_name):
    """Find a plant's ID by its name with intelligent matching"""
    try:
        # First verify the plant name with LLM
        verified_name = verify_plant_name(plant_name)
        if not verified_name:
            return f"'{plant_name}' doesn't appear to be a valid plant name."
        
        if verified_name != plant_name:
            print(f"Suggested spelling: {verified_name}")
        
        # Find similar plants
        matches = find_similar_plants(verified_name)
        
        if not matches:
            return f"No plants found matching '{verified_name}'"
        
        if len(matches) == 1:
            return matches[0]['id']
        
        # Multiple matches found
        response = "Multiple matching plants found:\n"
        for i, match in enumerate(matches, 1):
            match_type = "Exact match" if match['exact'] else "Similar match"
            response += f"{i}. {match['name']} (ID: {match['id']}) - {match_type}\n"
        response += "\nPlease specify which plant using its ID (e.g., 'update 3 location: patio')"
        return response
        
    except Exception as e:
        print(f"Error in find_plant_id_by_name: {e}")
        return None

def get_chat_response(message):
    """Get a chat response from OpenAI"""
    global conversation_history
    
    try:
        if not client:
            raise ValueError("OpenAI client is not initialized")
            
        # Update system prompt to get current plant list
        update_system_prompt()
        
        # Get complete plant data for context
        plants_data = get_plant_data()
        if isinstance(plants_data, list):
            plant_details = "\n\nDetailed plant information:\n"
            for plant in plants_data:
                plant_details += f"\nPlant: {plant.get('Plant Name', '')}\n"
                plant_details += f"Location: {plant.get('Location', '')}\n"
                plant_details += f"Description: {plant.get('Description', '')}\n"
                plant_details += f"Care Notes: {plant.get('Care Notes', '')}\n"
            
            # Add detailed plant data to system prompt
            conversation_history[0]['content'] += plant_details
        
        # Limit conversation history
        if len(conversation_history) > 6:  # System prompt + 5 messages
            conversation_history = [
                conversation_history[0],  # System prompt
                *conversation_history[-5:]  # Last 5 messages
            ]
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": message})
        
        logger.info("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            temperature=0.7,
            max_tokens=2000
        )
        
        assistant_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response
        
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        logger.error(traceback.format_exc())
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or contact support if the issue persists."

def update_plant_url(plant_id, new_url):
    """Update a plant's photo URL in the Google Sheet"""
    try:
        logger.info(f"Starting URL update for plant ID: {plant_id}")
        
        # Get current values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        header = values[0] if values else []
        
        # Find photo URL column index
        photo_idx = header.index('Photo URL') if 'Photo URL' in header else 14
        logger.info(f"Photo URL column index: {photo_idx}")
        
        # Find the plant row by ID (first column)
        plant_row = None
        for i, row in enumerate(values[1:], start=1):  # Skip header, use 1-based index
            if row and len(row) > 0 and row[0] == plant_id:
                plant_row = i
                logger.info(f"Found plant at row {i + 1}")
                break
        
        if plant_row is None:
            logger.error(f"Plant ID {plant_id} not found in sheet")
            return False
            
        # Create image formula
        photo_formula = f'=IMAGE("{new_url}")'
        logger.info(f"Created image formula: {photo_formula}")
        
        # Update only the photo URL column
        range_name = f'Plants!{chr(65 + photo_idx)}{plant_row + 1}'
        logger.info(f"Updating cell at {range_name}")
        
        result = sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': [[photo_formula]]}
        ).execute()
        
        logger.info(f"Update result: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating plant URL: {e}")
        logger.error(traceback.format_exc())
        return False

def gardenbot_response(message):
    """Get a response from the chatbot"""
    try:
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
                
        # Handle add plant command
        elif is_add_command:
            # Extract location if provided in the command
            explicit_location = ''
            location_start = message.lower().find(' location ')
            if location_start != -1:
                # Find the end of location (either at 'url' or end of string)
                location_text = message[location_start + 9:]  # Skip past ' location '
                url_pos = location_text.lower().find(' url ')
                if url_pos != -1:
                    explicit_location = location_text[:url_pos].strip()
                else:
                    explicit_location = location_text.strip()
            
            # Create plant info request
            user_message = (
                f"Create a detailed plant care guide for {message} in Houston, TX. "
                "Format the response as a JSON object with these exact field names: "
                "'Plant Name', 'Location', 'Description', 'Light Requirements', 'Frost Tolerance', "
                "'Watering Needs', 'Soil Preferences', 'Pruning Instructions', 'Mulching Needs', "
                "'Fertilizing Schedule', 'Winterizing Instructions', 'Spacing Requirements', "
                "'Care Notes', 'Photo URL'. "
                f"{'Use this specific location: ' + explicit_location if explicit_location else ''} "
                "Wrap the response in ```json code blocks."
            )
            response = get_chat_response(user_message)
            
            # Check if response contains JSON
            if '```json' in response.lower() or response.strip().startswith('{'):
                # Extract JSON data
                if '```json' in response.lower():
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                else:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    logger.info(f"Extracted JSON: {json_str}")
                    plant_data = json.loads(json_str)
                    
                    # Ensure location is set
                    if explicit_location:
                        plant_data['Location'] = explicit_location
                    elif not plant_data.get('Location'):
                        plant_data['Location'] = 'Garden'  # Default location if none specified
                    
                    # Try to update the plant
                    logger.info(f"Attempting to update plant: {plant_data.get('Plant Name')} at location: {plant_data.get('Location')}")
                    success = update_plant(plant_data)
                    if success:
                        logger.info("Plant updated successfully")
                        return f"Successfully added/updated plant: {plant_data.get('Plant Name')} at location: {plant_data.get('Location')}"
                    else:
                        logger.error("Failed to update plant")
                        return "Failed to update the plant information"
            
            return response
            
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
    """Update or add a plant in the Google Sheet"""
    try:
        logger.info("Starting plant update process")
        logger.info(f"Plant data received: {plant_data}")
        
        # Get current values
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
        
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 1 and row[1].lower() == plant_name.lower():  # Check Plant Name column
                plant_row = i
                logger.info(f"Found existing plant at row {i + 1}")
                break
        
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
        
        # Convert plant_data to row format (16 columns including Last Updated)
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
            logger.error(f"Sheet API error: {e}")
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"Error updating plant: {e}")
        logger.error(traceback.format_exc())
        return False

def get_weather_forecast() -> List[Dict]:
    """Get 5-day weather forecast for Houston using OpenWeatherMap API"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            logger.error("OpenWeather API key not found in environment variables")
            return []

        # Houston coordinates
        lat = 29.7604
        lon = -95.3698

        # Get 5-day forecast data (3-hour intervals)
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=imperial&appid={api_key}"
        logger.info(f"Requesting weather data from: {url}")
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Weather API error: {response.status_code} - {response.text}")
            return []

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
                    'uvi': 0  # UV index not available in standard API
                }
            
            # Update daily values
            daily_forecasts[date]['temp_max'] = max(daily_forecasts[date]['temp_max'], item['main']['temp_max'])
            daily_forecasts[date]['temp_min'] = min(daily_forecasts[date]['temp_min'], item['main']['temp_min'])
            daily_forecasts[date]['humidity'].append(item['main']['humidity'])
            daily_forecasts[date]['wind_speed'].append(item['wind']['speed'])
            daily_forecasts[date]['rain'] += float(item.get('rain', {}).get('3h', 0))
            daily_forecasts[date]['descriptions'].add(item['weather'][0]['description'])

        # Convert daily_forecasts to list and format final values
        forecast = []
        for date, data in daily_forecasts.items():
            forecast.append({
                'date': date,
                'temp_max': round(data['temp_max'], 1),
                'temp_min': round(data['temp_min'], 1),
                'humidity': round(sum(data['humidity']) / len(data['humidity'])),  # average humidity
                'rain': round(data['rain'], 2),
                'wind_speed': round(sum(data['wind_speed']) / len(data['wind_speed']), 1),  # average wind speed
                'description': ', '.join(data['descriptions']),
                'uvi': 0  # UV index not available in standard API
            })
        
        # Sort by date
        forecast.sort(key=lambda x: x['date'])
        logger.info(f"Successfully retrieved forecast for {len(forecast)} days")
        
        # Log the first day's forecast as a sample
        if forecast:
            logger.info(f"Sample forecast for {forecast[0]['date']}: "
                       f"High: {forecast[0]['temp_max']}°F, "
                       f"Low: {forecast[0]['temp_min']}°F, "
                       f"Rain: {forecast[0]['rain']}in, "
                       f"Wind: {forecast[0]['wind_speed']}mph")
        
        return forecast
        
    except Exception as e:
        logger.error(f"Error getting weather forecast: {e}")
        logger.error(traceback.format_exc())
        return []

def analyze_forecast_for_plants(forecast: List[Dict]) -> str:
    """Analyze weather forecast and provide plant care advice"""
    try:
        if not forecast:
            return "Unable to get weather forecast. Please check plants according to regular care schedule."

        plants = get_all_plants()
        advice = []
        
        # Get the weather conditions for each day
        frost_days = []
        hot_days = []
        dry_days = []
        rainy_days = []
        humid_days = []
        high_uv_days = []
        windy_days = []
        
        for day in forecast:
            date = day['date']
            conditions = []
            
            # Check temperature conditions
            if day['temp_min'] <= 32:
                frost_days.append(date)
                conditions.append('frost')
            if day['temp_max'] >= 90:
                hot_days.append(date)
                conditions.append('heat')
            
            # Check moisture conditions
            if day['rain'] > 0.1:  # More than 0.1 inches of rain
                rainy_days.append(date)
                conditions.append('rain')
            elif day['humidity'] < 50:
                dry_days.append(date)
                conditions.append('dry')
            
            # Check humidity
            if day['humidity'] > 80:
                humid_days.append(date)
                conditions.append('humid')
            
            # Check UV index
            if day['uvi'] > 8:
                high_uv_days.append(date)
                conditions.append('high UV')
            
            # Check wind conditions
            if day['wind_speed'] > 15:
                windy_days.append(date)
                conditions.append('windy')
            
            if conditions:
                logger.info(f"Date: {date} - Conditions: {', '.join(conditions)}")

        # Generate advice based on conditions
        if frost_days:
            advice.append("\n🌡️ Frost Alert:")
            frost_sensitive = [p['name'] for p in plants if p.get('frost_tolerance', '').lower().strip() in ['low', 'poor', 'sensitive']]
            if frost_sensitive:
                advice.append(f"- Protect these frost-sensitive plants on {', '.join(frost_days)}:")
                advice.extend(f"  • {plant}" for plant in sorted(frost_sensitive))
                advice.append("- Consider using frost cloth or moving potted plants indoors")
                advice.append("- Water plants before freezing temperatures to help protect roots")

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

        if high_uv_days:
            advice.append("\n☀️ High UV Alert:")
            advice.append(f"- Strong sun exposure on {', '.join(high_uv_days)}")
            advice.append("- Consider these protective measures:")
            advice.append("  • Use shade cloth for sensitive plants")
            advice.append("  • Water in early morning to prepare plants")
            advice.append("  • Monitor leaf burn on exposed plants")

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

        if rainy_days:
            advice.append("\n🌧️ Rain Alert:")
            advice.append(f"- Rain expected on {', '.join(rainy_days)}")
            advice.append("- Actions to take:")
            advice.append("  • Hold off on additional watering")
            advice.append("  • Check and clear drainage in plant beds")
            advice.append("  • Remove any debris that could block water flow")
            if humid_days:
                advice.append("  • Monitor plants for fungal issues due to high humidity")

        if windy_days:
            advice.append("\n💨 Wind Alert:")
            advice.append(f"- High winds expected on {', '.join(windy_days)}")
            advice.append("- Recommended actions:")
            advice.append("  • Secure or move lightweight potted plants")
            advice.append("  • Check stakes and supports on tall plants")
            advice.append("  • Consider temporary wind barriers for sensitive plants")

        # Add seasonal advice based on current month
        current_month = datetime.now().month
        if current_month in [3, 4, 5]:  # Spring
            advice.append("\n🌱 Spring Care Tips:")
            advice.append("- Begin fertilizing as new growth appears")
            advice.append("- Start pruning winter damage")
            advice.append("- Watch for early pest issues")
        elif current_month in [6, 7, 8]:  # Summer
            advice.append("\n☀️ Summer Care Tips:")
            advice.append("- Maintain regular watering schedule")
            advice.append("- Monitor for heat stress")
            advice.append("- Continue pest monitoring")
        elif current_month in [9, 10, 11]:  # Fall
            advice.append("\n🍂 Fall Care Tips:")
            advice.append("- Reduce watering frequency")
            advice.append("- Begin preparing for winter")
            advice.append("- Consider winter protection needs")
        else:  # Winter
            advice.append("\n❄️ Winter Care Tips:")
            advice.append("- Reduce watering frequency")
            advice.append("- Protect sensitive plants from frost")
            advice.append("- Monitor for winter damage")

        # Add general advice
        advice.append("\n📋 Daily Monitoring:")
        advice.append("- Check soil moisture levels")
        advice.append("- Look for signs of pest issues")
        advice.append("- Remove any dead or damaged growth")
        advice.append("- Ensure proper air circulation")
        
        return "\n".join(advice)
    except Exception as e:
        logger.error(f"Error analyzing forecast: {e}")
        logger.error(traceback.format_exc())
        return "Error generating plant care advice. Please check plants according to regular care schedule."

def display_weather_advice():
    """Get weather forecast and display plant care advice"""
    try:
        logger.info("Getting weather forecast and generating plant care advice...")
        forecast = get_weather_forecast()
        advice = analyze_forecast_for_plants(forecast)
        
        print("\n=== 🌿 10-Day Plant Care Forecast 🌿 ===")
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nBased on the weather forecast for Houston, here are your plant care recommendations:")
        print(advice)
        print("\n=====================================")
        
    except Exception as e:
        logger.error(f"Error displaying weather advice: {e}")
        print("\nUnable to generate weather-based plant care advice.")
        print("Please follow regular plant care schedule.")

# Display weather-based plant care advice
# display_weather_advice()  # Removing this line so it only runs when called from CLI