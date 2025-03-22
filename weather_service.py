import logging
import json
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for retrieving weather data and making gardening recommendations"""
    
    def __init__(self, api_key: str, lat: float, lon: float):
        """Initialize the weather service with location coordinates"""
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.est = pytz.timezone('US/Eastern')
    
    async def get_current_weather(self) -> Optional[Dict]:
        """Get current weather conditions"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": self.lat,
                        "lon": self.lon,
                        "appid": self.api_key,
                        "units": "imperial"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None
    
    async def get_forecast(self, days: int = 5) -> Optional[Dict]:
        """Get weather forecast for specified number of days"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": self.lat,
                        "lon": self.lon,
                        "appid": self.api_key,
                        "units": "imperial"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting forecast: {e}")
            return None
    
    def get_frost_risk(self, temp: float) -> str:
        """Determine frost risk based on temperature"""
        if temp <= 28:
            return "severe"
        elif temp <= 32:
            return "moderate"
        elif temp <= 36:
            return "light"
        return "none"
    
    async def get_gardening_recommendations(self) -> Dict:
        """Get gardening recommendations based on weather conditions"""
        try:
            current = await self.get_current_weather()
            forecast = await self.get_forecast()
            
            if not current or not forecast:
                return {"error": "Unable to fetch weather data"}
            
            current_temp = current['main']['temp']
            current_conditions = current['weather'][0]['main'].lower()
            
            # Get next 24 hours of forecast data
            now = datetime.now(self.est)
            tomorrow = now + timedelta(days=1)
            next_24h = [
                period for period in forecast['list']
                if now <= datetime.fromtimestamp(period['dt'], self.est) <= tomorrow
            ]
            
            # Check for frost risk
            min_temp = min(period['main']['temp'] for period in next_24h)
            frost_risk = self.get_frost_risk(min_temp)
            
            # Check for precipitation
            will_rain = any(
                'rain' in period['weather'][0]['main'].lower()
                for period in next_24h
            )
            
            recommendations = {
                "current_conditions": {
                    "temperature": current_temp,
                    "conditions": current_conditions,
                    "frost_risk": self.get_frost_risk(current_temp)
                },
                "forecast": {
                    "min_temp": min_temp,
                    "frost_risk": frost_risk,
                    "will_rain": will_rain
                },
                "recommendations": []
            }
            
            # Generate recommendations based on conditions
            if frost_risk != "none":
                recommendations["recommendations"].append(
                    f"Frost risk is {frost_risk}. Protect sensitive plants."
                )
            
            if current_conditions in ['rain', 'drizzle']:
                recommendations["recommendations"].append(
                    "Currently raining. Hold off on additional watering."
                )
            elif will_rain:
                recommendations["recommendations"].append(
                    "Rain expected in next 24 hours. Consider delaying watering."
                )
            
            if current_temp > 85:
                recommendations["recommendations"].append(
                    "High temperature. Ensure plants are well-watered and consider providing shade."
                )
            
            if not recommendations["recommendations"]:
                recommendations["recommendations"].append(
                    "Weather conditions are favorable for general gardening activities."
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"error": f"Error generating recommendations: {str(e)}"}
    
    def format_recommendations(self, recommendations: Dict) -> str:
        """Format weather recommendations into a readable message"""
        try:
            if "error" in recommendations:
                return f"Sorry, I couldn't get weather recommendations: {recommendations['error']}"
            
            current = recommendations["current_conditions"]
            forecast = recommendations["forecast"]
            
            message_parts = [
                f"Current temperature is {current['temperature']}°F with {current['conditions']} conditions.",
                f"Forecast low temperature: {forecast['min_temp']}°F",
                f"Frost risk: {forecast['frost_risk'].title()}",
                f"Rain expected: {'Yes' if forecast['will_rain'] else 'No'}",
                "\nRecommendations:",
                *recommendations["recommendations"]
            ]
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting recommendations: {e}")
            return "Sorry, I couldn't format the weather recommendations." 