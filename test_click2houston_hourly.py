#!/usr/bin/env python3
"""
Test script for Click2Houston hourly forecast scraping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from click2houston_scraper import Click2HoustonScraper
import json

def test_hourly_forecast():
    """Test the hourly forecast scraping functionality"""
    print("Testing Click2Houston hourly forecast scraping...")
    print("=" * 50)
    
    # Initialize the scraper
    scraper = Click2HoustonScraper()
    
    # Test availability first
    print("Checking if Click2Houston is available...")
    if not scraper.is_available():
        print("❌ Click2Houston is not available")
        return False
    
    print("✅ Click2Houston is available")
    
    # Test hourly forecast
    print("\nFetching hourly forecast...")
    try:
        hourly_data = scraper.get_hourly_forecast(hours=24)  # Get 24 hours
        
        if not hourly_data:
            print("❌ No hourly data returned")
            return False
        
        print(f"✅ Successfully retrieved {len(hourly_data)} hourly entries")
        
        # Display first few entries
        print("\nFirst 5 hourly entries:")
        print("-" * 80)
        for i, entry in enumerate(hourly_data[:5]):
            print(f"Entry {i+1}:")
            print(f"  Time: {entry.get('time', 'N/A')}")
            print(f"  Temperature: {entry.get('temperature', 'N/A')}°F")
            print(f"  Rain Probability: {entry.get('rain_probability', 'N/A')}%")
            print(f"  Description: {entry.get('description', 'N/A')}")
            print(f"  Wind Speed: {entry.get('wind_speed', 'N/A')} MPH")
            if entry.get('wind_direction'):
                print(f"  Wind Direction: {entry.get('wind_direction')}°")
            print()
        
        # Show data structure
        print("Data structure sample:")
        print(json.dumps(hourly_data[0], indent=2))
        
        # Validate data quality
        print("\nData quality check:")
        valid_entries = 0
        for entry in hourly_data:
            if (entry.get('time') and 
                entry.get('temperature') is not None and 
                entry.get('rain_probability') is not None):
                valid_entries += 1
        
        print(f"Valid entries: {valid_entries}/{len(hourly_data)}")
        
        if valid_entries > 0:
            print("✅ Hourly forecast scraping is working!")
            return True
        else:
            print("❌ No valid entries found")
            return False
            
    except Exception as e:
        print(f"❌ Error during hourly forecast test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_current_weather():
    """Test the current weather scraping functionality"""
    print("\n" + "=" * 50)
    print("Testing current weather scraping...")
    
    scraper = Click2HoustonScraper()
    
    try:
        current_weather = scraper.get_current_weather()
        
        if not current_weather:
            print("❌ No current weather data returned")
            return False
        
        print("✅ Current weather data retrieved:")
        print(json.dumps(current_weather, indent=2, default=str))
        return True
        
    except Exception as e:
        print(f"❌ Error during current weather test: {e}")
        return False

if __name__ == "__main__":
    print("Click2Houston Scraper Test")
    print("=" * 50)
    
    # Test hourly forecast
    hourly_success = test_hourly_forecast()
    
    # Test current weather
    current_success = test_current_weather()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Hourly Forecast: {'✅ PASS' if hourly_success else '❌ FAIL'}")
    print(f"Current Weather: {'✅ PASS' if current_success else '❌ FAIL'}")
    
    if hourly_success and current_success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 