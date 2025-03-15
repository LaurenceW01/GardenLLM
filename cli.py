#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import pytz
from datetime import datetime
import requests
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
SPREADSHEET_ID = '1zmKVuDTbgColGuoHJDF0ZJxXB6N2WfwLkp7LZ0vqOag'
RANGE_NAME = 'Plants!A1:P'

class GardenBotCLI:
    def __init__(self):
        self.openai_client = self.setup_openai_client()
        self.sheets_client = self.setup_sheets_client()
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are a helpful gardening assistant that helps manage a plant journal for a garden in Houston, Texas."
            }
        ]

    def setup_openai_client(self):
        """Initialize OpenAI client for CLI"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("No OpenAI API key found in environment variables")
        
        try:
            import httpx
            client = httpx.Client()
            return OpenAI(
                api_key=api_key,
                http_client=client
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

    def setup_sheets_client(self):
        """Set up Google Sheets client for CLI"""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        try:
            creds_json = os.getenv('GOOGLE_CREDENTIALS')
            if creds_json:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    f.write(creds_json)
                    temp_creds_path = f.name
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        temp_creds_path, scopes=SCOPES)
                finally:
                    os.unlink(temp_creds_path)
            else:
                local_creds_path = os.path.join(os.path.dirname(__file__), 'gardenllm-5607a1d9d8f3.json')
                if not os.path.exists(local_creds_path):
                    raise FileNotFoundError(f"Service account file not found: {local_creds_path}")
                creds = service_account.Credentials.from_service_account_file(
                    local_creds_path, scopes=SCOPES)
            
            service = build('sheets', 'v4', credentials=creds)
            return service.spreadsheets()
            
        except Exception as e:
            logger.error(f"Error setting up sheets client: {e}")
            raise

    def get_all_plants(self):
        """Get all plants from the Google Sheet"""
        try:
            result = self.sheets_client.values().get(
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
                    locations = [loc.strip() for loc in raw_locations if loc.strip()]
                    plants.append({
                        'name': row[name_idx],
                        'location': row[location_idx],
                        'locations': locations
                    })
            
            return plants
        except Exception as e:
            logger.error(f"Error getting plants: {e}")
            return []

    def get_chat_response(self, message: str) -> str:
        """Get a chat response from OpenAI"""
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Limit conversation history
            if len(self.conversation_history) > 6:
                self.conversation_history = [
                    self.conversation_history[0],
                    *self.conversation_history[-5:]
                ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=2000
            )
            
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error in get_chat_response: {str(e)}")
            return f"I encountered an error: {str(e)}"

    def find_plant_by_id_or_name(self, identifier: str) -> tuple:
        """Find a plant by ID or name"""
        try:
            result = self.sheets_client.values().get(
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
            return None, None

    def update_plant_field(self, plant_row: int, field_name: str, new_value: str) -> bool:
        """Update a specific field for a plant"""
        try:
            result = self.sheets_client.values().get(
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
            
            result = self.sheets_client.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [[formatted_value]]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating plant field: {e}")
            return False

    def handle_command(self, command: str) -> str:
        """Process user commands"""
        try:
            lower_cmd = command.lower().strip()
            
            # Handle add plant command
            if lower_cmd.startswith('add plant '):
                # Extract plant name and locations
                parts = command.split(' location')
                if len(parts) != 2:
                    return "Please use format: add plant [name] location [location1], [location2], ..."
                
                plant_name = parts[0].replace('add plant ', '').strip()
                locations = [loc.strip() for loc in parts[1].split(',') if loc.strip()]
                
                if not plant_name or not locations:
                    return "Please specify both plant name and at least one location"
                
                # Create plant info request
                prompt = (
                    f"Create a detailed plant care guide for {plant_name} in Houston, TX. "
                    "Include care requirements, growing conditions, and maintenance tips. "
                    "Focus on practical advice for the specified locations: " + 
                    ', '.join(locations)
                )
                
                response = self.get_chat_response(prompt)
                return f"Added plant '{plant_name}' to locations: {', '.join(locations)}\n\nCare guide:\n{response}"
            
            # Handle remove plant command
            elif lower_cmd.startswith('remove plant '):
                parts = command.split(' from ')
                plant_name = parts[0].replace('remove plant ', '').strip()
                
                if len(parts) > 1:
                    locations = [loc.strip() for loc in parts[1].split(',')]
                    return f"Removing plant '{plant_name}' from locations: {', '.join(locations)}"
                else:
                    return f"Removing plant '{plant_name}' from all locations"
            
            # Handle update commands
            elif lower_cmd.startswith('update ') or lower_cmd.startswith('update plant '):
                parts = command.split()
                start_idx = 2 if lower_cmd.startswith('update plant ') else 1
                
                # Find the first keyword after identifier
                keywords = ['url', 'location']
                field_start_idx = None
                field_type = None
                
                # Find the first keyword in parts
                for i, part in enumerate(parts[start_idx:], start=start_idx):
                    if part.lower() in keywords:
                        field_start_idx = i
                        field_type = part.lower()
                        break
                
                if not field_type:
                    return "Please specify what to update (url or location)"
                
                # Extract identifier (everything between start_idx and field_start_idx)
                identifier = ' '.join(parts[start_idx:field_start_idx])
                if not identifier:
                    return "Please specify plant ID or name"
                
                # Find the plant
                plant_row, plant_data = self.find_plant_by_id_or_name(identifier)
                if not plant_row:
                    return f"Plant '{identifier}' not found"
                
                # Handle URL update
                if field_type == 'url':
                    url_value = ' '.join(parts[field_start_idx + 1:])
                    if not url_value:
                        return "Please provide a URL value"
                    
                    if self.update_plant_field(plant_row, 'Photo URL', url_value):
                        return f"Successfully updated photo URL for plant {identifier}"
                    else:
                        return f"Failed to update photo URL for plant {identifier}"
                
                # Handle location update
                elif field_type == 'location':
                    new_locations = [loc.strip() for loc in ' '.join(parts[field_start_idx + 1:]).split(',')]
                    if not new_locations:
                        return "Please specify new locations"
                    
                    if self.update_plant_field(plant_row, 'Location', ', '.join(new_locations)):
                        return f"Successfully updated locations for plant {identifier}"
                    else:
                        return f"Failed to update locations for plant {identifier}"
            
            # Handle list location command
            elif lower_cmd.startswith('list location '):
                location = command.replace('list location ', '').strip()
                plants = self.get_all_plants()
                matching_plants = [p for p in plants if location.lower() in [loc.lower() for loc in p['locations']]]
                
                if matching_plants:
                    response = f"\nPlants in {location}:\n"
                    for plant in sorted(matching_plants, key=lambda x: x['name']):
                        response += f"- {plant['name']}\n"
                    return response
                else:
                    return f"No plants found in location: {location}"
            
            # Handle weather command
            elif lower_cmd == 'weather':
                return "Weather information is currently unavailable in CLI mode"
            
            # For unrecognized commands, get a chat response
            return self.get_chat_response(command)
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return f"Error processing command: {str(e)}"

def print_help():
    """Display help information"""
    print("""
GardenBot CLI Commands:
----------------------
add plant [name] location [location1], [location2], ...  - Add a new plant with locations
remove plant [name] from [location1], [location2], ...   - Remove plant from specific locations
remove plant [name]                                      - Remove plant from all locations
update plant [name] location [new_locations]             - Update plant locations
update plant [name] url [photo_url]                      - Update plant photo URL
list plants                                             - List all plants in the garden
list location [location_name]                           - List plants in a specific location
weather                                                 - Get current weather and plant care advice
help                                                    - Show this help message
exit                                                    - Exit the program

Examples:
---------
add plant "Tomato" location garden bed 1, patio
remove plant "Basil" from kitchen garden, patio
update plant "Rose" location front yard, side garden
list location "garden bed 1"
""")

def main():
    """Main CLI loop"""
    print("\nWelcome to GardenBot CLI!")
    print("Type 'help' for available commands or 'exit' to quit.")
    
    try:
        # Initialize GardenBot CLI
        bot = GardenBotCLI()
        logger.info("Successfully initialized GardenBot CLI")
        
        while True:
            try:
                # Get user input
                command = input("\n>>> ").strip()
                
                # Exit condition
                if command.lower() == 'exit':
                    print("Goodbye!")
                    break
                    
                # Help command
                if command.lower() == 'help':
                    print_help()
                    continue
                    
                # List all plants
                if command.lower() == 'list plants':
                    plants = bot.get_all_plants()
                    print("\nCurrent Plants in Garden:")
                    print("-------------------------")
                    for plant in sorted(plants, key=lambda x: x['name']):
                        print(f"\n{plant['name']}:")
                        print(f"Locations: {plant['location']}")
                    continue
                
                # Process other commands
                response = bot.handle_command(command)
                print("\nResponse:", response)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                print(f"\nAn error occurred: {str(e)}")
                print("Type 'help' for available commands.")
                
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        print(f"\nFailed to initialize GardenBot: {str(e)}")
        print("Please check your environment variables and credentials.")
        sys.exit(1)

if __name__ == "__main__":
    main() 