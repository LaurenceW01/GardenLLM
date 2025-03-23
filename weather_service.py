import logging
import json
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional, List
import httpx
import os
from dotenv import load_dotenv
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OpenWeather API configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
HOUSTON_LAT = 29.7604
HOUSTON_LON = -95.3698

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

    def get_weather_forecast(self) -> List[Dict]:
        """Get weather forecast for specified location"""
        try:
            # OpenWeather API endpoint for 5-day forecast
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=imperial"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Process forecast data
            forecast = []
            current_date = None
            daily_data = {}
            
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                date_str = dt.strftime('%Y-%m-%d')
                
                if current_date != date_str:
                    if current_date is not None:
                        forecast.append(daily_data)
                    current_date = date_str
                    daily_data = {
                        'date': date_str,
                        'temp_min': float('inf'),
                        'temp_max': float('-inf'),
                        'description': set(),
                        'rain': 0.0,
                        'humidity': 0,
                        'wind_speed': 0,
                        'readings': 0
                    }
                
                # Update daily data
                daily_data['temp_min'] = min(daily_data['temp_min'], item['main']['temp_min'])
                daily_data['temp_max'] = max(daily_data['temp_max'], item['main']['temp_max'])
                daily_data['description'].add(item['weather'][0]['description'])
                daily_data['rain'] += item.get('rain', {}).get('3h', 0) / 25.4  # Convert mm to inches
                daily_data['humidity'] += item['main']['humidity']
                daily_data['wind_speed'] += item['wind']['speed']
                daily_data['readings'] += 1
            
            # Add last day
            if daily_data:
                forecast.append(daily_data)
            
            # Calculate averages and format descriptions
            for day in forecast:
                day['humidity'] = round(day['humidity'] / day['readings'])
                day['wind_speed'] = round(day['wind_speed'] / day['readings'], 1)
                day['description'] = ', '.join(sorted(day['description']))
                day['rain'] = round(day['rain'], 2)
                day['temp_min'] = round(day['temp_min'])
                day['temp_max'] = round(day['temp_max'])
                del day['readings']
            
            return forecast[:5]  # Return 5-day forecast
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return []

    def analyze_forecast_for_plants(self, forecast: List[Dict]) -> str:
        """Analyze weather forecast and provide plant care recommendations"""
        try:
            if not forecast:
                return "Unable to analyze forecast - no data available"
            
            advice = []
            
            # Check temperature extremes
            max_temp = max(day['temp_max'] for day in forecast)
            min_temp = min(day['temp_min'] for day in forecast)
            
            if max_temp > 90:
                advice.append("🌡️ High Temperature Alert:\n"
                            "• Water plants deeply in early morning\n"
                            "• Consider adding mulch to retain moisture\n"
                            "• Provide shade for sensitive plants\n"
                            "• Monitor for signs of heat stress")
            
            if min_temp < 40:
                advice.append("❄️ Cold Temperature Alert:\n"
                            "• Protect sensitive plants from frost\n"
                            "• Move potted plants indoors or to sheltered areas\n"
                            "• Water plants before freezing temperatures arrive\n"
                            "• Use frost cloth or row covers if needed")
            
            # Check for rain
            total_rain = sum(day['rain'] for day in forecast)
            if total_rain < 0.5:
                advice.append("💧 Low Rainfall Alert:\n"
                            "• Increase watering frequency\n"
                            "• Focus on deep watering to encourage root growth\n"
                            "• Check soil moisture regularly\n"
                            "• Consider using drip irrigation")
            elif total_rain > 2:
                advice.append("🌧️ Heavy Rain Alert:\n"
                            "• Check drainage in garden beds\n"
                            "• Hold off on additional watering\n"
                            "• Monitor for fungal diseases\n"
                            "• Avoid walking on wet soil")
            
            # Check wind conditions
            max_wind = max(day['wind_speed'] for day in forecast)
            if max_wind > 15:
                advice.append("💨 High Wind Alert:\n"
                            "• Stake tall plants and young trees\n"
                            "• Move potted plants to sheltered areas\n"
                            "• Delay applying fertilizers or pesticides\n"
                            "• Check plant supports and ties")
            
            # Add general recommendations based on conditions
            conditions = set()
            for day in forecast:
                conditions.update(day['description'].lower().split(', '))
            
            if 'clear' in conditions or 'sunny' in conditions:
                advice.append("☀️ Sunny Conditions:\n"
                            "• Monitor water needs more frequently\n"
                            "• Provide shade for sensitive plants\n"
                            "• Consider using mulch to retain moisture")
            
            if 'rain' in conditions or 'shower' in conditions:
                advice.append("🌧️ Rainy Conditions:\n"
                            "• Check plants for disease symptoms\n"
                            "• Ensure good air circulation\n"
                            "• Hold off on fertilizing until drier weather")
            
            return "\n\n".join(advice)
            
        except Exception as e:
            logger.error(f"Error analyzing forecast: {e}")
            return "Error analyzing weather forecast"

    def handle_weather_query(self, message: str) -> str:
        """Handle weather-related queries and return formatted response"""
        try:
            logger.info("Getting weather forecast...")
            forecast = self.get_weather_forecast()
            if not forecast:
                return "I'm sorry, I couldn't retrieve the weather forecast at this time."

            advice = self.analyze_forecast_for_plants(forecast)
            
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
            return "I'm sorry, I encountered an error while processing the weather information."

# Create a global instance for Houston
weather_service = WeatherService(
    api_key=os.getenv('OPENWEATHER_API_KEY'),
    lat=29.7604,  # Houston latitude
    lon=-95.3698  # Houston longitude
)

# Export functions that use the global instance
def get_weather_forecast() -> List[Dict]:
    """Get weather forecast for Houston area"""
    return weather_service.get_weather_forecast()

def analyze_forecast_for_plants(forecast: List[Dict]) -> str:
    """Analyze weather forecast and provide plant care recommendations"""
    return weather_service.analyze_forecast_for_plants(forecast)

def handle_weather_query(message: str) -> str:
    """Handle weather-related queries and return formatted response"""
    return weather_service.handle_weather_query(message) 