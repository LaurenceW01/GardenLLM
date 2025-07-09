#!/usr/bin/env python3
"""
Test script for Click2Houston Selenium scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from click2houston_selenium_scraper import Click2HoustonSeleniumScraper
import json

def test_selenium_scraper():
    """Test the Selenium-based scraper functionality"""
    print("Testing Click2Houston Selenium scraper...")
    print("=" * 50)
    
    # Initialize the scraper with headless mode
    scraper = Click2HoustonSeleniumScraper(headless=True, timeout=30)
    
    try:
        # Test availability first
        print("Checking if Click2Houston is available...")
        if not scraper.is_available():
            print("❌ Click2Houston is not available")
            return False
        
        print("✅ Click2Houston is available")
        
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
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Always close the scraper
        scraper.close()

def test_with_visible_browser():
    """Test with visible browser for debugging"""
    print("Testing with visible browser...")
    print("=" * 50)
    
    # Initialize the scraper with visible browser
    scraper = Click2HoustonSeleniumScraper(headless=False, timeout=30)
    
    try:
        # Test availability
        print("Checking availability...")
        if not scraper.is_available():
            print("❌ Not available")
            return False
        
        print("✅ Available")
        
        # Test hourly forecast
        print("Fetching hourly forecast...")
        hourly_data = scraper.get_hourly_forecast(hours=12)
        
        if hourly_data:
            print(f"✅ Got {len(hourly_data)} entries")
            print("Sample data:")
            for entry in hourly_data[:3]:
                print(f"  {entry}")
        else:
            print("❌ No data")
        
        # Keep browser open for manual inspection
        input("Press Enter to close browser...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        scraper.close()

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Headless test (recommended)")
    print("2. Visible browser test (for debugging)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_with_visible_browser()
    else:
        test_selenium_scraper() 