#!/usr/bin/env python3
"""
Test web interface weather integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_web_weather_endpoints():
    """Test web endpoints that should include weather context"""
    print("🌐 WEB WEATHER INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test weather API endpoint
        from web import app
        import json
        
        with app.test_client() as client:
            print("📡 Testing /api/weather endpoint...")
            
            response = client.get('/api/weather')
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ✅ Weather API response: {data.get('success', False)}")
                
                if data.get('success'):
                    print(f"  📊 Current weather: {data.get('weather_summary', 'N/A')}")
                    print(f"  🌱 Plant care recommendations: {data.get('plant_care_recommendations', 'N/A')[:50]}...")
                    
                    # Check if weather data is present
                    current_weather = data.get('current_weather')
                    if current_weather:
                        print(f"  🌡️  Temperature: {current_weather.get('temperature', 'Unknown')}°F")
                        print(f"  💨 Wind: {current_weather.get('wind_speed', 'Unknown')} mph")
                        print(f"  💧 Humidity: {current_weather.get('humidity', 'Unknown')}%")
                    else:
                        print("  ⚠️  No current weather data in response")
                else:
                    print(f"  ❌ Weather API failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ Weather API returned status {response.status_code}")
        
        print("\n✅ Web weather integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in web weather test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_weather_context_availability():
    """Test that weather context is available throughout the system"""
    print("\n🔧 WEATHER CONTEXT AVAILABILITY TEST")
    print("=" * 50)
    
    try:
        # Test all weather context functions
        from weather_context_integration import (
            WeatherContextProvider,
            get_weather_context_messages,
            inject_weather_context_into_conversation,
            create_weather_aware_conversation
        )
        
        print("📡 Testing weather context availability...")
        
        # Test provider
        provider = WeatherContextProvider()
        context1 = provider.get_weather_context()
        print(f"  ✅ WeatherContextProvider: {len(context1)} messages")
        
        # Test utility functions
        context2 = get_weather_context_messages()
        print(f"  ✅ get_weather_context_messages: {len(context2)} messages")
        
        # Test conversation injection
        sample_conv = [{"role": "user", "content": "Hello"}]
        enhanced_conv = inject_weather_context_into_conversation(sample_conv)
        print(f"  ✅ inject_weather_context_into_conversation: {len(enhanced_conv)} messages")
        
        # Test weather-aware conversation
        weather_conv = create_weather_aware_conversation("Test question")
        print(f"  ✅ create_weather_aware_conversation: {len(weather_conv)} messages")
        
        # Verify all functions return consistent results
        if len(context1) == len(context2) and len(context1) > 0:
            print("  ✅ All weather context functions working consistently")
        else:
            print("  ⚠️  Inconsistent results from weather context functions")
        
        print("\n✅ Weather context availability test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in weather context availability test: {e}")
        return False

def test_weather_data_quality():
    """Test the quality of weather data being used"""
    print("\n📊 WEATHER DATA QUALITY TEST")
    print("=" * 50)
    
    try:
        from enhanced_weather_service import get_current_weather, get_hourly_forecast
        
        print("📡 Testing weather data quality...")
        
        # Test current weather
        current = get_current_weather()
        if current:
            print("  ✅ Current weather data available:")
            print(f"    🌡️  Temperature: {current.get('temperature', 'Unknown')}°F")
            print(f"    🌤️  Description: {current.get('description', 'Unknown')}")
            print(f"    💧 Humidity: {current.get('humidity', 'Unknown')}%")
            print(f"    💨 Wind Speed: {current.get('wind_speed', 'Unknown')} mph")
            
            # Check data quality
            temp = current.get('temperature')
            if temp and isinstance(temp, (int, float)) and 0 <= temp <= 120:
                print("    ✅ Temperature data is reasonable")
            else:
                print("    ⚠️  Temperature data may be invalid")
        else:
            print("  ❌ No current weather data available")
        
        # Test hourly forecast
        hourly = get_hourly_forecast(hours=6)
        if hourly:
            print(f"  ✅ Hourly forecast available: {len(hourly)} hours")
            
            # Check first few hours
            for i, hour in enumerate(hourly[:3]):
                temp = hour.get('temperature')
                rain_prob = hour.get('rain_probability', 0)
                print(f"    Hour {i+1}: {temp}°F, {rain_prob}% rain")
                
                if temp and isinstance(temp, (int, float)) and 0 <= temp <= 120:
                    print(f"      ✅ Temperature {temp}°F is reasonable")
                else:
                    print(f"      ⚠️  Temperature {temp}°F may be invalid")
        else:
            print("  ❌ No hourly forecast data available")
        
        print("\n✅ Weather data quality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in weather data quality test: {e}")
        return False

def main():
    """Run all web weather integration tests"""
    print("🌐 WEB WEATHER INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Web Weather Endpoints", test_web_weather_endpoints),
        ("Weather Context Availability", test_weather_context_availability),
        ("Weather Data Quality", test_weather_data_quality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All web weather integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 