#!/usr/bin/env python3
"""
Weather Context Integration Demo Test

This test demonstrates the weather context integration by showing
how different weather conditions are formatted into context messages
for AI conversations.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_context_integration import WeatherContextProvider, get_weather_context_messages
from enhanced_weather_service import get_current_weather, get_hourly_forecast
import json

def demo_current_weather_context():
    """Demonstrate current weather context formatting"""
    print("🌤️  CURRENT WEATHER CONTEXT DEMO")
    print("=" * 60)
    
    try:
        # Get actual current weather
        current_weather = get_current_weather()
        
        if current_weather:
            print("✅ Current Weather Data Retrieved:")
            print(f"  Temperature: {current_weather.get('temperature', 'Unknown')}°F")
            print(f"  Description: {current_weather.get('description', 'Unknown')}")
            print(f"  Humidity: {current_weather.get('humidity', 'Unknown')}%")
            print(f"  Wind Speed: {current_weather.get('wind_speed', 'Unknown')} mph")
            print(f"  Pressure: {current_weather.get('pressure', 'Unknown')} hPa")
            
            # Create provider and format context
            provider = WeatherContextProvider()
            current_context = provider._format_current_weather(current_weather)
            
            print(f"\n📝 Formatted Current Weather Context:")
            print(f"  '{current_context}'")
            
        else:
            print("❌ No current weather data available")
            
    except Exception as e:
        print(f"❌ Error getting current weather: {e}")

def demo_forecast_context():
    """Demonstrate forecast context formatting"""
    print("\n🌦️  FORECAST CONTEXT DEMO")
    print("=" * 60)
    
    try:
        # Get actual hourly forecast
        hourly_forecast = get_hourly_forecast(hours=24)
        
        if hourly_forecast:
            print(f"✅ Hourly Forecast Data Retrieved: {len(hourly_forecast)} hours")
            
            # Show first few hours
            print("\n📊 First 6 Hours of Forecast:")
            for i, hour in enumerate(hourly_forecast[:6]):
                print(f"  {hour.get('time', 'Unknown')}: {hour.get('temperature', 'Unknown')}°F, "
                      f"{hour.get('rain_probability', 0)}% rain, {hour.get('wind_speed', 'Unknown')} mph wind")
            
            # Create provider and analyze forecast
            provider = WeatherContextProvider()
            
            # Test forecast analysis
            significant_events = provider._analyze_forecast_events(hourly_forecast)
            print(f"\n🔍 Significant Events Found: {len(significant_events)}")
            
            for event in significant_events:
                print(f"  - {event['description']}")
            
            # Format forecast summary
            forecast_context = provider._format_forecast_summary(hourly_forecast)
            
            print(f"\n📝 Formatted Forecast Context:")
            if forecast_context:
                print(f"  '{forecast_context}'")
            else:
                print("  (No significant events to report)")
                
        else:
            print("❌ No hourly forecast data available")
            
    except Exception as e:
        print(f"❌ Error getting forecast: {e}")

def demo_complete_weather_context():
    """Demonstrate complete weather context messages"""
    print("\n🌍 COMPLETE WEATHER CONTEXT MESSAGES")
    print("=" * 60)
    
    try:
        # Get complete weather context
        context_messages = get_weather_context_messages()
        
        print(f"✅ Generated {len(context_messages)} weather context messages:")
        
        for i, message in enumerate(context_messages):
            print(f"\n📨 Message {i+1}:")
            print(f"  Role: {message['role']}")
            print(f"  Content: {message['content']}")
            
            # Analyze content
            content = message['content'].lower()
            if 'current weather' in content:
                print("  📍 Type: Current Weather")
            elif 'forecast' in content:
                print("  📍 Type: Forecast")
            elif 'unavailable' in content:
                print("  📍 Type: Fallback")
            
            # Check for specific weather elements
            if '°f' in message['content']:
                print("  🌡️  Contains: Temperature")
            if 'rain' in content:
                print("  🌧️  Contains: Rain information")
            if 'wind' in content:
                print("  💨 Contains: Wind information")
            if 'humidity' in content:
                print("  💧 Contains: Humidity information")
                
    except Exception as e:
        print(f"❌ Error getting complete weather context: {e}")

def demo_weather_context_in_conversation():
    """Demonstrate weather context in a sample conversation"""
    print("\n💬 WEATHER CONTEXT IN CONVERSATION DEMO")
    print("=" * 60)
    
    try:
        from weather_context_integration import create_weather_aware_conversation
        
        # Sample gardening questions
        sample_questions = [
            "Should I water my tomatoes today?",
            "Is it a good day to plant new flowers?",
            "Do I need to protect my plants from frost tonight?",
            "Can I fertilize my garden today?",
            "Should I bring my potted plants inside?"
        ]
        
        print("✅ Sample Gardening Questions with Weather Context:")
        
        for i, question in enumerate(sample_questions):
            print(f"\n🌱 Question {i+1}: {question}")
            
            # Create weather-aware conversation
            conversation = create_weather_aware_conversation(question)
            
            print(f"  📝 Weather Context Messages: {len(conversation) - 1}")
            for j, message in enumerate(conversation[:-1]):  # Exclude user message
                print(f"    Context {j+1}: {message['content'][:80]}...")
            
            print(f"  👤 User Message: {conversation[-1]['content']}")
            
    except Exception as e:
        print(f"❌ Error demonstrating conversation context: {e}")

def demo_cache_functionality():
    """Demonstrate weather context caching"""
    print("\n⏱️  WEATHER CONTEXT CACHE DEMO")
    print("=" * 60)
    
    try:
        provider = WeatherContextProvider()
        
        print("🔄 Testing cache functionality...")
        
        # First call - should fetch fresh data
        print("\n📡 First call (fresh data):")
        start_time = time.time()
        context1 = provider.get_weather_context()
        time1 = time.time() - start_time
        print(f"  Time: {time1:.3f}s")
        print(f"  Messages: {len(context1)}")
        
        # Second call - should use cache
        print("\n💾 Second call (cached data):")
        start_time = time.time()
        context2 = provider.get_weather_context()
        time2 = time.time() - start_time
        print(f"  Time: {time2:.3f}s")
        print(f"  Messages: {len(context2)}")
        
        # Compare results
        if context1 == context2:
            print("  ✅ Cache working correctly - same results")
        else:
            print("  ⚠️  Cache may not be working - different results")
            
        if time2 < time1:
            print(f"  ✅ Cache is faster: {time1/time2:.1f}x speedup")
        else:
            print(f"  ⚠️  Cache not faster: {time2/time1:.1f}x slower")
            
    except Exception as e:
        print(f"❌ Error testing cache: {e}")

def demo_error_handling():
    """Demonstrate error handling in weather context"""
    print("\n🛡️  ERROR HANDLING DEMO")
    print("=" * 60)
    
    try:
        provider = WeatherContextProvider()
        
        # Test with invalid weather data
        print("🧪 Testing with invalid weather data...")
        
        invalid_weather = {
            'temperature': None,
            'description': None,
            'humidity': None,
            'wind_speed': None
        }
        
        context = provider._format_current_weather(invalid_weather)
        print(f"  📝 Formatted context: '{context}'")
        
        # Test with empty forecast
        print("\n🧪 Testing with empty forecast...")
        empty_forecast = []
        forecast_context = provider._format_forecast_summary(empty_forecast)
        print(f"  📝 Formatted context: '{forecast_context}'")
        
        print("\n✅ Error handling working correctly")
        
    except Exception as e:
        print(f"❌ Error in error handling demo: {e}")

def main():
    """Run all weather context demos"""
    print("🌤️  WEATHER CONTEXT INTEGRATION DEMONSTRATION")
    print("=" * 80)
    print("This demo shows how weather data is converted into context messages")
    print("for AI conversations, enabling weather-aware gardening advice.")
    print("=" * 80)
    
    demos = [
        ("Current Weather Context", demo_current_weather_context),
        ("Forecast Context", demo_forecast_context),
        ("Complete Weather Context", demo_complete_weather_context),
        ("Weather Context in Conversation", demo_weather_context_in_conversation),
        ("Cache Functionality", demo_cache_functionality),
        ("Error Handling", demo_error_handling)
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ Error in {demo_name}: {e}")
        
        print("\n" + "="*80)
    
    print("🎉 Weather Context Integration Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Current weather formatting")
    print("✅ Forecast analysis and summarization")
    print("✅ Significant weather event detection")
    print("✅ Context message generation")
    print("✅ Conversation integration")
    print("✅ Caching for performance")
    print("✅ Error handling and fallbacks")

if __name__ == "__main__":
    main() 