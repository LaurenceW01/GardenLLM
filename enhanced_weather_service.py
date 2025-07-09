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
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions (scraper first, API fallback)
        
        Returns:
            Optional[Dict[str, Any]]: Current weather data or None if error
        """
        try:
            # Try scraper first
            if self.scraper.is_available():
                logger.info("Using Click2Houston scraper for current weather")
                weather_data = self.scraper.get_current_weather()
                if weather_data:
                    self.last_service_used = "scraper"
                    return weather_data
            
            # Fallback to API if available
            if self.fallback_service:
                logger.info("Falling back to OpenWeather API for current weather")
                weather_data = self.fallback_service.get_current_weather()
                if weather_data:
                    self.last_service_used = "api"
                    return weather_data
            
            logger.error("Both scraper and API failed to get current weather")
            return None
            
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None
    
    def get_weather_forecast(self, days: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get daily forecast (scraper first, API fallback)
        
        Args:
            days (int): Number of days to forecast
            
        Returns:
            Optional[List[Dict[str, Any]]]: Daily forecast data or None if error
        """
        try:
            # Try scraper first
            if self.scraper.is_available():
                logger.info("Using Click2Houston scraper for daily forecast")
                forecast_data = self.scraper.get_daily_forecast(days)
                if forecast_data:
                    self.last_service_used = "scraper"
                    return forecast_data
            
            # Fallback to API if available
            if self.fallback_service:
                logger.info("Falling back to OpenWeather API for daily forecast")
                forecast_data = self.fallback_service.get_weather_forecast(days)
                if forecast_data:
                    self.last_service_used = "api"
                    return forecast_data
            
            logger.error("Both scraper and API failed to get daily forecast")
            return None
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    def get_hourly_rain_forecast(self, hours: int = 12) -> Optional[List[Dict[str, Any]]]:
        """
        Get hourly rain forecast (scraper first, API fallback)
        
        Args:
            hours (int): Number of hours to forecast
            
        Returns:
            Optional[List[Dict[str, Any]]]: Hourly forecast data or None if error
        """
        try:
            # Try scraper first
            if self.scraper.is_available():
                logger.info("Using Click2Houston scraper for hourly forecast")
                hourly_data = self.scraper.get_hourly_forecast(hours)
                if hourly_data:
                    self.last_service_used = "scraper"
                    return hourly_data
            
            # Fallback to API if available
            if self.fallback_service:
                logger.info("Falling back to OpenWeather API for hourly forecast")
                hourly_data = self.fallback_service.get_hourly_rain_forecast(hours)
                if hourly_data:
                    self.last_service_used = "api"
                    return hourly_data
            
            logger.error("Both scraper and API failed to get hourly forecast")
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
You are a gardening expert providing care recommendations for plants in Houston, Texas. 
Use the following weather and climate information to provide specific, actionable advice.

Climate Context:
{climate_context}

Current Weather Conditions:
- Temperature: {weather_data.get('temperature', 'Unknown')}°F
- Feels Like: {weather_data.get('feels_like', 'Unknown')}°F
- Humidity: {weather_data.get('humidity', 'Unknown')}%
- Wind Speed: {weather_data.get('wind_speed', 'Unknown')} mph
- Weather Description: {weather_data.get('description', 'Unknown')}
- Pressure: {weather_data.get('pressure', 'Unknown')} hPa
- Visibility: {weather_data.get('visibility', 'Unknown')} km

Data Source: {self.last_service_used or 'Unknown'}

Please provide:
1. General plant care recommendations based on current conditions
2. Specific advice for watering, fertilizing, and protection
3. Any weather-related precautions gardeners should take
4. Recommendations for indoor vs outdoor plants

Keep the response concise but comprehensive, focusing on practical advice that Houston gardeners can implement immediately.
"""
            
            # Get AI response
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable gardening expert specializing in Houston, Texas climate and growing conditions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "Unable to generate plant care recommendations"
            
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
            current_weather = self.get_current_weather()
            forecast = self.get_weather_forecast(3)  # Next 3 days
            hourly_rain = self.get_hourly_rain_forecast(12)  # Next 12 hours
            
            if not current_weather:
                return "Unable to retrieve weather information at this time."
            
            # Build summary
            summary_parts = []
            
            # Current conditions
            summary_parts.append(f"**Current Conditions:**")
            summary_parts.append(f"Temperature: {current_weather.get('temperature', 'Unknown')}°F")
            summary_parts.append(f"Feels Like: {current_weather.get('feels_like', 'Unknown')}°F")
            summary_parts.append(f"Humidity: {current_weather.get('humidity', 'Unknown')}%")
            summary_parts.append(f"Wind: {current_weather.get('wind_speed', 'Unknown')} mph")
            summary_parts.append(f"Conditions: {current_weather.get('description', 'Unknown')}")
            summary_parts.append(f"Data Source: {self.last_service_used or 'Unknown'}")
            
            # Hourly forecast
            if hourly_rain:
                summary_parts.append(f"\n**Next 12 Hours:**")
                for hour in hourly_rain[:6]:  # Show first 6 hours
                    summary_parts.append(f"{hour['time']}: {hour['temperature']}°F, {hour['rain_probability']}% rain chance")
            
            # Daily forecast
            if forecast:
                summary_parts.append(f"\n**3-Day Forecast:**")
                for day in forecast:
                    date_str = day['date'].strftime('%a, %b %d')
                    summary_parts.append(f"{date_str}: High {day['temp_max']}°F, Low {day['temp_min']}°F, {day['rain_probability']}% rain chance")
            
            return "\n".join(summary_parts)
            
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