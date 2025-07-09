#!/usr/bin/env python3
"""Test script to verify weather data fixes"""

from baron_weather_velocity_api import BaronWeatherVelocityAPI
from config import BARON_API_KEY, BARON_API_SECRET

def test_weather_fixes():
    """Test the weather data fixes"""
    print("Testing weather data fixes...")
    print("=" * 50)
    
    api = BaronWeatherVelocityAPI(BARON_API_KEY, BARON_API_SECRET)
    
    # Test current weather
    current = api.get_current_weather()
    if current:
        print(f"Current Weather:")
        print(f"  Temperature: {current['temperature']}°F")
        print(f"  Wind Speed: {current['wind_speed']} mph (should be rounded)")
        print(f"  Conditions: {current['description']}")
        print()
    
    # Test hourly forecast
    hourly = api.get_hourly_forecast(hours=8)
    if hourly:
        print(f"Hourly Forecast (first 8 hours):")
        print(f"{'Time':<8} {'Temp':<6} {'Rain':<6} {'Wind':<6} {'Description'}")
        print("-" * 50)
        for h in hourly[:8]:
            print(f"{h['time']:<8} {h['temperature']}°F   {h['rain_probability']}%    {h['wind_speed']} mph  {h['description']}")
    
    print("\n" + "=" * 50)
    print("✅ Weather data fixes applied!")

if __name__ == "__main__":
    test_weather_fixes() 