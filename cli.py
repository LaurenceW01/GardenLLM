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
    gardenbot_response,
    get_all_plants,
    find_plant_by_id_or_name,
    update_plant_field,
    get_chat_response,
    display_weather_advice,
    setup_sheets_client,
    initialize_sheet
)

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
        """Initialize the CLI interface"""
        try:
            # Load environment variables
            load_dotenv()
            
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