#!/usr/bin/env python3
"""Test script to debug rain probability calculation"""

from weather_service import get_weather_forecast, get_hourly_rain_forecast
import json

def test_rain_data():
    print("Testing rain probability calculations...")
    
    # Test 3-day forecast
    print("\n=== 3-Day Forecast ===")
    forecast = get_weather_forecast()
    for day in forecast:
        print(f"Date: {day['date']}")
        print(f"  Rain Probability: {day['rain_probability']}%")
        print(f"  Wind Speed: {day['wind_speed']} mph")
        print(f"  Temperature: {day['temp_min']}°F - {day['temp_max']}°F")
        print()
    
    # Test hourly forecast
    print("\n=== Hourly Rain Forecast ===")
    hourly = get_hourly_rain_forecast()
    for hour in hourly[:6]:  # First 6 hours
        print(f"Time: {hour['time']}")
        print(f"  Rain Probability: {hour['rain_probability']}%")
        print(f"  Wind Speed: {hour['wind_speed']} mph")
        print(f"  Temperature: {hour['temperature']}°F")
        print()

if __name__ == "__main__":
    test_rain_data() 