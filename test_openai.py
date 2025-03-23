from dotenv import load_dotenv
import os
from click import prompt
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from datetime import datetime, timedelta
import json
from openai import OpenAI
import logging
import traceback
import pytz
import requests
from typing import List, Dict, Optional, Any, cast
import math
import time
from time import sleep
import httpx

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
        sheets = cast(Resource, service.spreadsheets())
        
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
        
    # Create httpx client without proxies for direct connection
    http_client = httpx.Client(
        timeout=60.0,
        follow_redirects=True
    )
        
    client = OpenAI(
        api_key=api_key,
        http_client=http_client,
        base_url="https://api.openai.com/v1",
        max_retries=2
    )

    # Test the OpenAI connection
    logger.info("Testing OpenAI connection...")
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    logger.info(f"OpenAI connection successful. Test response: {test_response}")
except Exception as e:
    logger.error(f"OpenAI connection failed: {str(e)}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")

def initialize_sheet(start_cli=False):
    """Initialize the Google Sheet with headers and formatting"""
    print("Initializing sheet with new headers including ID...")
    # Get the spreadsheet metadata to find the sheet ID
    spreadsheet = sheets_client.get(spreadsheetId=SPREADSHEET_ID).execute()
    
    # Use the correct sheet ID from the URL
    sheet_id = int(SHEET_GID)
    
    # Define column headers for the sheet
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
        'Raw Photo URL',
        'Last Updated'
    ]
    
    # Check if headers already exist
    result = sheets_client.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Plants!A1:P1'
    ).execute()
    
    if not result.get('values'):
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
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': 14,
                'endIndex': 15
            },
            'properties': {
                'pixelSize': 200
            },
            'fields': 'pixelSize'
        }
    }, {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 1
            },
            'properties': {
                'pixelSize': 150
            },
            'fields': 'pixelSize'
        }
    }]
    
    # Apply formatting requests
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

def get_photo_url_from_album(photo_url):
    """Convert Google Photos URL to publicly accessible format"""
    try:
        if 'photos.google.com' in photo_url:
            if '?share=' not in photo_url:
                if '?' in photo_url:
                    photo_url += '&share=true'
                else:
                    photo_url += '?share=true'
            
            if '&key=' not in photo_url:
                photo_url += '&key=public'
                
            logger.info(f"Formatted photo URL: {photo_url}")
            return photo_url
        return photo_url
    except Exception as e:
        logger.error(f"Error formatting photo URL: {e}")
        return photo_url

def parse_care_guide(response: str) -> Dict[str, str]:
    """Parse the care guide response from OpenAI into a structured dictionary.
    
    Args:
        response (str): The response text from OpenAI containing the care guide
        
    Returns:
        Dict[str, str]: A dictionary containing parsed care guide sections
    """
    # Initialize the dictionary with empty values for all expected fields
    care_details = {
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
    }
    
    try:
        # Split the response into sections based on the ** markers
        sections = response.split('**')
        
        # Process each section
        for section in sections:
            if not section.strip():
                continue
                
            # Split section into title and content
            parts = section.split(':', 1)
            if len(parts) != 2:
                continue
                
            title = parts[0].strip()
            content = parts[1].strip()
            
            # Remove any leading/trailing whitespace and newlines
            content = ' '.join(content.split())
            
            # Store content if title matches exactly
            if title in care_details:
                care_details[title] = content
                logger.info(f"Parsed section '{title}': {content[:50]}...")
    except Exception as e:
        logger.error(f"Error parsing care guide: {e}")
        logger.error(f"Response: {response}")
    
    # Verify all sections were found
    missing_sections = [title for title, content in care_details.items() if not content]
    if missing_sections:
        logger.warning(f"Missing sections in care guide: {missing_sections}")
    
    return care_details