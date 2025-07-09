#!/usr/bin/env python3
"""
Debug script to examine Click2Houston HTML structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from click2houston_scraper import Click2HoustonScraper
from bs4 import BeautifulSoup
import re

def debug_page_structure():
    """Debug the actual HTML structure of the Click2Houston weather page"""
    print("Debugging Click2Houston page structure...")
    print("=" * 60)
    
    scraper = Click2HoustonScraper()
    
    # Get the HTML content
    soup = scraper._get_html_content()
    if not soup:
        print("❌ Could not fetch HTML content")
        return
    
    print("✅ HTML content fetched successfully")
    
    # Look for hourline elements
    print("\n1. Searching for 'hourline' elements...")
    hourline_elements = soup.find_all('div', class_='hourline')
    print(f"Found {len(hourline_elements)} elements with class 'hourline'")
    
    if hourline_elements:
        print("First hourline element:")
        print(hourline_elements[0].prettify()[:500] + "...")
    else:
        print("No hourline elements found")
    
    # Look for any divs with 'hour' in the class name
    print("\n2. Searching for divs with 'hour' in class name...")
    hour_divs = soup.find_all('div', class_=re.compile(r'hour', re.IGNORECASE))
    print(f"Found {len(hour_divs)} divs with 'hour' in class name")
    
    for i, div in enumerate(hour_divs[:3]):
        print(f"Div {i+1} classes: {div.get('class', [])}")
        print(f"Content preview: {div.get_text()[:100]}...")
    
    # Look for weather-related classes
    print("\n3. Searching for weather-related classes...")
    weather_classes = ['weather', 'forecast', 'temp', 'temperature', 'precip', 'wind']
    for class_name in weather_classes:
        elements = soup.find_all(class_=re.compile(class_name, re.IGNORECASE))
        print(f"Elements with '{class_name}' in class: {len(elements)}")
        if elements:
            print(f"  First element classes: {elements[0].get('class', [])}")
    
    # Look for table structures
    print("\n4. Searching for table structures...")
    tables = soup.find_all('table')
    print(f"Found {len(tables)} table elements")
    
    for i, table in enumerate(tables[:2]):
        print(f"Table {i+1}:")
        print(f"  Classes: {table.get('class', [])}")
        print(f"  Rows: {len(table.find_all('tr'))}")
        if table.find_all('tr'):
            first_row = table.find_all('tr')[0]
            print(f"  First row content: {first_row.get_text()[:100]}...")
    
    # Look for specific text patterns
    print("\n5. Searching for weather data patterns...")
    page_text = soup.get_text()
    
    # Look for time patterns
    time_pattern = re.compile(r'\d{1,2}\s*(?:AM|PM|am|pm)')
    time_matches = time_pattern.findall(page_text)
    print(f"Time patterns found: {len(time_matches)}")
    if time_matches:
        print(f"  Sample times: {time_matches[:10]}")
    
    # Look for temperature patterns
    temp_pattern = re.compile(r'\d+°')
    temp_matches = temp_pattern.findall(page_text)
    print(f"Temperature patterns found: {len(temp_matches)}")
    if temp_matches:
        print(f"  Sample temperatures: {temp_matches[:10]}")
    
    # Look for percentage patterns
    percent_pattern = re.compile(r'\d+%')
    percent_matches = percent_pattern.findall(page_text)
    print(f"Percentage patterns found: {len(percent_matches)}")
    if percent_matches:
        print(f"  Sample percentages: {percent_matches[:10]}")
    
    # Look for the specific pattern we were trying to match
    print("\n6. Searching for the specific hourly pattern...")
    hourly_pattern = re.compile(r'(\d{1,2}\s*(?:AM|PM|am|pm))\s*(\d+)°\s*(\d+)%\s*(\d+)', re.IGNORECASE)
    matches = hourly_pattern.findall(page_text)
    print(f"Specific hourly pattern matches: {len(matches)}")
    if matches:
        print("  Sample matches:")
        for i, match in enumerate(matches[:5]):
            print(f"    {i+1}: {match}")
    
    # Look for any divs that might contain weather data
    print("\n7. Searching for divs with weather-like content...")
    weather_divs = []
    all_divs = soup.find_all('div')
    
    for div in all_divs:
        div_text = div.get_text().strip()
        # Look for divs that contain time, temperature, and percentage
        if (re.search(r'\d{1,2}\s*(?:AM|PM)', div_text) and 
            re.search(r'\d+°', div_text) and 
            re.search(r'\d+%', div_text)):
            weather_divs.append(div)
    
    print(f"Found {len(weather_divs)} divs with weather-like content")
    for i, div in enumerate(weather_divs[:3]):
        print(f"  Div {i+1}: {div.get_text()[:100]}...")
        print(f"    Classes: {div.get('class', [])}")
    
    # Save a sample of the HTML for manual inspection
    print("\n8. Saving HTML sample for manual inspection...")
    with open('click2houston_sample.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("✅ Saved HTML sample to 'click2houston_sample.html'")

if __name__ == "__main__":
    debug_page_structure() 