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
from test_openai import (
    get_all_plants,
    find_plant_by_id_or_name,
    update_plant_field,
    get_chat_response,
    display_weather_advice,
    setup_sheets_client,
    initialize_sheet,
    gardenbot_response,
    SPREADSHEET_ID,
    RANGE_NAME,
    parse_care_guide,
    update_plant
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GardenBotCLI:
    def __init__(self):
        """Initialize the CLI interface"""
        try:
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("No OpenAI API key found in environment variables")
            
            # Initialize Google Sheets
            initialize_sheet()
            
            logger.info("GardenBot CLI initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise
    
    def handle_command(self, command):
        """Process user commands"""
        try:
            # If it's a help command, show available commands
            if command.lower() == 'help':
                return """Available commands:
                - add plant [name] location [location1, location2, ...]
                - update plant [name/id] location [new_locations]
                - update plant [name/id] url [new_url]
                - remove plant [name] from [location1, location2, ...]
                - remove plant [name] (removes from all locations)
                - list plants
                - list location [location_name]
                - weather
                - help
                
                You can also ask general gardening questions!"""
            
            # If it's a weather command, show weather advice
            if command.lower() == 'weather':
                display_weather_advice()
                return "Weather advice displayed above."
            
            # Handle add plant command
            if command.lower().startswith('add plant '):
                try:
                    # Split command into parts
                    parts = command.split(' location ')
                    if len(parts) != 2:
                        return "Please specify the plant name and location(s). Format: add plant [name] location [location1], [location2], ..."
                    
                    # Extract plant name and clean it
                    plant_name = parts[0].replace('add plant', '', 1).strip()
                    plant_name = ' '.join(word.capitalize() for word in plant_name.split())
                    
                    # Process locations and URL if present
                    location_url_parts = parts[1].split(' url ')
                    locations = [loc.strip() for loc in location_url_parts[0].split(',') if loc.strip()]
                    if not locations:
                        return "Please specify at least one location for the plant."
                    
                    # Extract URL if present
                    photo_url = location_url_parts[1].strip() if len(location_url_parts) > 1 else ''
                    
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
                    
                    # Create plant data with all fields
                    plant_data = {
                        'Plant Name': plant_name,
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
                        'Care Notes': response,
                        'Photo URL': photo_url
                    }
                    
                    # Add the plant to the spreadsheet
                    if update_plant(plant_data):
                        return f"Added plant '{plant_name}' to locations: {', '.join(locations)}\n\nCare guide:\n{response}"
                    else:
                        return f"Error adding plant '{plant_name}' to database"
                    
                except Exception as e:
                    logger.error(f"Error adding plant: {e}")
                    return f"Error adding plant: {str(e)}"
            
            # For all other commands, use the existing gardenbot_response function
            response = gardenbot_response(command)
            return response
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return f"Error processing command: {str(e)}"

def main():
    """Main CLI loop"""
    try:
        cli = GardenBotCLI()
        print("Welcome to GardenBot CLI!")
        print("Type 'help' for available commands or 'exit' to quit.")
        
        while True:
            try:
                command = input("\nEnter command: ").strip()
                
                if command.lower() == 'exit':
                    print("Goodbye!")
                    break
                    
                if command:
                    response = cli.handle_command(command)
                    print("\nResponse:", response)
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
                
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
                print(f"Error: {str(e)}")
                
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main() 