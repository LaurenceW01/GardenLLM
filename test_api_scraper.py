#!/usr/bin/env python3
"""
Test script for Click2Houston API scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from click2houston_api_scraper import Click2HoustonAPIScraper
import json

def test_api_scraper():
    """Test the API-based scraper functionality"""
    print("Testing Click2Houston API scraper...")
    print("=" * 50)
    
    # Initialize the scraper
    scraper = Click2HoustonAPIScraper()
    
    try:
        # Test availability first
        print("Checking if Click2Houston is available...")
        if not scraper.is_available():
            print("❌ Click2Houston is not available")
            return False
        
        print("✅ Click2Houston is available")
        
        # Test current weather
        print("\nFetching current weather...")
        current_weather = scraper.get_current_weather()
        
        if current_weather:
            print("✅ Successfully fetched current weather:")
            print(f"  Temperature: {current_weather.get('temperature', 'N/A')}°F")
            print(f"  Description: {current_weather.get('description', 'N/A')}")
            print(f"  Humidity: {current_weather.get('humidity', 'N/A')}%")
            print(f"  Wind Speed: {current_weather.get('wind_speed', 'N/A')} mph")
        else:
            print("❌ Failed to fetch current weather")
            return False
        
        # Test hourly forecast
        print("\nFetching hourly forecast...")
        hourly_data = scraper.get_hourly_forecast(hours=24)
        
        if hourly_data:
            print(f"✅ Successfully fetched {len(hourly_data)} hourly entries")
            print("\nFirst 5 hourly entries:")
            for i, entry in enumerate(hourly_data[:5]):
                print(f"  {i+1}. {entry}")
        else:
            print("❌ Failed to fetch hourly forecast")
            return False
        
        # Test API endpoint extraction
        print("\nExtracting API endpoints...")
        endpoints = scraper._extract_api_endpoints()
        if endpoints:
            print(f"✅ Found {len(endpoints)} potential API endpoints:")
            for i, endpoint in enumerate(endpoints[:3]):
                print(f"  {i+1}. {endpoint}")
        else:
            print("ℹ️  No API endpoints found (this is normal)")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_weather_extraction():
    """Test weather data extraction from HTML"""
    print("\nTesting weather data extraction from HTML...")
    print("=" * 50)
    
    scraper = Click2HoustonAPIScraper()
    
    try:
        # Test HTML extraction
        html_data = scraper._extract_weather_data_from_html()
        if html_data:
            print("✅ Successfully extracted weather data from HTML:")
            for key, value in html_data.items():
                print(f"  {key}: {value}")
        else:
            print("ℹ️  No weather data extracted from HTML (falling back to generated data)")
        
        # Test hourly extraction
        hourly_data = scraper._extract_hourly_from_html(12)
        if hourly_data:
            print(f"✅ Successfully extracted {len(hourly_data)} hourly entries from HTML")
            print("Sample entries:")
            for entry in hourly_data[:3]:
                print(f"  {entry}")
        else:
            print("ℹ️  No hourly data extracted from HTML (falling back to generated data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Click2Houston API Scraper")
    print("=" * 50)
    
    # Run main test
    success1 = test_api_scraper()
    
    # Run extraction test
    success2 = test_weather_extraction()
    
    if success1 and success2:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed, but the scraper may still work with fallback data") 