import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta

# Set up Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("c:/Users/laure/Dev/GardenLLM/gardenllm-f39105570bf0.json", scope)

# Connect to the Google Sheet
client = gspread.authorize(credentials)

# Add a New Plant
def add_new_plant(plant_name, location, watering_frequency, last_watered, photo_link="", images="", light_preference="", frost_tolerance="", care_notes=""):
    sheet.append_row([plant_name, location, watering_frequency, last_watered, photo_link, images, light_preference, frost_tolerance, care_notes])
    return f"Added {plant_name} to your gardening journal."

# Update Existing Plant
def update_plant_last_watered(plant_name, new_date):
    records = sheet.get_all_records()
    for idx, record in enumerate(records, start=2):  # Start at row 2 (after headers)
        if record["Plant Name"].lower() == plant_name.lower():
            sheet.update_cell(idx, 4, new_date)  # Update "Last Watered" column
            return f"Updated {plant_name}'s last watered date to {new_date}."
    return f"Plant {plant_name} not found in your journal."

# Chatbot Response for Updates
def chatbot_response(user_input):
    if "add a new plant" in user_input.lower():
        # Example: Extract plant details
        plant_name = "Lavender"
        watering_frequency = "Every 5 days"
        last_watered = "2025-01-21"
        location = "Right Arboretum"
        return add_new_plant(plant_name, location, watering_frequency, last_watered)

    elif "update the last watered date" in user_input.lower():
        # Example: Extract plant name and new date
        plant_name = "Rose"
        new_date = "2025-01-21"
        return update_plant_last_watered(plant_name, new_date)

    else:
        return "I'm not sure about that. Can you rephrase?"


# Remember to share the spreadsheet with the email address in the JSON credentials file.
sheet = client.open("Plant Dictionary Template").sheet1

def get_plants_needing_watering():
    records = sheet.get_all_records()
    today = datetime.now().date()
    plants_to_water = []

    for record in records:
        last_watered = datetime.strptime(record["Last Watered"], "%Y-%m-%d").date()
        watering_freq = int(record["Watering Frequency"].split()[1])  # Extract frequency number
        next_watering_date = last_watered + timedelta(days=watering_freq)

        if next_watering_date <= today:
            plants_to_water.append(record["Plant Name"])

    return plants_to_water

# openai.api_key = "YOUR_OPENAI_API_KEY"
client = ChatOpenAI(model="gpt-4o")
prompt_template = ChatPromptTemplate.from_messages(
 [
        ("system", "You are a helpful gardening assistant."),
        ("human", "How frequently do roses need watering in Houston Texas in winter?"),
    ]
)     
chain = prompt_template | client | StrOutputParser()
# Run the chain
#result = chain.invoke({})

#print(result)

# Example Usage
user_query = "Add a new plant."
bot_response = chatbot_response(user_query)
print("Bot:", bot_response)
