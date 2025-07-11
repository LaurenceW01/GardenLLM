from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import json

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

def generate_schema():
    # Initialize Sheets client
    sheets_client = setup_sheets_client()
    
    try:
        # Get the data from the sheet
        result = sheets_client.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print('No data found.')
            return
            
        # Convert to DataFrame for easier processing
        headers = values[0]
        data = values[1:]
        df = pd.DataFrame(data, columns=headers)
        
        # Generate schema
        schema = {
            "spreadsheet_id": SPREADSHEET_ID,
            "sheet_gid": SHEET_GID,
            "range": RANGE_NAME,
            "columns": []
        }
        
        for col in df.columns:
            # Get all non-null values in the column
            non_null_values = df[col].dropna().tolist()
            
            # Try to infer type from values
            inferred_type = "string"  # default type
            if non_null_values:
                # Check if all values are numeric
                if all(str(x).replace('.','',1).isdigit() for x in non_null_values):
                    if all(float(x).is_integer() for x in non_null_values):
                        inferred_type = "integer"
                    else:
                        inferred_type = "float"
                # Check if values are formulas (start with =)
                elif any(str(x).startswith('=') for x in non_null_values):
                    inferred_type = "formula"
            
            schema["columns"].append({
                "name": col,
                "type": inferred_type,
                "nullable": True,  # Google Sheets allows null values by default
                "sample_values": non_null_values[:3] if non_null_values else [],
                "column_index": headers.index(col)
            })
        
        # Save schema to a JSON file
        with open('sheet_schema.json', 'w') as f:
            json.dump(schema, f, indent=2, default=str)
        
        print("Schema has been saved to 'sheet_schema.json'")
        print("\nSchema preview:")
        print(json.dumps(schema, indent=2, default=str))
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    generate_schema()
