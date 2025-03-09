from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from test_openai import gardenbot_response, get_weather_forecast, analyze_forecast_for_plants
import logging
import os
from typing import Optional, List, Dict
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class WeatherResponse(BaseModel):
    forecast: List[Dict]
    plant_care_advice: List[str]

def handle_weather_query(message: str) -> str:
    """Handle weather-related queries and return formatted response"""
    try:
        logger.info("Getting weather forecast...")
        forecast = get_weather_forecast()
        if not forecast:
            return "I'm sorry, I couldn't retrieve the weather forecast at this time."

        advice = analyze_forecast_for_plants(forecast)
        
        # Format the response
        response = "🌿 Weather Forecast and Plant Care Advice 🌿\n\n"
        
        # Add forecast summary
        response += "Weather Forecast:\n"
        for day in forecast[:5]:  # Show next 5 days
            response += f"\n📅 {day['date']}:\n"
            response += f"• Temperature: {day['temp_min']}°F to {day['temp_max']}°F\n"
            response += f"• Conditions: {day['description']}\n"
            response += f"• Rain: {day['rain']} inches\n"
            response += f"• Humidity: {day['humidity']}%\n"
            response += f"• Wind: {day['wind_speed']} mph\n"
        
        # Add plant care advice
        response += "\n🌱 Plant Care Recommendations:\n"
        response += advice
        
        return response
    except Exception as e:
        logger.error(f"Error handling weather query: {e}")
        logger.error(traceback.format_exc())
        return "I'm sorry, I encountered an error while processing the weather information."

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get current weather for display
    forecast = get_weather_forecast()
    current_weather = {
        'temp': f"{forecast[0]['temp_max']}/{forecast[0]['temp_min']}" if forecast else "N/A",
        'conditions': forecast[0]['description'] if forecast else "N/A",
        'advice': "Check plants according to regular schedule" if not forecast else analyze_forecast_for_plants(forecast).split('\n')[0]
    }
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "weather": current_weather}
    )

@app.get("/weather", response_class=HTMLResponse)
async def weather_page(request: Request):
    forecast = get_weather_forecast()
    advice = analyze_forecast_for_plants(forecast)
    
    # Split advice into sections for better display
    advice_sections = [section for section in advice.split('\n\n') if section.strip()]
    
    return templates.TemplateResponse(
        "weather.html",
        {
            "request": request,
            "forecast": forecast,
            "plant_care": advice_sections
        }
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Chat endpoint accessed with message: {request.message}")
    try:
        response = gardenbot_response(request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "GardenBot server is running"}

@app.get("/weather")
async def weather():
    """Weather endpoint for retrieving forecast and plant care advice"""
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
            plant_care_advice=advice
        )
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))