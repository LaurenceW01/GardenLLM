"""
Weather service for GardenLLM.
Provides weather data and plant care recommendations based on weather conditions.
"""

import logging
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import openai_client
from climate_config import get_climate_context, get_default_location, get_hardiness_zone

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    """Weather service for getting weather data and plant care recommendations"""
    
    def __init__(self, api_key: str, latitude: float = 29.7604, longitude: float = -95.3698):
        """
        Initialize the weather service with location coordinates
        
        Args:
            api_key (str): OpenWeather API key
            latitude (float): Latitude coordinate (default: Houston, TX)
            longitude (float): Longitude coordinate (default: Houston, TX)
        """
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        # Use climate_config to get default location info
        self.default_location = get_default_location()
        self.hardiness_zone = get_hardiness_zone()
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions
        
        Returns:
            Optional[Dict[str, Any]]: Current weather data or None if error
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'visibility': data.get('visibility', 0),
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']),
                'sunset': datetime.fromtimestamp(data['sys']['sunset'])
            }
            
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None
    
    def get_weather_forecast(self, days: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get weather forecast for specified location
        
        Args:
            days (int): Number of days to forecast (default: 5)
            
        Returns:
            Optional[List[Dict[str, Any]]]: Forecast data or None if error
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Group forecast data by day
            daily_data = {}
            for item in data['list']:
                date = datetime.fromtimestamp(item['dt']).date()
                if date not in daily_data:
                    daily_data[date] = {
                        'temp_min': float('inf'),
                        'temp_max': float('-inf'),
                        'humidity': [],
                        'description': set(),
                        'wind_speed': [],
                        'pressure': []
                    }
                
                daily_data[date]['temp_min'] = min(daily_data[date]['temp_min'], item['main']['temp_min'])
                daily_data[date]['temp_max'] = max(daily_data[date]['temp_max'], item['main']['temp_max'])
                daily_data[date]['humidity'].append(item['main']['humidity'])
                daily_data[date]['description'].add(item['weather'][0]['description'])
                daily_data[date]['wind_speed'].append(item['wind']['speed'])
                daily_data[date]['pressure'].append(item['main']['pressure'])
            
            # Calculate averages and format descriptions
            forecast = []
            for date, day_data in sorted(daily_data.items()):
                day = {
                    'date': date,
                    'temp_min': round(day_data['temp_min'], 1),
                    'temp_max': round(day_data['temp_max'], 1),
                    'humidity': round(sum(day_data['humidity']) / len(day_data['humidity'])),
                    'description': ', '.join(sorted(day_data['description'])),
                    'wind_speed': round(sum(day_data['wind_speed']) / len(day_data['wind_speed']), 1),
                    'pressure': round(sum(day_data['pressure']) / len(day_data['pressure']))
                }
                forecast.append(day)
            
            return forecast[:days]
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    def get_plant_care_recommendations(self, weather_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Get plant care recommendations based on current weather
        
        Args:
            weather_data (Optional[Dict[str, Any]]): Weather data to use. If None, fetches current weather.
            
        Returns:
            str: Plant care recommendations
        """
        try:
            if weather_data is None:
                weather_data = self.get_current_weather()
            
            if not weather_data:
                return "Unable to get weather data for plant care recommendations."
            
            # Get climate context for the AI prompt
            climate_context = get_climate_context()
            
            # Build the prompt with weather and climate information
            prompt = f"""
            Based on the current weather conditions and {self.default_location} climate, provide plant care recommendations.
            
            Climate Context:
            {climate_context}
            
            Current Weather:
            - Temperature: {weather_data['temperature']}°F
            - Feels like: {weather_data['feels_like']}°F
            - Humidity: {weather_data['humidity']}%
            - Conditions: {weather_data['description']}
            - Wind Speed: {weather_data['wind_speed']} mph
            
            Please provide specific, actionable plant care advice considering:
            1. Watering needs based on temperature and humidity
            2. Protection measures if needed (frost, heat, wind)
            3. General maintenance tasks appropriate for these conditions
            4. Any special considerations for {self.default_location} climate
            
            Keep the advice practical and specific to the current conditions.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable gardening expert specializing in weather-aware plant care."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            return response.choices[0].message.content or "Unable to generate plant care recommendations."
            
        except Exception as e:
            logger.error(f"Error getting plant care recommendations: {e}")
            return "Unable to generate plant care recommendations due to an error."
    
    def get_weather_summary(self) -> str:
        """
        Get a comprehensive weather summary with plant care advice
        
        Returns:
            str: Weather summary and plant care recommendations
        """
        try:
            current_weather = self.get_current_weather()
            forecast = self.get_weather_forecast(3)  # 3-day forecast
            
            if not current_weather:
                return "Unable to retrieve weather data."
            
            # Build weather summary
            summary_parts = [
                f"Weather Summary for {self.default_location}",
                f"Current Conditions: {current_weather['temperature']}°F, {current_weather['description']}",
                f"Humidity: {current_weather['humidity']}%",
                f"Wind: {current_weather['wind_speed']} mph"
            ]
            
            if forecast:
                summary_parts.append("\n3-Day Forecast:")
                for day in forecast:
                    summary_parts.append(f"- {day['date'].strftime('%A, %B %d')}: {day['temp_min']}°F - {day['temp_max']}°F, {day['description']}")
            
            # Get plant care recommendations
            care_recommendations = self.get_plant_care_recommendations(current_weather)
            
            summary_parts.append(f"\nPlant Care Recommendations:\n{care_recommendations}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error getting weather summary: {e}")
            return "Unable to generate weather summary due to an error."
    
    def analyze_weather_conditions(self) -> Dict[str, Any]:
        """
        Analyze current weather conditions for gardening impact
        
        Returns:
            Dict[str, Any]: Analysis of weather conditions
        """
        try:
            weather_data = self.get_current_weather()
            if not weather_data:
                return {"error": "Unable to retrieve weather data"}
            
            # Get climate context for analysis
            climate_context = get_climate_context()
            
            analysis = {
                'location': self.default_location,
                'hardiness_zone': self.hardiness_zone,
                'current_conditions': weather_data,
                'gardening_impact': {}
            }
            
            # Analyze temperature impact
            temp = weather_data['temperature']
            if temp < 32:
                analysis['gardening_impact']['temperature'] = 'Frost risk - protect sensitive plants'
            elif temp < 50:
                analysis['gardening_impact']['temperature'] = 'Cold conditions - limit outdoor planting'
            elif temp > 95:
                analysis['gardening_impact']['temperature'] = 'High heat - provide shade and extra water'
            elif temp > 85:
                analysis['gardening_impact']['temperature'] = 'Warm conditions - monitor water needs'
            else:
                analysis['gardening_impact']['temperature'] = 'Good growing conditions'
            
            # Analyze humidity impact
            humidity = weather_data['humidity']
            if humidity > 80:
                analysis['gardening_impact']['humidity'] = 'High humidity - watch for fungal diseases'
            elif humidity < 30:
                analysis['gardening_impact']['humidity'] = 'Low humidity - increase watering frequency'
            else:
                analysis['gardening_impact']['humidity'] = 'Moderate humidity - normal care'
            
            # Analyze wind impact
            wind_speed = weather_data['wind_speed']
            if wind_speed > 20:
                analysis['gardening_impact']['wind'] = 'High winds - protect plants and secure containers'
            elif wind_speed > 10:
                analysis['gardening_impact']['wind'] = 'Moderate winds - monitor for damage'
            else:
                analysis['gardening_impact']['wind'] = 'Light winds - normal conditions'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing weather conditions: {e}")
            return {"error": f"Unable to analyze weather conditions: {str(e)}"}

# Create a global instance for Houston
weather_service = WeatherService(
    api_key=os.getenv('OPENWEATHER_API_KEY') or '',
    latitude=29.7604,  # Houston latitude
    longitude=-95.3698  # Houston longitude
)

# Export functions that use the global instance
def get_weather_forecast() -> List[Dict[str, Any]]:
    """Get weather forecast for Houston area"""
    forecast = weather_service.get_weather_forecast()
    return forecast if forecast else []

def get_weather_summary() -> str:
    """Get comprehensive weather summary with plant care advice"""
    return weather_service.get_weather_summary()

def get_plant_care_recommendations() -> str:
    """Get plant care recommendations based on current weather"""
    return weather_service.get_plant_care_recommendations()

def analyze_weather_conditions() -> Dict[str, Any]:
    """Analyze current weather conditions for gardening impact"""
    return weather_service.analyze_weather_conditions() 