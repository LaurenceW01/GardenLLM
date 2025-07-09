#!/usr/bin/env python3
"""Debug the time calculation for hourly forecasts"""

from baron_weather_velocity_api import BaronWeatherVelocityAPI
from config import BARON_API_KEY, BARON_API_SECRET
from datetime import datetime, timedelta, timezone

def debug_time():
    """Debug the time calculation"""
    print("Debugging time calculation...")
    print("=" * 60)
    
    # Create API instance
    api = BaronWeatherVelocityAPI(BARON_API_KEY, BARON_API_SECRET)
    
    # Get current time
    current_time = api._get_houston_time()
    print(f"Current Houston time: {current_time}")
    print(f"Current hour: {current_time.hour}")
    print(f"Current minute: {current_time.minute}")
    
    # Calculate next hour
    next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    print(f"Next hour: {next_hour}")
    print(f"Next hour formatted: {next_hour.strftime('%I %p').replace(' 0', ' ')}")
    
    # Test the calculation for first few hours
    print("\nFirst 8 hours:")
    for i in range(8):
        hour_time = next_hour + timedelta(hours=i)
        formatted_time = hour_time.strftime('%I %p').replace(' 0', ' ')
        print(f"  Hour {i}: {hour_time} -> {formatted_time}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_time() 