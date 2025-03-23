from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat_response import get_chat_response
from weather_service import get_weather_forecast, analyze_forecast_for_plants, handle_weather_query
from plant_vision import analyze_plant_image, validate_image, save_image, conversation_manager, client, MODEL_NAME
from plant_operations import update_plant
from test_openai import parse_care_guide
import logging
import os
from typing import Optional, List, Dict
import traceback
from datetime import datetime
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI()

app = FastAPI(title="GardenLLM API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class WeatherResponse(BaseModel):
    forecast: List[Dict]
    plant_care_advice: List[str]

class ImageAnalysisRequest(BaseModel):
    message: Optional[str] = None
    conversation_id: Optional[str] = None

class AddPlantRequest(BaseModel):
    """Request model for adding a plant"""
    name: str
    locations: List[str]
    photo_url: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def home(request: Request):
    # Get current weather for display
    try:
        forecast = get_weather_forecast()
        if not forecast or len(forecast) == 0:
            raise ValueError("No forecast data available")

        # Get plant care advice
        advice = analyze_forecast_for_plants(forecast)
        
        # Extract the most relevant advice sections
        advice_sections = []
        current_section = []
        
        for line in advice.split('\n'):
            if line.strip():
                if any(alert in line for alert in ['Alert:', '🌡️', '☀️', '💧', '🌧️', '💨']):
                    if current_section:
                        advice_sections.append('\n'.join(current_section))
                        current_section = []
                current_section.append(line.strip())
        
        if current_section:
            advice_sections.append('\n'.join(current_section))
        
        # Take the first two most relevant sections
        first_advice = '\n\n'.join(advice_sections[:2]) if advice_sections else "Check plants according to regular schedule"

        current_weather = {
            'temp': f"{forecast[0]['temp_max']}/{forecast[0]['temp_min']}" if forecast else "N/A",
            'conditions': forecast[0]['description'] if forecast else "N/A",
            'advice': first_advice
        }
        
        logger.info(f"Weather data prepared for home page: {current_weather}")
        
    except Exception as e:
        logger.error(f"Error getting weather for home page: {e}")
        logger.error(traceback.format_exc())
        current_weather = {
            'temp': "N/A",
            'conditions': "N/A",
            'advice': "Check plants according to regular schedule"
        }
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "weather": current_weather}
    )

@app.get("/weather")
async def weather_page(request: Request):
    """Weather page with forecast and plant care advice"""
    try:
        # Get weather forecast
        forecast = get_weather_forecast()
        if not forecast:
            return templates.TemplateResponse(
                "weather.html",
                {
                    "request": request,
                    "weather": {"temp": "N/A", "conditions": "N/A", "humidity": "N/A"},
                    "forecast": [],
                    "plant_care": ["Unable to retrieve weather data. Please try again later."]
                }
            )

        # Get current weather
        current_weather = {
            'temp': f"{forecast[0]['temp_max']}/{forecast[0]['temp_min']}",
            'conditions': forecast[0]['description'],
            'humidity': forecast[0]['humidity']
        }

        # Get plant care advice
        advice = analyze_forecast_for_plants(forecast)
        # Split advice into sections for better display
        advice_sections = [section for section in advice.split('\n\n') if section.strip()]

        return templates.TemplateResponse(
            "weather.html",
            {
                "request": request,
                "weather": current_weather,
                "forecast": forecast,
                "plant_care": advice_sections
            }
        )
    except Exception as e:
        logger.error(f"Error in weather page: {e}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "weather.html",
            {
                "request": request,
                "weather": {"temp": "Error", "conditions": "Error", "humidity": "Error"},
                "forecast": [],
                "plant_care": [f"Error loading weather data: {str(e)}"]
            }
        )

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests"""
    try:
        response = get_chat_response(request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "GardenBot server is running"}

@app.get("/api/weather")
async def weather_api():
    """Weather API endpoint for retrieving forecast and plant care advice"""
    try:
        forecast = get_weather_forecast()
        if not forecast:
            raise HTTPException(
                status_code=500,
                detail="Unable to retrieve weather forecast"
            )
        
        advice = analyze_forecast_for_plants(forecast)
        return WeatherResponse(
            forecast=forecast,
            plant_care_advice=advice.split("\n")
        )
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-plant")
async def analyze_plant(
    file: UploadFile = File(...),
    message: Optional[str] = None,
    conversation_id: Optional[str] = None
):
    """Endpoint for analyzing plant images"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Validate image
        if not validate_image(image_data):
            raise HTTPException(
                status_code=400,
                detail="Invalid image format. Please upload a JPEG, PNG, or GIF image."
            )
            
        # Save image
        try:
            file_path = save_image(image_data, file.filename)
            logger.info(f"Image saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            # Continue with analysis even if save fails
            
        # Generate new conversation ID if none provided
        if not conversation_id:
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Generated new conversation ID: {conversation_id}")
            
        # Analyze image with conversation history
        analysis = analyze_plant_image(image_data, message, conversation_id)
        
        logger.info(f"Returning analysis with conversation ID: {conversation_id}")
        return {"response": analysis, "conversation_id": conversation_id}
        
    except Exception as e:
        logger.error(f"Error in analyze_plant endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plants")
async def add_plant(request: AddPlantRequest):
    """Add a new plant to the database"""
    try:
        # Create plant info request
        prompt = (
            f"You are a gardening expert assistant. Create a detailed plant care guide for {request.name} in Houston, TX. "
            "Include care requirements, growing conditions, and maintenance tips. "
            "Focus on practical advice for the specified locations: " + 
            ', '.join(request.locations) + "\n\n" +
            "Format your response with these EXACT section titles - do not modify them:\n" +
            "**Description:**\n" +
            "**Light Requirements:**\n" +
            "**Frost Tolerance:**\n" +
            "**Watering Needs:**\n" +
            "**Soil Preferences:**\n" +
            "**Pruning Instructions:**\n" +
            "**Mulching Needs:**\n" +
            "**Fertilizing Schedule:**\n" +
            "**Winterizing Instructions:**\n" +
            "**Spacing Requirements:**\n\n" +
            "Be specific and detailed in each section. Focus on practical care instructions. "
            "IMPORTANT: Use these exact section titles without modification."
        )
        
        # Get plant care information from OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a gardening expert assistant. Provide detailed, practical plant care guides with specific instructions. Use the exact section titles provided without modification."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract the response text
        care_guide = response.choices[0].message.content
        logger.info(f"Generated care guide: {care_guide}")
        
        # Parse the care guide to extract details
        care_details = parse_care_guide(care_guide)
        logger.info(f"Parsed care details: {care_details}")
        
        # Create plant data with all fields
        plant_data = {
            'Plant Name': request.name,
            'Location': ', '.join(request.locations),
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
            'Care Notes': care_guide,
            'Photo URL': request.photo_url or ''
        }
        
        logger.info(f"Final plant data: {plant_data}")
        
        # Add the plant to the spreadsheet
        if update_plant(plant_data):
            return {
                "success": True,
                "message": f"Added plant '{request.name}' to locations: {', '.join(request.locations)}",
                "care_guide": care_guide,
                "plant_data": plant_data
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error adding plant '{request.name}' to database"
            )
            
    except Exception as e:
        logger.error(f"Error adding plant: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/add-plant", response_class=HTMLResponse)
async def add_plant_page(request: Request):
    """Page for adding new plants"""
    return templates.TemplateResponse(
        "add_plant.html",
        {"request": request}
    )