#!/usr/bin/env python3
"""
Simple test to check if Selenium can load Click2Houston page
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_page_load():
    """Simple test to see if we can load the page"""
    print("Testing basic page load...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Increase timeout
    chrome_options.add_argument("--timeout=60000")
    
    try:
        print("Initializing webdriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)  # 60 second timeout
        
        print("Loading page...")
        driver.get("https://www.click2houston.com/weather/")
        
        print("Page loaded successfully!")
        print(f"Title: {driver.title}")
        print(f"URL: {driver.current_url}")
        
        # Wait a bit for content to load
        time.sleep(5)
        
        # Get page source length
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)} characters")
        
        # Look for weather-related content
        if "weather" in page_source.lower():
            print("✅ Weather content found in page source")
        else:
            print("❌ No weather content found in page source")
        
        # Look for hourline elements
        hourline_elements = driver.find_elements("class name", "hourline")
        print(f"Found {len(hourline_elements)} hourline elements")
        
        # Look for any elements with temperature
        temp_elements = driver.find_elements("xpath", "//*[contains(text(), '°')]")
        print(f"Found {len(temp_elements)} elements with temperature symbols")
        
        if temp_elements:
            print("Sample temperature elements:")
            for i, elem in enumerate(temp_elements[:3]):
                print(f"  {i+1}. {elem.text}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    test_page_load() 