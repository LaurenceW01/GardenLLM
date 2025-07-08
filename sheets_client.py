from datetime import datetime, timedelta
import logging
from time import sleep
from typing import List, Dict, Optional, Any
from config import (
    sheets_client, SPREADSHEET_ID, RANGE_NAME, SHEETS_REQUESTS,
    MAX_REQUESTS_PER_MINUTE, QUOTA_RESET_INTERVAL, SHEET_GID
)
from field_config import get_all_field_names

logger = logging.getLogger(__name__)

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
        sleep(QUOTA_RESET_INTERVAL)
        SHEETS_REQUESTS.clear()
    
    # Track this request
    SHEETS_REQUESTS[current_time] = SHEETS_REQUESTS.get(current_time, 0) + 1

def initialize_sheet(start_cli=False):
    """Initialize the Google Sheet with headers and formatting"""
    print("Initializing sheet with new headers including ID...")
    spreadsheet = sheets_client.get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_id = int(SHEET_GID)
    
    # Use field_config to get all field names
    headers = get_all_field_names()
    
    # Check if headers exist
    result = sheets_client.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Plants!A1:Q1'
    ).execute()
    
    if not result.get('values'):
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
    
    # Format headers and dimensions
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
                'startIndex': 14,  # Photo URL column
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
                'dimension': 'COLUMNS',
                'startIndex': 15,  # Raw Photo URL column
                'endIndex': 16
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
    
    sheets_client.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    # Add formula to extract URLs from IMAGE formulas in the Raw Photo URL column
    result = sheets_client.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Plants!A2:O'  # Get all rows except header, up to Photo URL column
    ).execute()
    
    values = result.get('values', [])
    if values:
        formulas = []
        for i in range(len(values)):
            row_num = i + 2  # Start from row 2 (after header)
            formula = f'=IF(O{row_num}<>"", REGEXEXTRACT(FORMULATEXT(O{row_num}), """(https?://[^""]+)"""), "")'
            formulas.append([formula])
        
        # Update Raw Photo URL column with formulas
        sheets_client.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'Plants!P2:P{len(values)+1}',
            valueInputOption='USER_ENTERED',
            body={'values': formulas}
        ).execute()
    
    print("Sheet initialized successfully!")
    
    if start_cli:
        print("GardenBot is ready! Type 'exit' to end the conversation.")
        print(">>>")

def get_next_id() -> Optional[str]:
    """Get next available ID from sheet"""
    try:
        values = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Plants!A:A'
        ).execute()
        
        ids = [row[0] for row in values.get('values', [])[1:] if row and row[0]]
        
        if not ids:
            return "1"
            
        numeric_ids = []
        for id_str in ids:
            try:
                numeric_ids.append(int(id_str))
            except ValueError:
                continue
                
        if not numeric_ids:
            return "1"
            
        return str(max(numeric_ids) + 1)
        
    except Exception as e:
        print(f"Error getting next ID: {e}")
        return None 