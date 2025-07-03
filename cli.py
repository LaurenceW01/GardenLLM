#!/usr/bin/env python3
"""Command Line Interface for GardenLLM - A gardening assistant chatbot"""

import sys  # System-specific parameters and functions
import os  # Operating system interface
from dotenv import load_dotenv  # Load environment variables from .env file
import logging  # Logging facility for Python
from openai import OpenAI  # OpenAI API client
from google.oauth2 import service_account  # Google OAuth2 service account credentials
from googleapiclient.discovery import build  # Google API client library
import json  # JSON encoder and decoder
import pytz  # World timezone definitions
from datetime import datetime  # Basic date and time types
import requests  # HTTP library for Python
from typing import List, Dict  # Type hints for better code documentation
from plant_operations import (
    get_all_plants,  # Get all plants from the database
    find_plant_by_id_or_name,  # Find a specific plant by ID or name
    update_plant_field,  # Update a specific field for a plant
    update_plant  # Add or update a plant in the database
)
from chat_response import get_chat_response  # Generate chat responses for user queries
from weather_service import get_weather_forecast, analyze_forecast_for_plants, handle_weather_query  # Weather-related functions
from test_openai import setup_sheets_client, initialize_sheet, parse_care_guide, SPREADSHEET_ID, RANGE_NAME  # OpenAI and sheet utilities

# Set up logging configuration for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file for API keys and configuration
load_dotenv()

class GardenBotCLI:
    """Main CLI class for handling user commands and plant operations"""
    
    def __init__(self):
        """Initialize the CLI interface with OpenAI and Google Sheets connections"""
        try:
            # Initialize OpenAI client by checking for API key in environment variables
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("No OpenAI API key found in environment variables")
            
            # Initialize Google Sheets connection and setup
            initialize_sheet()
            
            logger.info("GardenBot CLI initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise
    
    def handle_command(self, command):
        """Process user commands and route them to appropriate handlers"""
        try:
            # If it's a help command, show available commands and usage instructions
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
            
            # If it's a weather command, get weather forecast and provide plant-specific advice
            if command.lower() == 'weather':
                forecast = get_weather_forecast()  # Get current weather data
                return analyze_forecast_for_plants(forecast)  # Analyze weather for plant care
            
            # Handle add plant command - parse plant name, locations, and optional photo URL
            if command.lower().startswith('add plant '):
                try:
                    # Extract the command parts after "add plant" keyword
                    command_parts = command[len('add plant '):].strip()
                    
                    # Find the location keyword to separate plant name from locations
                    location_index = command_parts.lower().find('location')
                    if location_index == -1:
                        return "Please specify the location using 'location' keyword. Format: add plant [name] location [location1], [location2], ..."
                    
                    # Split command into plant name (before 'location') and locations part (after 'location')
                    plant_name = command_parts[:location_index].strip()
                    locations_part = command_parts[location_index + len('location'):].strip()
                    
                    # Process locations and URL if present - split by 'url' keyword
                    location_url_parts = locations_part.split(' url ')
                    locations = [loc.strip() for loc in location_url_parts[0].split(',') if loc.strip()]  # Parse comma-separated locations
                    if not locations:
                        return "Please specify at least one location for the plant."
                    
                    # Extract optional photo URL if provided after 'url' keyword
                    photo_url = location_url_parts[1].strip() if len(location_url_parts) > 1 else ''
                    
                    # Create detailed plant care guide prompt for OpenAI
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
                    
                    # Get plant care information from OpenAI directly using GPT-4 Turbo
                    from config import openai_client  # Import OpenAI client for direct API calls
                    response = openai_client.chat.completions.create(
                        model="gpt-4-turbo-preview",  # Use latest GPT-4 model for best results
                        messages=[
                            {"role": "system", "content": "You are a gardening expert assistant. Provide detailed, practical plant care guides with specific instructions. Use the exact section titles provided without modification."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,  # Balance between creativity and consistency
                        max_tokens=1000  # Limit response length for efficiency
                    )
                    response = response.choices[0].message.content or ""  # Extract response text, default to empty string if None
                    
                    # Parse the care guide response to extract structured data for database storage
                    care_details = parse_care_guide(response)
                    
                    # Create comprehensive plant data dictionary with all required fields for database
                    plant_data = {
                        'Plant Name': plant_name,  # Name of the plant
                        'Location': ', '.join(locations),  # Comma-separated list of locations
                        'Description': care_details.get('Description', ''),  # Plant description from AI
                        'Light Requirements': care_details.get('Light Requirements', ''),  # Light needs
                        'Soil Preferences': care_details.get('Soil Preferences', ''),  # Soil requirements
                        'Watering Needs': care_details.get('Watering Needs', ''),  # Watering instructions
                        'Frost Tolerance': care_details.get('Frost Tolerance', ''),  # Cold tolerance
                        'Pruning Instructions': care_details.get('Pruning Instructions', ''),  # Pruning guidance
                        'Mulching Needs': care_details.get('Mulching Needs', ''),  # Mulching requirements
                        'Fertilizing Schedule': care_details.get('Fertilizing Schedule', ''),  # Fertilizer needs
                        'Winterizing Instructions': care_details.get('Winterizing Instructions', ''),  # Winter care
                        'Spacing Requirements': care_details.get('Spacing Requirements', ''),  # Planting spacing
                        'Care Notes': response,  # Full AI-generated care guide
                        'Photo URL': photo_url  # Optional photo URL
                    }
                    
                    # Add the plant to the Google Sheets database and return success/error message
                    if update_plant(plant_data):
                        return f"Added plant '{plant_name}' to locations: {', '.join(locations)}\n\nCare guide:\n{response}"
                    else:
                        return f"Error adding plant '{plant_name}' to database"
                    
                except Exception as e:
                    logger.error(f"Error adding plant: {e}")  # Log the error for debugging
                    return f"Error adding plant: {str(e)}"  # Return user-friendly error message
            
            # For all other commands, use the chat response function to handle general gardening questions
            response = get_chat_response(command)  # Generate AI response for non-command queries
            return response
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")  # Log any unexpected errors
            return f"Error processing command: {str(e)}"  # Return generic error message

def main():
    """Main CLI loop - handles user input and command processing"""
    try:
        cli = GardenBotCLI()  # Initialize the CLI interface
        print("Welcome to GardenBot CLI!")  # Display welcome message
        print("Type 'help' for available commands or 'exit' to quit.")  # Show usage instructions
        
        while True:  # Main command loop - runs until user exits
            try:
                command = input("\nEnter command: ").strip()  # Get user input and remove whitespace
                
                if command.lower() == 'exit':  # Check for exit command
                    print("Goodbye!")  # Display farewell message
                    break  # Exit the loop
                    
                if command:  # Process non-empty commands
                    response = cli.handle_command(command)  # Process the command and get response
                    print("\nResponse:", response)  # Display the response to user
                    
            except KeyboardInterrupt:  # Handle Ctrl+C gracefully
                print("\nGoodbye!")  # Display farewell message
                break  # Exit the loop
                
            except Exception as e:  # Handle any unexpected errors in command processing
                logger.error(f"Error in command loop: {e}")  # Log the error
                print(f"Error: {str(e)}")  # Display error to user
                
    except Exception as e:  # Handle fatal initialization errors
        logger.error(f"Fatal error in main: {e}")  # Log the fatal error
        print(f"Fatal error: {str(e)}")  # Display fatal error to user

if __name__ == "__main__":
    main() 