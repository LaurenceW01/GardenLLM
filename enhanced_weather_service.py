"""
Enhanced Weather Service for GardenLLM.
Uses BaronWeatherVelocityAPI as the sole source for weather data.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from baron_weather_velocity_api import BaronWeatherVelocityAPI
from climate_config import get_climate_context, get_default_location, get_hardiness_zone
from config import BARON_API_KEY, BARON_API_SECRET
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedWeatherService:
    """Enhanced weather service using BaronWeatherVelocityAPI only"""
    
    def __init__(self, access_key: Optional[str] = None, access_key_secret: Optional[str] = None, latitude: float = 29.7604, longitude: float = -95.3698):
        """
        Initialize the enhanced weather service
        Args:
            access_key (str): Baron Weather API key
            access_key_secret (str): Baron Weather API secret
            latitude (float): Latitude coordinate (default: Houston, TX)
            longitude (float): Longitude coordinate (default: Houston, TX)
        """
        self.latitude = latitude  # Store latitude for future use
        self.longitude = longitude  # Store longitude for future use
        # Initialize BaronWeatherVelocityAPI client
        self.weather_api = BaronWeatherVelocityAPI(
            access_key=access_key or BARON_API_KEY,
            access_key_secret=access_key_secret or BARON_API_SECRET
        )
        # Use climate_config to get default location info
        self.default_location = get_default_location()  # Default location for display
        self.hardiness_zone = get_hardiness_zone()  # Hardiness zone for display
        # Cache for consolidated weather data to reduce requests
        self._weather_cache = {}  # Internal cache for weather data
        self._cache_timeout = 15 * 60  # 15 minutes
        self._last_cache_update = 0  # Timestamp of last cache update
    
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
        Update the weather cache with fresh data from BaronWeatherVelocityAPI
        Returns:
            bool: True if cache was updated successfully, False otherwise
        """
        try:
            # Get all weather data in one go to minimize requests
            current_weather = self.weather_api.get_current_weather()  # Get current weather
            hourly_forecast = self.weather_api.get_hourly_forecast(hours=48)  # Get 48-hour forecast
            # No daily forecast endpoint, so generate from hourly if needed
            daily_forecast = None  # Placeholder for future expansion
            if current_weather and hourly_forecast:
                self._weather_cache = {
                    'current_weather': current_weather,
                    'hourly_forecast': hourly_forecast,
                    'daily_forecast': daily_forecast,
                    'timestamp': time.time()
                }
                self._last_cache_update = time.time()
                logger.info(f"Got {len(hourly_forecast) if hourly_forecast else 0} hours of hourly forecast from BaronWeatherVelocityAPI")
                return True
            else:
                logger.warning("Baron Weather API returned no data - weather service unavailable")
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
    
    def get_hourly_forecast(self, hours: int = 48) -> Optional[List[Dict[str, Any]]]:
        """
        Get hourly forecast (uses cached data when possible)
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
            logger.error(f"Error getting hourly forecast: {e}")
            return None
    
    def get_weather_forecast(self, days: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get daily forecast (currently not implemented, returns None)
        Args:
            days (int): Number of days to forecast
        Returns:
            Optional[List[Dict[str, Any]]]: Daily forecast data or None
        """
        # No daily forecast endpoint in BaronWeatherVelocityAPI; could be generated from hourly in future
        return None

# Global instance for use in app
baron_weather_service = EnhancedWeatherService()

def get_current_weather() -> Optional[Dict[str, Any]]:
    """Get current weather using enhanced service"""
    return baron_weather_service.get_current_weather()

def get_hourly_forecast(hours: int = 48) -> Optional[List[Dict[str, Any]]]:
    """Get hourly forecast using enhanced service"""
    return baron_weather_service.get_hourly_forecast(hours=hours)

def get_weather_forecast(days: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Get daily forecast using enhanced service (currently returns None)"""
    return baron_weather_service.get_weather_forecast(days=days) 