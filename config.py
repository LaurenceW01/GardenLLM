from dotenv import load_dotenv
import os
import logging
import traceback
import httpx
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Google Sheets Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '1zmKVuDTbgColGuoHJDF0ZJxXB6N2WfwLkp7LZ0vqOag'
SHEET_GID = '828349954'
RANGE_NAME = 'Plants!A1:P'

# API Rate Limiting
SHEETS_REQUESTS = {}  # Track API requests
MAX_REQUESTS_PER_MINUTE = 30
RATE_LIMIT_SLEEP = 2
QUOTA_RESET_INTERVAL = 60

# Initialize OpenAI client
def init_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("No OpenAI API key found in environment variables")
    
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
    
    # Test connection
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    logger.info(f"OpenAI connection successful. Test response: {test_response}")
    return client

# Initialize Google Sheets client
def init_sheets_client():
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
                time.sleep(1)
    
    if sheets_client is None:
        raise RuntimeError("Could not initialize Google Sheets client")
    
    return sheets_client

def setup_sheets_client() -> Resource:
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
                logger.error(f"Service account file not found: {local_creds_path}")
                return None
            creds = service_account.Credentials.from_service_account_file(
                local_creds_path, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        sheets = service.spreadsheets()
        sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        return sheets
        
    except Exception as e:
        logger.error(f"Error setting up sheets client: {e}")
        logger.error(traceback.format_exc())
        return None

# Initialize clients
try:
    openai_client = init_openai_client()
    sheets_client = init_sheets_client()
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    logger.error(traceback.format_exc())
    raise 