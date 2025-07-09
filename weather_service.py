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
        Get daily forecast with max pop and associated weather description for each day
        Returns:
            List of dicts: [{date, max_rain_probability, description, ...}]
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
            daily_data = {}
            for item in data['list']:
                date = datetime.fromtimestamp(item['dt']).date()
                pop = item.get('pop', 0)
                desc = item['weather'][0]['description'].capitalize()
                if date not in daily_data:
                    daily_data[date] = {
                        'temp_min': float('inf'),
                        'temp_max': float('-inf'),
                        'max_pop': 0,
                        'max_pop_desc': '',
                        'humidity': [],
                        'wind_speed': [],
                        'pressure': []
                    }
                daily_data[date]['temp_min'] = min(daily_data[date]['temp_min'], item['main']['temp_min'])
                daily_data[date]['temp_max'] = max(daily_data[date]['temp_max'], item['main']['temp_max'])
                daily_data[date]['humidity'].append(item['main']['humidity'])
                daily_data[date]['wind_speed'].append(item['wind']['speed'])
                daily_data[date]['pressure'].append(item['main']['pressure'])
                # Track max pop and its description
                if pop > daily_data[date]['max_pop']:
                    daily_data[date]['max_pop'] = pop
                    daily_data[date]['max_pop_desc'] = desc
            forecast = []
            for date, day_data in sorted(daily_data.items()):
                forecast.append({
                    'date': date,
                    'temp_min': round(day_data['temp_min'], 1),
                    'temp_max': round(day_data['temp_max'], 1),
                    'humidity': round(sum(day_data['humidity']) / len(day_data['humidity'])),
                    'wind_speed': round(sum(day_data['wind_speed']) / len(day_data['wind_speed']), 1),
                    'pressure': round(sum(day_data['pressure']) / len(day_data['pressure'])),
                    'rain_probability': round(day_data['max_pop'] * 100, 1),
                    'rain_description': day_data['max_pop_desc']
                })
            return forecast[:days]
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    def get_hourly_rain_forecast(self, hours: int = 12) -> Optional[list]:
        """
        Get hourly rain probability forecast from current time forward (default: next 12 blocks)
        Returns:
            List of dicts: [{time, rain_probability, description}]
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
            
            # Use UTC time for comparison since OpenWeather API returns UTC timestamps
            from datetime import timezone
            import pytz
            
            now_utc = datetime.now(timezone.utc).timestamp()
            houston_tz = pytz.timezone('America/Chicago')
            
            # Only include blocks from now forward
            hourly_data = []
            for item in data['list']:
                if item['dt'] >= now_utc:
                    # Convert UTC timestamp to Houston time for display
                    utc_time = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                    houston_time = utc_time.astimezone(houston_tz)
                    hourly_data.append({
                        'time': houston_time.strftime('%a %I %p'),
                        'rain_probability': round(item.get('pop', 0) * 100, 1),
                        'description': item['weather'][0]['description'].capitalize(),
                        'wind_speed': round(item.get('wind', {}).get('speed', 0), 1),
                        'temperature': round(item.get('main', {}).get('temp', 0), 1)
                    })
            return hourly_data[:hours]
        except Exception as e:
            logger.error(f"Error getting hourly rain forecast: {e}")
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
            Based on the current weather conditions and {self.default_location} climate, provide clear, actionable plant care recommendations.
            
            Current Weather:
            - Temperature: {weather_data['temperature']}°F
            - Feels like: {weather_data['feels_like']}°F
            - Humidity: {weather_data['humidity']}%
            - Conditions: {weather_data['description']}
            - Wind Speed: {weather_data['wind_speed']} mph
            
            Please provide specific, actionable plant care advice in this format:
            
            <h4 class="text-lg font-semibold text-green-800 mb-2">Watering Recommendations:</h4>
            <ul class="list-disc list-inside space-y-1 mb-4">
            [Specific watering advice based on current conditions]
            </ul>
            
            <h4 class="text-lg font-semibold text-green-800 mb-2">Protection Measures:</h4>
            <ul class="list-disc list-inside space-y-1 mb-4">
            [Any protection needed for current weather]
            </ul>
            
            <h4 class="text-lg font-semibold text-green-800 mb-2">Maintenance Tasks:</h4>
            <ul class="list-disc list-inside space-y-1 mb-4">
            [General maintenance appropriate for these conditions]
            </ul>
            
            <h4 class="text-lg font-semibold text-green-800 mb-2">Special Considerations:</h4>
            <ul class="list-disc list-inside space-y-1 mb-4">
            [Any specific advice for {self.default_location} climate]
            </ul>
            
            Keep the advice practical, specific, and easy to follow. Use bullet points and clear language.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable gardening expert specializing in weather-aware plant care. Always format your responses with proper HTML tags including <h4>, <ul>, and <li> tags for structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content or "Unable to generate plant care recommendations."
            
            # Post-process to ensure proper HTML formatting
            import re
            
            # If the AI didn't use proper HTML, convert plain text to HTML
            if not re.search(r'<h4>|<ul>|<li>', content):
                # Split by sections and convert to HTML
                sections = content.split('\n\n')
                html_parts = []
                
                for section in sections:
                    if section.strip():
                        lines = section.strip().split('\n')
                        if lines:
                            # First line is the header
                            header = lines[0].replace(':', '').strip()
                            if header and not header.startswith('<'):
                                html_parts.append(f'<h4 class="text-lg font-semibold text-green-800 mb-2">{header}</h4>')
                                html_parts.append('<ul class="list-disc list-inside space-y-1 mb-4">')
                                
                                # Remaining lines are bullet points
                                for line in lines[1:]:
                                    line = line.strip()
                                    if line and not line.startswith('<'):
                                        # Remove common bullet point indicators
                                        line = re.sub(r'^[-•*]\s*', '', line)
                                        html_parts.append(f'<li class="text-gray-700">{line}</li>')
                                
                                html_parts.append('</ul>')
                
                content = '\n'.join(html_parts)
            else:
                # If AI provided HTML, ensure it has proper CSS classes
                # Add classes to h4 tags if missing
                content = re.sub(r'<h4(?![^>]*class=)', r'<h4 class="text-lg font-semibold text-green-800 mb-2"', content)
                # Add classes to ul tags if missing
                content = re.sub(r'<ul(?![^>]*class=)', r'<ul class="list-disc list-inside space-y-1 mb-4"', content)
                # Add classes to li tags if missing
                content = re.sub(r'<li(?![^>]*class=)', r'<li class="text-gray-700"', content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting plant care recommendations: {e}")
            return "Unable to generate plant care recommendations due to an error."
    
    def get_weather_summary(self) -> str:
        """
        Get a comprehensive weather summary (without plant care advice)
        
        Returns:
            str: Weather summary only
        """
        try:
            current_weather = self.get_current_weather()
            forecast = self.get_weather_forecast(3)  # 3-day forecast
            hourly_rain = self.get_hourly_rain_forecast()  # Hourly rain data
            
            if not current_weather:
                return "Unable to retrieve weather data."
            
            # Build weather summary with HTML formatting
            summary_parts = [
                f"<h3 class='text-lg font-semibold text-blue-900 mb-3'>Current Weather for {self.default_location}</h3>",
                f"<div class='grid grid-cols-1 md:grid-cols-2 gap-4 mb-4'>",
                f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Temperature:</strong> {current_weather['temperature']}°F (feels like {current_weather['feels_like']}°F)</div>",
                f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Conditions:</strong> {current_weather['description'].title()}</div>",
                f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Humidity:</strong> {current_weather['humidity']}%</div>",
                f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Wind Speed:</strong> {current_weather['wind_speed']} mph</div>",
                f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Pressure:</strong> {current_weather['pressure']} hPa</div>",
                f"</div>"
            ]
            
            # Add hourly rain forecast for current time forward
            if hourly_rain:
                summary_parts.append("<h4 class='text-md font-semibold text-blue-800 mb-3'>Upcoming Hourly Rain Forecast</h4>")
                summary_parts.append("<div class='grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-4'>")
                for hour in hourly_rain:
                    rain_color = "bg-red-100" if hour['rain_probability'] > 50 else "bg-yellow-100" if hour['rain_probability'] > 20 else "bg-green-100"
                    summary_parts.append(f"<div class='{rain_color} p-2 rounded text-center text-sm'>")
                    summary_parts.append(f"<div class='font-semibold'>{hour['time']}</div>")
                    summary_parts.append(f"<div class='text-blue-600'>{hour['rain_probability']}% ({hour['description']})</div>")
                    summary_parts.append("</div>")
                summary_parts.append("</div>")
            
            if forecast:
                summary_parts.append("<h4 class='text-md font-semibold text-blue-800 mb-3'>3-Day Rain Forecast</h4>")
                summary_parts.append("<div class='space-y-2'>")
                for day in forecast:
                    rain_color = "border-red-300" if day['rain_probability'] > 50 else "border-yellow-300" if day['rain_probability'] > 20 else "border-blue-300"
                    summary_parts.append(f"<div class='bg-blue-50 p-3 rounded border-l-4 {rain_color}'>")
                    summary_parts.append(f"<strong>{day['date'].strftime('%A, %B %d')}:</strong> {day['rain_probability']}% ({day['rain_description']})")
                    summary_parts.append(f"<br><span class='text-sm text-blue-600'>Temp: {day['temp_min']}°F - {day['temp_max']}°F | Wind: {day['wind_speed']} mph</span>")
                    summary_parts.append("</div>")
                summary_parts.append("</div>")
            
            return "".join(summary_parts)
            
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

def get_hourly_rain_forecast() -> List[Dict[str, Any]]:
    """Get hourly rain forecast for Houston area"""
    hourly_rain = weather_service.get_hourly_rain_forecast()
    return hourly_rain if hourly_rain else []

def get_weather_summary() -> str:
    """Get comprehensive weather summary with plant care advice"""
    return weather_service.get_weather_summary()

def get_plant_care_recommendations() -> str:
    """Get plant care recommendations based on current weather"""
    return weather_service.get_plant_care_recommendations()

def analyze_weather_conditions() -> Dict[str, Any]:
    """Analyze current weather conditions for gardening impact"""
    return weather_service.analyze_weather_conditions() 