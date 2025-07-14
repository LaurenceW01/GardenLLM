#!/usr/bin/env python3
"""
Simple test to show weather context messages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show_weather_context():
    """Show the weather context messages being generated"""
    print("🌤️  WEATHER CONTEXT MESSAGES")
    print("=" * 50)
    
    try:
        # Import and get weather context
        from weather_context_integration import get_weather_context_messages
        
        print("📡 Fetching weather context messages...")
        context_messages = get_weather_context_messages()
        
        print(f"\n✅ Generated {len(context_messages)} weather context messages:")
        print("-" * 50)
        
        for i, message in enumerate(context_messages):
            print(f"\n📨 Message {i+1}:")
            print(f"  Role: {message['role']}")
            print(f"  Content: {message['content']}")
            print("-" * 30)
        
        # Also show raw weather data for comparison
        print("\n🔍 RAW WEATHER DATA FOR COMPARISON:")
        print("-" * 50)
        
        from enhanced_weather_service import get_current_weather, get_hourly_forecast
        
        current = get_current_weather()
        if current:
            print("Current Weather:")
            print(f"  Temperature: {current.get('temperature', 'Unknown')}°F")
            print(f"  Description: {current.get('description', 'Unknown')}")
            print(f"  Humidity: {current.get('humidity', 'Unknown')}%")
            print(f"  Wind Speed: {current.get('wind_speed', 'Unknown')} mph")
        
        hourly = get_hourly_forecast(hours=6)
        if hourly:
            print(f"\nHourly Forecast (first 6 hours):")
            for i, hour in enumerate(hourly[:6]):
                print(f"  {hour.get('time', 'Unknown')}: {hour.get('temperature', 'Unknown')}°F, "
                      f"{hour.get('rain_probability', 0)}% rain")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_weather_context() 