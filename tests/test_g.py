from google.oauth2 import service_account
from googleapiclient.discovery import build
import traceback
import os

# Google Sheets Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']  # Added drive scope
SERVICE_ACCOUNT_FILE = r'C:\Users\laure\Dev\GardenLLM\gardenllm-5607a1d9d8f3.json'

def create_plant_journal():
    try:
        # Check if service account file exists
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"Error: Service account file not found at {SERVICE_ACCOUNT_FILE}")
            return None
            
        print(f"Found service account file at {SERVICE_ACCOUNT_FILE}")
        
        # Create credentials
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print(f"Service Account Email: {creds.service_account_email}")
        
        # Build the service
        service = build('sheets', 'v4', credentials=creds)
        sheets = service.spreadsheets()
        
        print("Successfully created service...")
        
        # Create a new spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'Plant Journal'
            },
            'sheets': [{
                'properties': {
                    'title': 'Plants',
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                }
            }]
        }
        
        print("Attempting to create spreadsheet...")
        spreadsheet = sheets.create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Get the sheet ID from the created spreadsheet
        sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']
        print(f"Created new Plant Journal with ID: {spreadsheet_id}")
        print(f"Sheet ID: {sheet_id}")
        
        # Set up headers
        headers = [
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
            'Last Updated'
        ]
        
        # Add headers
        sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range='Plants!A1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Format headers with correct sheet ID
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,  # Using the actual sheet ID
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        }]
        
        sheets.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print("Plant Journal initialized successfully!")
        print("\nIMPORTANT: Please update your test_openai.py with this spreadsheet ID:")
        print(f"SPREADSHEET_ID = '{spreadsheet_id}'")
        
        # After creating the spreadsheet, share it with your email
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Your email
        your_email = "laurence.wright01@gmail.com"
        
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={
                'type': 'user',
                'role': 'writer',
                'emailAddress': your_email
            }
        ).execute()
        
        print(f"\nSpreadsheet shared with {your_email}")
        print(f"You can access it at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        
        return spreadsheet_id
        
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    spreadsheet_id = create_plant_journal()