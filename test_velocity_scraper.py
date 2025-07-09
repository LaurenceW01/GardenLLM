#!/usr/bin/env python3
"""
Test script for Click2Houston Velocity Weather scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from click2houston_velocity_scraper import Click2HoustonVelocityScraper
import json

def test_velocity_scraper():
    """Test the Velocity Weather scraper functionality"""
    print("Testing Click2Houston Velocity Weather scraper...")
    print("=" * 50)
    
    # Initialize the scraper
    scraper = Click2HoustonVelocityScraper()
    
    try:
        # Test availability first
        print("Checking if Click2Houston Velocity Weather is available...")
        if not scraper.is_available():
            print("❌ Click2Houston Velocity Weather is not available")
            return False
        
        print("✅ Click2Houston Velocity Weather is available")
        
        # Test current weather
        print("\nFetching current weather...")
        current_weather = scraper.get_current_weather()
        
        if current_weather:
            print("✅ Successfully fetched current weather:")
            print(json.dumps(current_weather, indent=2, default=str))
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
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_velocity_scraper() 