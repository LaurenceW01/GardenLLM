#!/usr/bin/env python3
"""Clear cache and get fresh weather data"""

from baron_weather_velocity_api import BaronWeatherVelocityAPI
from config import BARON_API_KEY, BARON_API_SECRET
import time

def clear_cache_and_test():
    """Clear cache and get fresh weather data"""
    print("Clearing cache and getting fresh weather data...")
    print("=" * 60)
    
    # Create new API instance (this will have a fresh cache)
    api = BaronWeatherVelocityAPI(BARON_API_KEY, BARON_API_SECRET)
    
    # Clear the cache manually
    api.cache.clear()
    print("✅ Cache cleared")
    
    # Get fresh current weather
    print("\nGetting fresh current weather...")
    current = api.get_current_weather()
    if current:
        print(f"Current Weather:")
        print(f"  Temperature: {current['temperature']}°F")
        print(f"  Wind Speed: {current['wind_speed']} mph")
        print(f"  Conditions: {current['description']}")
        print(f"  Humidity: {current['humidity']}%")
        print(f"  Pressure: {current['pressure']} hPa")
    else:
        print("❌ No current weather data available")
    
    # Get fresh hourly forecast
    print("\nGetting fresh hourly forecast...")
    hourly = api.get_hourly_forecast(hours=8)
    if hourly:
        print(f"Hourly Forecast (first 8 hours):")
        print(f"{'Time':<8} {'Temp':<6} {'Rain':<6} {'Wind':<6} {'Description'}")
        print("-" * 60)
        for h in hourly[:8]:
            print(f"{h['time']:<8} {h['temperature']}°F   {h['rain_probability']}%    {h['wind_speed']} mph  {h['description']}")
    else:
        print("❌ No hourly forecast data available")
    
    print("\n" + "=" * 60)
    print("✅ Fresh data retrieved!")

if __name__ == "__main__":
    clear_cache_and_test() 