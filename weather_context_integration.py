"""
Weather Context Integration Module

This module implements the weather context integration plan to provide
concise weather summaries for AI conversations, enabling weather-aware
gardening advice.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enhanced_weather_service import get_current_weather, get_hourly_forecast
from climate_config import get_default_location

# Set up logging
logger = logging.getLogger(__name__)

class WeatherContextProvider:
    """
    Provides concise weather context for AI conversations.
    
    This class implements the weather context integration plan by:
    1. Collecting current weather and forecast data
    2. Summarizing data into concise, relevant information
    3. Formatting context for injection into AI conversations
    """
    
    def __init__(self):
        """Initialize the weather context provider"""
        self.location = get_default_location()
        self._last_context_update = 0
        self._context_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timeout = 5 * 60  # 5 minutes cache
    
    def get_weather_context(self) -> List[Dict[str, Any]]:
        """
        Get weather context messages for AI conversations.
        
        Returns:
            List[Dict[str, Any]]: List of weather context messages to inject into conversation
        """
        try:
            # Check cache first
            if self._is_cache_valid() and self._context_cache is not None:
                logger.info("Using cached weather context")
                return self._context_cache
            
            # Get fresh weather data
            current_weather = get_current_weather()
            hourly_forecast = get_hourly_forecast(hours=24)
            
            # Generate context messages
            context_messages = []
            
            # Add current weather context
            if current_weather:
                current_context = self._format_current_weather(current_weather)
                context_messages.append({
                    "role": "system",
                    "content": current_context
                })
                logger.info(f"Added current weather context: {current_context}")
            
            # Add forecast context
            if hourly_forecast:
                forecast_context = self._format_forecast_summary(hourly_forecast)
                if forecast_context:
                    context_messages.append({
                        "role": "system", 
                        "content": forecast_context
                    })
                    logger.info(f"Added forecast context: {forecast_context}")
            
            # Add fallback if no weather data
            if not context_messages:
                fallback_context = f"Weather data is currently unavailable. Answer based on general {self.location} climate."
                context_messages.append({
                    "role": "system",
                    "content": fallback_context
                })
                logger.warning("No weather data available, using fallback context")
            
            # Update cache
            self._context_cache = context_messages
            self._last_context_update = datetime.now().timestamp()
            
            return context_messages
            
        except Exception as e:
            logger.error(f"Error getting weather context: {e}")
            # Return fallback context on error
            return [{
                "role": "system",
                "content": f"Weather data is currently unavailable. Answer based on general {self.location} climate."
            }]
    
    def _is_cache_valid(self) -> bool:
        """Check if cached context is still valid"""
        if self._context_cache is None:
            return False
        return (datetime.now().timestamp() - self._last_context_update) < self._cache_timeout
    
    def _format_current_weather(self, weather_data: Dict[str, Any]) -> str:
        """
        Format current weather data into a concise sentence.
        
        Args:
            weather_data (Dict[str, Any]): Current weather data from API
            
        Returns:
            str: Formatted current weather context
        """
        try:
            temp = weather_data.get('temperature', 'Unknown')
            description = weather_data.get('description', 'Unknown')
            humidity = weather_data.get('humidity', 'Unknown')
            wind_speed = weather_data.get('wind_speed', 'Unknown')
            
            # Format as single sentence
            context = f"Current weather in {self.location}: {temp}°F, {description.lower()}"
            
            # Add humidity and wind if available
            if humidity != 'Unknown':
                context += f", humidity {humidity}%"
            if wind_speed != 'Unknown':
                context += f", wind {wind_speed} mph"
            
            context += "."
            
            return context
            
        except Exception as e:
            logger.error(f"Error formatting current weather: {e}")
            return f"Current weather in {self.location}: Data unavailable."
    
    def _format_forecast_summary(self, hourly_forecast: List[Dict[str, Any]]) -> str:
        """
        Format hourly forecast into a concise summary.
        
        Args:
            hourly_forecast (List[Dict[str, Any]]): Hourly forecast data
            
        Returns:
            str: Formatted forecast summary or empty string if no significant events
        """
        try:
            if not hourly_forecast:
                return ""
            
            # Analyze forecast for significant events
            significant_events = self._analyze_forecast_events(hourly_forecast)
            
            if not significant_events:
                # No significant events, return brief summary
                return self._format_brief_forecast(hourly_forecast)
            
            # Format significant events
            return self._format_significant_events(significant_events)
            
        except Exception as e:
            logger.error(f"Error formatting forecast summary: {e}")
            return ""
    
    def _analyze_forecast_events(self, hourly_forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze forecast for significant weather events.
        
        Args:
            hourly_forecast (List[Dict[str, Any]]): Hourly forecast data
            
        Returns:
            List[Dict[str, Any]]: List of significant events
        """
        events = []
        
        # Look for rain events
        rain_events = self._find_rain_events(hourly_forecast)
        if rain_events:
            events.extend(rain_events)
        
        # Look for temperature extremes
        temp_events = self._find_temperature_extremes(hourly_forecast)
        if temp_events:
            events.extend(temp_events)
        
        # Look for wind events
        wind_events = self._find_wind_events(hourly_forecast)
        if wind_events:
            events.extend(wind_events)
        
        return events
    
    def _find_rain_events(self, hourly_forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find significant rain events in the forecast"""
        rain_events = []
        
        for hour_data in hourly_forecast:
            rain_prob = hour_data.get('rain_probability', 0)
            time_str = hour_data.get('time', '')
            
            # Consider rain significant if >30% probability
            if rain_prob > 30:
                rain_events.append({
                    'type': 'rain',
                    'time': time_str,
                    'probability': rain_prob,
                    'description': f"{rain_prob}% chance of rain at {time_str}"
                })
        
        return rain_events
    
    def _find_temperature_extremes(self, hourly_forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find temperature extremes in the forecast"""
        temp_events = []
        
        if not hourly_forecast:
            return temp_events
        
        # Find high and low temperatures
        temps = [h.get('temperature', 75) for h in hourly_forecast]
        high_temp = max(temps)
        low_temp = min(temps)
        
        # Check for extreme temperatures
        if high_temp > 90:
            temp_events.append({
                'type': 'high_temp',
                'temperature': high_temp,
                'description': f"High temperature of {high_temp}°F expected"
            })
        
        if low_temp < 40:
            temp_events.append({
                'type': 'low_temp', 
                'temperature': low_temp,
                'description': f"Low temperature of {low_temp}°F expected"
            })
        
        return temp_events
    
    def _find_wind_events(self, hourly_forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find significant wind events in the forecast"""
        wind_events = []
        
        for hour_data in hourly_forecast:
            wind_speed = hour_data.get('wind_speed', 0)
            time_str = hour_data.get('time', '')
            
            # Consider wind significant if >15 mph
            if wind_speed > 15:
                wind_events.append({
                    'type': 'wind',
                    'time': time_str,
                    'speed': wind_speed,
                    'description': f"Windy conditions ({wind_speed} mph) at {time_str}"
                })
        
        return wind_events
    
    def _format_brief_forecast(self, hourly_forecast: List[Dict[str, Any]]) -> str:
        """Format a brief forecast summary when no significant events are found"""
        if not hourly_forecast:
            return ""
        
        # Get temperature range
        temps = [h.get('temperature', 75) for h in hourly_forecast]
        high_temp = max(temps)
        low_temp = min(temps)
        
        # Check if there's any rain
        has_rain = any(h.get('rain_probability', 0) > 10 for h in hourly_forecast)
        
        if has_rain:
            return f"Forecast: High {high_temp}°F, low {low_temp}°F with some rain possible."
        else:
            return f"Forecast: High {high_temp}°F, low {low_temp}°F, no significant weather expected."
    
    def _format_significant_events(self, events: List[Dict[str, Any]]) -> str:
        """Format significant weather events into a concise summary"""
        if not events:
            return ""
        
        # Group events by type
        rain_events = [e for e in events if e['type'] == 'rain']
        temp_events = [e for e in events if e['type'] in ['high_temp', 'low_temp']]
        wind_events = [e for e in events if e['type'] == 'wind']
        
        parts = []
        
        # Add rain events
        if rain_events:
            rain_descriptions = [e['description'] for e in rain_events[:2]]  # Limit to 2 events
            parts.append(f"{', '.join(rain_descriptions)}")
        
        # Add temperature events
        if temp_events:
            temp_descriptions = [e['description'] for e in temp_events]
            parts.append(f"{', '.join(temp_descriptions)}")
        
        # Add wind events
        if wind_events:
            wind_descriptions = [e['description'] for e in wind_events[:1]]  # Limit to 1 event
            parts.append(f"{', '.join(wind_descriptions)}")
        
        if parts:
            return f"Forecast: {'; '.join(parts)}."
        
        return ""

# Global instance for use throughout the application
weather_context_provider = WeatherContextProvider()

def get_weather_context_messages() -> List[Dict[str, Any]]:
    """
    Get weather context messages for AI conversations.
    
    Returns:
        List[Dict[str, Any]]: List of weather context messages to inject into conversation
    """
    return weather_context_provider.get_weather_context()

def inject_weather_context_into_conversation(conversation_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Inject weather context into an existing conversation.
    
    Args:
        conversation_messages (List[Dict[str, Any]]): Existing conversation messages
        
    Returns:
        List[Dict[str, Any]]: Conversation messages with weather context injected
    """
    try:
        # Get weather context messages
        weather_context = get_weather_context_messages()
        
        # Insert weather context at the beginning (after any existing system messages)
        enhanced_messages = []
        system_messages_added = 0
        
        # Add existing system messages first
        for message in conversation_messages:
            if message.get('role') == 'system':
                enhanced_messages.append(message)
                system_messages_added += 1
            else:
                break
        
        # Add weather context messages
        enhanced_messages.extend(weather_context)
        
        # Add remaining messages
        enhanced_messages.extend(conversation_messages[system_messages_added:])
        
        logger.info(f"Injected {len(weather_context)} weather context messages into conversation")
        return enhanced_messages
        
    except Exception as e:
        logger.error(f"Error injecting weather context: {e}")
        return conversation_messages  # Return original messages on error

def create_weather_aware_conversation(user_message: str, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Create a new conversation with weather context for AI processing.
    
    Args:
        user_message (str): The user's message
        conversation_id (str, optional): Conversation ID for context
        
    Returns:
        List[Dict[str, Any]]: Conversation messages with weather context
    """
    try:
        # Get weather context
        weather_context = get_weather_context_messages()
        
        # Build conversation messages
        messages = []
        
        # Add weather context first
        messages.extend(weather_context)
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info(f"Created weather-aware conversation with {len(weather_context)} context messages")
        return messages
        
    except Exception as e:
        logger.error(f"Error creating weather-aware conversation: {e}")
        # Fallback to simple conversation
        return [{"role": "user", "content": user_message}] 