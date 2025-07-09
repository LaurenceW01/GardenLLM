"""
Enhanced Weather Service for GardenLLM.
Uses Click2Houston scraper as primary source with OpenWeather API as fallback.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import openai_client
from climate_config import get_climate_context, get_default_location, get_hardiness_zone
from click2houston_scraper import Click2HoustonScraper
from weather_service import WeatherService
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedWeatherService:
    """Enhanced weather service with scraper and API fallback"""
    
    def __init__(self, api_key: Optional[str] = None, latitude: float = 29.7604, longitude: float = -95.3698):
        """
        Initialize the enhanced weather service
        
        Args:
            api_key (str): OpenWeather API key (optional, for fallback)
            latitude (float): Latitude coordinate (default: Houston, TX)
            longitude (float): Longitude coordinate (default: Houston, TX)
        """
        self.latitude = latitude
        self.longitude = longitude
        
        # Initialize scraper
        self.scraper = Click2HoustonScraper()
        
        # Initialize fallback API service
        self.fallback_service = None
        if api_key:
            self.fallback_service = WeatherService(api_key, latitude, longitude)
        
        # Use climate_config to get default location info
        self.default_location = get_default_location()
        self.hardiness_zone = get_hardiness_zone()
        
        # Track which service was used last
        self.last_service_used = None
        
        # Cache for consolidated weather data to reduce requests
        self._weather_cache = {}
        self._cache_timeout = 15 * 60  # 15 minutes
        self._last_cache_update = 0
    
    def _get_cached_weather_data(self) -> Optional[Dict[str, Any]]:
        """
        Get cached weather data if still valid
        
        Returns:
            Optional[Dict[str, Any]]: Cached weather data or None if expired
        """
        if (time.time() - self._last_cache_update) < self._cache_timeout:
            return self._weather_cache
        return None
    
    def _update_weather_cache(self) -> bool:
        """
        Update the weather cache with fresh data from scraper or API
        
        Returns:
            bool: True if cache was updated successfully, False otherwise
        """
        try:
            # Try scraper first
            if self.scraper.is_available():
                logger.info("Using Click2Houston scraper for weather data")
                
                # Get all weather data in one go to minimize requests
                current_weather = self.scraper.get_current_weather()
                daily_forecast = self.scraper.get_daily_forecast(5)
                
                # Get hourly forecast (48 hours to get all available)
                hourly_forecast = self.scraper.get_hourly_forecast(hours=48)
                
                if current_weather:
                    self._weather_cache = {
                        'current_weather': current_weather,
                        'daily_forecast': daily_forecast,
                        'hourly_forecast': hourly_forecast,
                        'timestamp': time.time()
                    }
                    self._last_cache_update = time.time()
                    self.last_service_used = "scraper"
                    logger.info(f"Got {len(hourly_forecast) if hourly_forecast else 0} hours of hourly forecast from scraper")
                    return True
            
            # Fallback to API if available
            if self.fallback_service:
                logger.info("Falling back to OpenWeather API for weather data")
                
                current_weather = self.fallback_service.get_current_weather()
                daily_forecast = self.fallback_service.get_weather_forecast(5)
                
                # Get hourly forecast (48 hours to get all available)
                hourly_forecast = self.fallback_service.get_hourly_rain_forecast(hours=48)
                
                if current_weather:
                    self._weather_cache = {
                        'current_weather': current_weather,
                        'daily_forecast': daily_forecast,
                        'hourly_forecast': hourly_forecast,
                        'timestamp': time.time()
                    }
                    self._last_cache_update = time.time()
                    self.last_service_used = "api"
                    logger.info(f"Got {len(hourly_forecast) if hourly_forecast else 0} hours of hourly forecast from API")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating weather cache: {e}")
            return False
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions (uses cached data when possible)
        
        Returns:
            Optional[Dict[str, Any]]: Current weather data or None if error
        """
        try:
            # Check cache first
            cached_data = self._get_cached_weather_data()
            if cached_data and 'current_weather' in cached_data:
                return cached_data['current_weather']
            
            # Update cache if needed
            if self._update_weather_cache():
                return self._weather_cache.get('current_weather')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None
    
    def get_weather_forecast(self, days: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get daily forecast (uses cached data when possible)
        
        Args:
            days (int): Number of days to forecast
            
        Returns:
            Optional[List[Dict[str, Any]]]: Daily forecast data or None if error
        """
        try:
            # Check cache first
            cached_data = self._get_cached_weather_data()
            if cached_data and 'daily_forecast' in cached_data:
                forecast = cached_data['daily_forecast']
                return forecast[:days] if forecast else None
            
            # Update cache if needed
            if self._update_weather_cache():
                forecast = self._weather_cache.get('daily_forecast')
                return forecast[:days] if forecast else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    def get_hourly_rain_forecast(self, hours: int = 12) -> Optional[List[Dict[str, Any]]]:
        """
        Get hourly rain forecast (uses cached data when possible)
        
        Args:
            hours (int): Number of hours to forecast
            
        Returns:
            Optional[List[Dict[str, Any]]]: Hourly forecast data or None if error
        """
        try:
            # Check cache first
            cached_data = self._get_cached_weather_data()
            if cached_data and 'hourly_forecast' in cached_data:
                forecast = cached_data['hourly_forecast']
                return forecast[:hours] if forecast else None
            
            # Update cache if needed
            if self._update_weather_cache():
                forecast = self._weather_cache.get('hourly_forecast')
                return forecast[:hours] if forecast else None
            
            return None
            
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
- Temperature: {weather_data.get('temperature', 'Unknown')}°F
- Feels like: {weather_data.get('feels_like', 'Unknown')}°F
- Humidity: {weather_data.get('humidity', 'Unknown')}%
- Conditions: {weather_data.get('description', 'Unknown')}
- Wind Speed: {weather_data.get('wind_speed', 'Unknown')} mph

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
            
            # Get AI response
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable gardening expert specializing in weather-aware plant care. Always format your responses with proper HTML tags including <h4>, <ul>, and <li> tags for structure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            if not content:
                return "Unable to generate plant care recommendations."
            
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
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting plant care recommendations: {e}")
            return f"Unable to generate plant care recommendations due to an error: {str(e)}"
    
    def get_weather_summary(self) -> str:
        """
        Get a comprehensive weather summary
        
        Returns:
            str: Weather summary text
        """
        try:
            # Use cached data to avoid multiple requests
            cached_data = self._get_cached_weather_data()
            if not cached_data:
                if not self._update_weather_cache():
                    return "Unable to retrieve weather information at this time."
                cached_data = self._weather_cache
            
            current_weather = cached_data.get('current_weather')
            forecast = cached_data.get('daily_forecast', [])[:3]  # Next 3 days
            
            if not current_weather:
                return "Unable to retrieve weather information at this time."
            
            # Build summary with proper HTML formatting
            summary_parts = []
            
            # Current conditions
            summary_parts.append(f"<h3 class='text-lg font-semibold text-blue-900 mb-3'>Current Weather for {self.default_location}</h3>")
            summary_parts.append(f"<div class='grid grid-cols-1 md:grid-cols-2 gap-4 mb-4'>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Temperature:</strong> {current_weather.get('temperature', 'Unknown')}°F (feels like {current_weather.get('feels_like', 'Unknown')}°F)</div>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Conditions:</strong> {current_weather.get('description', 'Unknown').title()}</div>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Humidity:</strong> {current_weather.get('humidity', 'Unknown')}%</div>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Wind Speed:</strong> {current_weather.get('wind_speed', 'Unknown')} mph</div>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Pressure:</strong> {current_weather.get('pressure', 'Unknown')} hPa</div>")
            summary_parts.append(f"<div class='bg-blue-100 p-3 rounded-lg'><strong>Data Source:</strong> {self.last_service_used or 'Unknown'}</div>")
            summary_parts.append(f"</div>")
            
            # Daily forecast only (hourly is shown separately in template)
            if forecast:
                summary_parts.append("<h4 class='text-md font-semibold text-blue-800 mb-3'>3-Day Forecast</h4>")
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
            return f"Unable to generate weather summary due to an error: {str(e)}"
    
    def analyze_weather_conditions(self) -> Dict[str, Any]:
        """
        Analyze current weather conditions for plant care
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            current_weather = self.get_current_weather()
            if not current_weather:
                return {"error": "Unable to get weather data"}
            
            temp = current_weather.get('temperature', 0)
            humidity = current_weather.get('humidity', 0)
            wind_speed = current_weather.get('wind_speed', 0)
            description = current_weather.get('description', '').lower()
            
            # Analyze conditions
            analysis = {
                "temperature_category": "normal",
                "humidity_category": "normal", 
                "wind_category": "normal",
                "overall_conditions": "good",
                "recommendations": []
            }
            
            # Temperature analysis
            if temp < 50:
                analysis["temperature_category"] = "cold"
                analysis["recommendations"].append("Protect sensitive plants from cold")
            elif temp > 90:
                analysis["temperature_category"] = "hot"
                analysis["recommendations"].append("Provide extra water and shade")
            
            # Humidity analysis
            if humidity < 40:
                analysis["humidity_category"] = "low"
                analysis["recommendations"].append("Consider misting or humidifier")
            elif humidity > 80:
                analysis["humidity_category"] = "high"
                analysis["recommendations"].append("Ensure good air circulation")
            
            # Wind analysis
            if wind_speed > 15:
                analysis["wind_category"] = "high"
                analysis["recommendations"].append("Secure potted plants and protect from wind damage")
            
            # Overall assessment
            if len(analysis["recommendations"]) > 2:
                analysis["overall_conditions"] = "challenging"
            elif len(analysis["recommendations"]) > 0:
                analysis["overall_conditions"] = "moderate"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing weather conditions: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

# Global instance for easy access
enhanced_weather_service: Optional[EnhancedWeatherService] = None

def initialize_enhanced_weather_service(api_key: Optional[str] = None):
    """Initialize the global enhanced weather service instance"""
    global enhanced_weather_service
    enhanced_weather_service = EnhancedWeatherService(api_key)

# Convenience functions that match the original weather service interface
def get_current_weather() -> Optional[Dict[str, Any]]:
    """Get current weather using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.get_current_weather()
    return None

def get_weather_forecast() -> Optional[List[Dict[str, Any]]]:
    """Get weather forecast using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.get_weather_forecast()
    return None

def get_hourly_rain_forecast() -> Optional[List[Dict[str, Any]]]:
    """Get hourly rain forecast using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.get_hourly_rain_forecast()
    return None

def get_weather_summary() -> str:
    """Get weather summary using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.get_weather_summary()
    return "Unable to get weather summary"

def get_plant_care_recommendations() -> str:
    """Get plant care recommendations using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.get_plant_care_recommendations()
    return "Unable to get plant care recommendations"

def analyze_weather_conditions() -> Dict[str, Any]:
    """Analyze weather conditions using enhanced service"""
    if enhanced_weather_service is None:
        initialize_enhanced_weather_service()
    if enhanced_weather_service is not None:
        return enhanced_weather_service.analyze_weather_conditions()
    return {"error": "Weather service not available"} 