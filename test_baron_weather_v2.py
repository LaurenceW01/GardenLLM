#!/usr/bin/env python3
"""
Test script for Baron Weather VelocityWeather API client (v2) with HMAC authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from baron_weather_velocity_api import BaronWeatherVelocityAPI
import json

def test_baron_weather_v2():
    """Test the Baron Weather VelocityWeather API client functionality"""
    print("Testing Baron Weather VelocityWeather API client (v2)...")
    print("=" * 50)
    
    # Initialize the scraper with your API credentials
    access_key = "tcATLX0GE43S"
    access_key_secret = "1fWKEKScFNHPGxxUA851w7rDXfbMSPFTkEfgBvByNm"
    
    scraper = BaronWeatherVelocityAPI(access_key=access_key, access_key_secret=access_key_secret)
    
    try:
        # Test availability first
        print("Checking if Baron Weather VelocityWeather API is available...")
        if not scraper.is_available():
            print("❌ Baron Weather VelocityWeather API is not available")
            return False
        
        print("✅ Baron Weather VelocityWeather API is available")
        
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

def test_api_endpoints_directly():
    """Test the API endpoints directly to understand the response format"""
    print("\nTesting API endpoints directly...")
    print("=" * 50)
    
    import requests
    import base64
    import hmac
    import hashlib
    import time
    
    access_key = "tcATLX0GE43S"
    access_key_secret = "1fWKEKScFNHPGxxUA851w7rDXfbMSPFTkEfgBvByNm"
    host = "http://api.velocityweather.com/v1"
    
    def sign_request(url):
        """Sign a request with HMAC authentication"""
        ts = str(int(time.time()))
        sig = base64.urlsafe_b64encode(
            hmac.new(
                access_key_secret.encode('utf-8'), 
                (access_key + ":" + ts).encode('utf-8'), 
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        separator = '?' if '?' not in url else '&'
        return f"{url}{separator}sig={sig}&ts={ts}"
    
    # Test METAR nearest endpoint
    print("Testing METAR nearest endpoint...")
    metar_uri = f"/reports/metar/nearest.json?lat=29.7604&lon=-95.3698&within_radius=500&max_age=75"
    metar_url = f"{host}/{access_key}{metar_uri}"
    signed_metar_url = sign_request(metar_url)
    
    try:
        response = requests.get(signed_metar_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ METAR API response:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing METAR: {e}")
    
    # Test NDFD hourly forecast endpoint
    print("\nTesting NDFD hourly forecast endpoint...")
    from datetime import datetime, timedelta
    
    forecast_time = datetime.utcnow() + timedelta(hours=4)
    datetime_str = forecast_time.replace(microsecond=0).isoformat() + 'Z'
    
    ndfd_uri = f"/reports/ndfd/hourly.json?lat=29.7604&lon=-95.3698&utc={datetime_str}"
    ndfd_url = f"{host}/{access_key}{ndfd_uri}"
    signed_ndfd_url = sign_request(ndfd_url)
    
    try:
        response = requests.get(signed_ndfd_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ NDFD hourly forecast API response:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing NDFD: {e}")

if __name__ == "__main__":
    # Test API endpoints first to understand the response format
    test_api_endpoints_directly()
    
    # Then test the scraper
    test_baron_weather_v2() 