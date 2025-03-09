# from dotenv import load_dotenv
from click import prompt
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import json
from openai import OpenAI  # New import style

# Google Sheets Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = r'C:\Users\laure\Dev\GardenLLM\gardenllm-5607a1d9d8f3.json'
SPREADSHEET_ID = '1zmKVuDTbgColGuoHJDF0ZJxXB6N2WfwLkp7LZ0vqOag'
SHEET_GID = '828349954'
RANGE_NAME = 'Plants!A1:P'

def setup_sheets_client():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

# Initialize Sheets client
sheets_client = setup_sheets_client()

# Initialize OpenAI client
client = OpenAI()  # This will use your OPENAI_API_KEY environment variable

def initialize_sheet():
    """Initialize the plant journal sheet with headers"""
    try:
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
    except Exception as e:
        print(f"Error initializing sheet: {e}")
        import traceback
        traceback.print_exc()

# Initialize the sheet
initialize_sheet()

# Initialize Conversation Memory
conversation_history = [
    {
        "role": "system",
        "content": """You are a helpful gardening assistant that helps manage a plant journal for a garden in Houston, Texas. 
        When updating plants, use these exact field names:
        - ID
        - Plant Name
        - Description
        - Location
        - Light Requirements
        - Frost Tolerance
        - Watering Needs
        - Soil Preferences
        - Pruning Instructions
        - Mulching Needs
        - Fertilizing Schedule
        - Winterizing Instructions
        - Spacing Requirements
        - Care Notes
        - Photo URL
        - Last Updated
        
        Example response for updates:
        {
            "id": 1,
            "field": "Photo URL",  # Use exact field name
            "value": "https://photos.google.com/xxx"
        }
        
        When a user adds a plant with 'add plant' followed by a name and location, you must:
        1. Create a JSON object with the provided name and location
        2. Fill in all other fields with appropriate information for growing that plant in Houston's climate
        3. If a photo URL is provided, include it in the JSON
        
        Users can update existing plants using their ID:
        "update plant 1 location: new backyard"
        "update plant 2 watering: twice weekly"
        
        Example inputs:
        "add plant Name: Tomato Location: Back garden"
        "add plant Name: Rose Location: Front yard Photo: https://photos.google.com/share/xxx"
        
        Example response:
        {
            "name": "Tomato",
            "location": "Back garden",
            "description": "Heat-tolerant tomato variety suitable for Houston's climate",
            "light": "Full sun, with afternoon shade during peak summer",
            "frost_tolerance": "Protect when temperatures drop below 40°F, typical during Houston winters",
            "watering": "Regular watering, 1-2 inches per week, more during summer heat",
            "soil": "Well-draining amended clay soil, pH 6.0-6.8",
            "pruning": "Remove suckers and lower leaves to improve air circulation in humid climate",
            "mulching": "3 inches of mulch to retain moisture and protect from extreme heat",
            "fertilizing": "Monthly balanced fertilizer during growing season, March through November",
            "winterizing": "Remove plants after fall harvest, protect any late producers from occasional freezes",
            "spacing": "24-36 inches between plants for good air flow in humid conditions",
            "care_notes": "Plant in spring (Feb-March) or fall (Sept) to avoid peak summer heat",
            "photo_url": "https://photos.google.com/share/xxx"
        }
        
        To add a photo later, users can say:
        "add photo https://photos.google.com/xxx to Tomato"
        
        Always start your response with the complete JSON object, followed by any additional advice.
        Make all recommendations specific to Houston's growing conditions."""
    }
]

def get_next_id():
    """Get the next available ID number"""
    try:
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:A'  # Get all IDs from first column
        ).execute()
        
        values = result.get('values', [])
        if len(values) <= 1:  # Only header or empty
            return 1
            
        # Filter out header and empty values, convert to integers
        ids = [int(row[0]) for row in values[1:] if row and row[0].isdigit()]
        return max(ids, default=0) + 1
        
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
            
        # Create row with all fields
        row = [
            str(next_id),
            plant_data.get('name', ''),
            plant_data.get('description', ''),
            plant_data.get('location', ''),
            plant_data.get('light', ''),
            plant_data.get('frost_tolerance', ''),
            plant_data.get('watering', ''),
            plant_data.get('soil', ''),
            plant_data.get('pruning', ''),
            plant_data.get('mulching', ''),
            plant_data.get('fertilizing', ''),
            plant_data.get('winterizing', ''),
            plant_data.get('spacing', ''),
            plant_data.get('care_notes', ''),
            f'=IMAGE("{plant_data.get("photo_url", "")}")' if plant_data.get('photo_url') else "",
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

def update_plant_field(plant_id, field_name, new_value):
    """Update a specific field for a plant by ID"""
    try:
        # Get current values
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:P'  # Include all columns
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print("No data found in sheet")
            return "No plants found in the database"
            
        # Get headers to map field names to column indices
        headers = values[0]
        print("Available headers:", headers)  # Debug print
        
        # Try to match the field name with headers
        field_name = field_name.strip()
        if field_name.lower() == "photo url" or field_name.lower() == "photo_url":
            field_name = "Photo URL"  # Match exact header name
            if new_value:  # Only wrap in IMAGE() if there's a URL
                new_value = f'=IMAGE("{new_value}")'
        
        try:
            column_index = headers.index(field_name)
            print(f"Found field '{field_name}' at column {column_index}")  # Debug print
        except ValueError:
            error_msg = f"Field '{field_name}' not found. Available fields are: {', '.join(headers)}"
            print(error_msg)
            return error_msg
        
        # Find the row for the given ID
        row_index = None
        for i, row in enumerate(values):
            if row[0] == str(plant_id):
                row_index = i
                break
        
        if row_index is None:
            error_msg = f"Plant ID {plant_id} not found. Please check the ID and try again."
            print(error_msg)
            return error_msg
        
        # Update the field
        range_name = f'Plants!{chr(65 + column_index)}{row_index + 1}'
        print(f"Updating range: {range_name} with value: {new_value}")  # Debug print
        
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': [[new_value]]}
        ).execute()
        
        success_msg = f"Updated {field_name} for plant ID {plant_id}"
        print(success_msg)
        return True
        
    except Exception as e:
        error_msg = f"Error updating plant field: {e}"
        print(error_msg)
        print("Full error details:")
        import traceback
        traceback.print_exc()
        return error_msg

def gardenbot_response(user_input):
    global conversation_history
    
    print(f"\n=== Processing new user input ===")
    print(f"Input: {user_input}")
    
    # Format the input if it's a plant addition
    if user_input.lower().startswith('add') and 'to' in user_input.lower():
        # Convert "Add a hibiscus to the patio" to "add plant Name: Hibiscus Location: Patio"
        parts = user_input.lower().split('to')
        plant_name = parts[0].replace('add', '').replace('a', '').strip()
        location = parts[1].strip()
        formatted_input = f"add plant Name: {plant_name.title()} Location: {location.title()}"
        print(f"Formatted input: {formatted_input}")
        user_input = formatted_input
    
    # Add user input to conversation history
    conversation_history.append({"role": "user", "content": user_input})
    print("\nConversation history:", conversation_history)  # Debug print
    
    try:
        print("\nSending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_history
        )
        
        assistant_response = response.choices[0].message.content
        print(f"\nFull assistant response:\n{assistant_response}")
        
        # Handle update commands
        if user_input.lower().startswith('update plant'):
            try:
                parts = user_input.split(' ', 3)  # Split into ['update', 'plant', 'ID', 'field: value']
                if len(parts) >= 4:
                    plant_id = int(parts[2])
                    field_parts = parts[3].split(':', 1)
                    if len(field_parts) == 2:
                        field_name = field_parts[0].strip()
                        new_value = field_parts[1].strip()
                        result = update_plant_field(plant_id, field_name, new_value)
                        if isinstance(result, str):  # If we got an error message back
                            return f"Error: {result}"
                        elif result:
                            return f"Successfully updated {field_name} for plant ID {plant_id}"
                        else:
                            return f"Failed to update {field_name} for plant ID {plant_id}"
                return "Invalid update command format. Use: update plant [ID] [field]: [value]"
            except ValueError:
                return "Invalid plant ID. Please provide a valid number."
            except Exception as e:
                error_msg = f"Error processing update command: {e}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                return error_msg
        
        # Handle add plant command
        elif user_input.lower().startswith('add plant'):
            print("\nDetected plant command, looking for JSON data...")
            try:
                # Look for JSON data in the response
                json_start = assistant_response.find('{')
                json_end = assistant_response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = assistant_response[json_start:json_end]
                    print(f"\nExtracted JSON string:\n{json_str}")
                    
                    # Clean up the JSON string
                    json_str = json_str.strip()
                    if not json_str.endswith('}'):
                        print("JSON string doesn't end with }, fixing...")
                        json_str = json_str[:json_str.rfind('}')+1]
                    
                    print(f"\nCleaned JSON string:\n{json_str}")
                    plant_data = json.loads(json_str)
                    print("\nParsed plant data:", plant_data)
                    
                    # Map the fields directly to our expected format
                    field_mapping = {
                        'Plant Name': 'name',
                        'Description': 'description',
                        'Location': 'location',
                        'Light Requirements': 'light',
                        'Frost Tolerance': 'frost_tolerance',
                        'Watering Needs': 'watering',
                        'Soil Preferences': 'soil',
                        'Pruning Instructions': 'pruning',
                        'Mulching Needs': 'mulching',
                        'Fertilizing Schedule': 'fertilizing',
                        'Winterizing Instructions': 'winterizing',
                        'Spacing Requirements': 'spacing',
                        'Care Notes': 'care_notes',
                        'Photo URL': 'photo_url'
                    }
                    
                    standardized_data = {}
                    for key, value in plant_data.items():
                        if key in field_mapping:
                            standardized_data[field_mapping[key]] = value
                    
                    print("\nStandardized data:", standardized_data)
                    
                    # Ensure required fields exist
                    required_fields = ['name', 'location']
                    if all(field in standardized_data for field in required_fields):
                        print("\nRequired fields present, attempting to log plant...")
                        # Try to add plant up to 3 times
                        for attempt in range(3):
                            print(f"\nAttempt {attempt + 1} to add plant to sheet")
                            if log_plant_to_sheets(standardized_data):
                                print("Plant data successfully logged to sheet")
                                break
                            else:
                                print(f"Attempt {attempt + 1} failed, {'retrying' if attempt < 2 else 'giving up'}")
                        else:
                            print("Failed to add plant after 3 attempts")
                    else:
                        print(f"Missing required fields. Found fields: {list(standardized_data.keys())}")
                else:
                    print("No JSON data found in response")
                print("Full response:", assistant_response)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print("JSON string attempted to parse:", json_str)
                print("Full response:", assistant_response)
            except Exception as e:
                print(f"Unexpected error processing plant data: {e}")
                import traceback
                traceback.print_exc()
        
        # Add assistant's response to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        print(error_msg)
        print("Full error details:")
        import traceback
        traceback.print_exc()
        return error_msg

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

print("GardenBot is ready! Type 'exit' to end the conversation.")
while True:
    user_input = input(">>> ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    response = gardenbot_response(user_input)
    print(f"GardenBot: {response}")