from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from test_openai import gardenbot_response, get_weather_forecast, analyze_forecast_for_plants
from plant_vision import analyze_plant_image, validate_image, save_image
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

class ImageAnalysisRequest(BaseModel):
    message: Optional[str] = None

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

@app.get("/weather/page", response_class=HTMLResponse)
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
    message: Optional[str] = None
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
            
        # Analyze image
        analysis = analyze_plant_image(image_data, message)
        
        return {"response": analysis}
        
    except Exception as e:
        logger.error(f"Error in analyze_plant endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))