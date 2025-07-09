#!/usr/bin/env python3
"""Debug script to examine raw OpenWeather API data"""

import os
import requests
from datetime import datetime

def debug_weather_api():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        print("No API key found")
        return
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': 29.7604,  # Houston latitude
        'lon': -95.3698,  # Houston longitude
        'appid': api_key,
        'units': 'imperial'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("=== Raw API Data Analysis ===")
        print(f"Total forecast entries: {len(data['list'])}")
        print()
        
        # Examine first few entries in detail
        for i, item in enumerate(data['list'][:8]):  # First 8 entries (24 hours)
            dt = datetime.fromtimestamp(item['dt'])
            print(f"Entry {i+1}: {dt.strftime('%Y-%m-%d %I:%M %p')}")
            print(f"  Weather: {item['weather'][0]['description']}")
            print(f"  Temperature: {item['main']['temp']}°F")
            print(f"  Wind Speed: {item['wind']['speed']} mph")
            
            # Check for pop (probability of precipitation)
            if 'pop' in item:
                print(f"  POP: {item['pop']} ({item['pop'] * 100}%)")
            else:
                print(f"  POP: Not present")
            
            # Check for rain data
            if 'rain' in item:
                print(f"  Rain: {item['rain']}")
            else:
                print(f"  Rain: Not present")
            
            print()
        
        # Check if any entries have non-zero pop values
        non_zero_pop = [item for item in data['list'] if 'pop' in item and item['pop'] > 0]
        print(f"Entries with non-zero POP: {len(non_zero_pop)}")
        
        if non_zero_pop:
            print("Non-zero POP entries:")
            for item in non_zero_pop:
                dt = datetime.fromtimestamp(item['dt'])
                print(f"  {dt.strftime('%Y-%m-%d %I:%M %p')}: {item['pop'] * 100}% - {item['weather'][0]['description']}")
        else:
            print("No non-zero POP values found!")
        
        print()
        
        # Check for any rain data
        rain_entries = [item for item in data['list'] if 'rain' in item and item['rain']]
        print(f"Entries with rain data: {len(rain_entries)}")
        
        if rain_entries:
            print("Rain data entries:")
            for item in rain_entries:
                dt = datetime.fromtimestamp(item['dt'])
                print(f"  {dt.strftime('%Y-%m-%d %I:%M %p')}: {item['rain']} - {item['weather'][0]['description']}")
        else:
            print("No rain data found!")
        
        print()
        
        # Show all weather conditions
        print("All weather conditions in forecast:")
        conditions = {}
        for item in data['list']:
            condition = item['weather'][0]['description']
            if condition not in conditions:
                conditions[condition] = 0
            conditions[condition] += 1
        
        for condition, count in sorted(conditions.items()):
            print(f"  {condition}: {count} times")
        
        print()
        
        # Show first few entries with POP values
        print("First 10 entries with POP values:")
        for i, item in enumerate(data['list'][:10]):
            dt = datetime.fromtimestamp(item['dt'])
            pop = item.get('pop', 'Not present')
            if pop != 'Not present':
                pop = f"{pop * 100}%"
            print(f"  {dt.strftime('%Y-%m-%d %I:%M %p')}: POP = {pop}, Weather = {item['weather'][0]['description']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_weather_api() 