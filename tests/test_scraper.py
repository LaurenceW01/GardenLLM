"""
Test script for Click2Houston scraper and enhanced weather service.
"""

import os
import sys
from datetime import datetime

def test_scraper():
    """Test the Click2Houston scraper functionality"""
    print("Testing Click2Houston Scraper...")
    print("=" * 50)
    
    try:
        from click2houston_scraper import Click2HoustonScraper
        
        scraper = Click2HoustonScraper()
        
        # Test availability
        print("1. Testing scraper availability...")
        is_available = scraper.is_available()
        print(f"   Scraper available: {is_available}")
        
        if is_available:
            # Test current weather
            print("\n2. Testing current weather...")
            current_weather = scraper.get_current_weather()
            if current_weather:
                print(f"   Temperature: {current_weather.get('temperature', 'Unknown')}°F")
                print(f"   Humidity: {current_weather.get('humidity', 'Unknown')}%")
                print(f"   Wind Speed: {current_weather.get('wind_speed', 'Unknown')} mph")
                print(f"   Description: {current_weather.get('description', 'Unknown')}")
            else:
                print("   Failed to get current weather")
            
            # Test hourly forecast
            print("\n3. Testing hourly forecast...")
            hourly_forecast = scraper.get_hourly_forecast(6)
            if hourly_forecast:
                print(f"   Got {len(hourly_forecast)} hours of forecast data")
                for i, hour in enumerate(hourly_forecast[:3]):
                    print(f"   Hour {i+1}: {hour['time']} - {hour['temperature']}°F, {hour['rain_probability']}% rain")
            else:
                print("   Failed to get hourly forecast")
            
            # Test daily forecast
            print("\n4. Testing daily forecast...")
            daily_forecast = scraper.get_daily_forecast(3)
            if daily_forecast:
                print(f"   Got {len(daily_forecast)} days of forecast data")
                for day in daily_forecast:
                    date_str = day['date'].strftime('%Y-%m-%d')
                    print(f"   {date_str}: High {day['temp_max']}°F, Low {day['temp_min']}°F, {day['rain_probability']}% rain")
            else:
                print("   Failed to get daily forecast")
        
    except Exception as e:
        print(f"Error testing scraper: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_service():
    """Test the enhanced weather service"""
    print("\n\nTesting Enhanced Weather Service...")
    print("=" * 50)
    
    try:
        from enhanced_weather_service import EnhancedWeatherService
        
        # Initialize with fallback API key if available
        api_key = os.getenv('OPENWEATHER_API_KEY')
        service = EnhancedWeatherService(api_key if api_key else None)
        
        # Test current weather
        print("1. Testing current weather...")
        current_weather = service.get_current_weather()
        if current_weather:
            print(f"   Temperature: {current_weather.get('temperature', 'Unknown')}°F")
            print(f"   Data Source: {service.last_service_used}")
        else:
            print("   Failed to get current weather")
        
        # Test weather summary
        print("\n2. Testing weather summary...")
        summary = service.get_weather_summary()
        if summary:
            print("   Summary generated successfully")
            print(f"   Length: {len(summary)} characters")
        else:
            print("   Failed to get weather summary")
        
        # Test plant care recommendations
        print("\n3. Testing plant care recommendations...")
        recommendations = service.get_plant_care_recommendations()
        if recommendations:
            print("   Recommendations generated successfully")
            print(f"   Length: {len(recommendations)} characters")
        else:
            print("   Failed to get plant care recommendations")
        
        # Test weather analysis
        print("\n4. Testing weather analysis...")
        analysis = service.analyze_weather_conditions()
        if analysis and 'error' not in analysis:
            print(f"   Temperature category: {analysis.get('temperature_category', 'Unknown')}")
            print(f"   Humidity category: {analysis.get('humidity_category', 'Unknown')}")
            print(f"   Overall conditions: {analysis.get('overall_conditions', 'Unknown')}")
            print(f"   Recommendations: {len(analysis.get('recommendations', []))}")
        else:
            print("   Failed to analyze weather conditions")
        
    except Exception as e:
        print(f"Error testing enhanced service: {e}")
        import traceback
        traceback.print_exc()

def compare_services():
    """Compare scraper vs API performance"""
    print("\n\nComparing Services...")
    print("=" * 50)
    
    try:
        from click2houston_scraper import Click2HoustonScraper
        from weather_service import WeatherService
        import time
        
        api_key = os.getenv('OPENWEATHER_API_KEY')
        
        if not api_key:
            print("No OpenWeather API key found, skipping comparison")
            return
        
        scraper = Click2HoustonScraper()
        api_service = WeatherService(api_key)
        
        # Test scraper performance
        print("Testing scraper performance...")
        start_time = time.time()
        scraper_weather = scraper.get_current_weather()
        scraper_time = time.time() - start_time
        
        # Test API performance
        print("Testing API performance...")
        start_time = time.time()
        api_weather = api_service.get_current_weather()
        api_time = time.time() - start_time
        
        print(f"\nPerformance Comparison:")
        print(f"   Scraper time: {scraper_time:.2f} seconds")
        print(f"   API time: {api_time:.2f} seconds")
        print(f"   Speed difference: {api_time/scraper_time:.1f}x {'slower' if api_time > scraper_time else 'faster'}")
        
        if scraper_weather and api_weather:
            print(f"\nData Comparison:")
            print(f"   Scraper temp: {scraper_weather.get('temperature', 'Unknown')}°F")
            print(f"   API temp: {api_weather.get('temperature', 'Unknown')}°F")
            print(f"   Scraper humidity: {scraper_weather.get('humidity', 'Unknown')}%")
            print(f"   API humidity: {api_weather.get('humidity', 'Unknown')}%")
        
    except Exception as e:
        print(f"Error comparing services: {e}")

if __name__ == "__main__":
    print(f"Click2Houston Scraper Test - {datetime.now()}")
    print("=" * 60)
    
    # Test scraper
    test_scraper()
    
    # Test enhanced service
    test_enhanced_service()
    
    # Compare services
    compare_services()
    
    print("\n" + "=" * 60)
    print("Test completed!") 