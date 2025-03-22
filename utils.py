import logging
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and normalize text for comparison"""
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.lower().split())

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|=IMAGE\("([^"]+)"\)'
    urls = []
    
    try:
        # Find all matches
        matches = re.finditer(url_pattern, text)
        for match in matches:
            # If it's an IMAGE formula, extract the URL from the formula
            if match.group(1):
                urls.append(match.group(1))
            else:
                urls.append(match.group(0))
        
        return urls
    except Exception as e:
        logger.error(f"Error extracting URLs: {e}")
        return []

def format_google_photos_url(url: str) -> str:
    """Format Google Photos URL for public access"""
    try:
        if 'photos.google.com' in url:
            # Remove any existing parameters and add authuser=0
            base_url = url.split('?')[0]
            return f"{base_url}?authuser=0"
        return url
    except Exception as e:
        logger.error(f"Error formatting Google Photos URL: {e}")
        return url

def get_current_time_est() -> str:
    """Get current time in EST timezone"""
    try:
        est = pytz.timezone('US/Eastern')
        return datetime.now(est).strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates"""
    try:
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except Exception:
        return False

def parse_image_formula(formula: str) -> Optional[str]:
    """Parse Google Sheets IMAGE formula and extract URL"""
    try:
        if not formula or not isinstance(formula, str):
            return None
            
        if formula.startswith('=IMAGE("') and formula.endswith('")'):
            url = formula[8:-2]  # Remove =IMAGE(" and ")
            return url
        return None
    except Exception as e:
        logger.error(f"Error parsing IMAGE formula: {e}")
        return None

def format_plant_name(name: str) -> str:
    """Format plant name for display"""
    try:
        # Capitalize first letter of each word
        words = name.split()
        formatted_words = [word.capitalize() for word in words]
        return ' '.join(formatted_words)
    except Exception as e:
        logger.error(f"Error formatting plant name: {e}")
        return name

def get_season() -> str:
    """Get current season based on date"""
    try:
        now = datetime.now()
        month = now.month
        day = now.day
        
        if (month == 3 and day >= 20) or (month == 4) or (month == 5) or (month == 6 and day < 21):
            return "spring"
        elif (month == 6 and day >= 21) or (month == 7) or (month == 8) or (month == 9 and day < 22):
            return "summer"
        elif (month == 9 and day >= 22) or (month == 10) or (month == 11) or (month == 12 and day < 21):
            return "fall"
        else:
            return "winter"
    except Exception as e:
        logger.error(f"Error getting season: {e}")
        return "unknown"

def get_seasonal_tasks(season: str) -> List[str]:
    """Get seasonal gardening tasks"""
    tasks = {
        "spring": [
            "Start seeds indoors",
            "Clean up garden beds",
            "Prune winter damage",
            "Prepare soil for planting",
            "Plant cold-hardy vegetables"
        ],
        "summer": [
            "Regular watering",
            "Mulch to retain moisture",
            "Monitor for pests",
            "Harvest vegetables",
            "Deadhead flowers"
        ],
        "fall": [
            "Clean up dead plants",
            "Plant spring bulbs",
            "Mulch for winter protection",
            "Collect seeds",
            "Prepare compost"
        ],
        "winter": [
            "Plan next year's garden",
            "Order seeds",
            "Maintain tools",
            "Monitor winter protection",
            "Start indoor herbs"
        ]
    }
    return tasks.get(season.lower(), ["No specific tasks for this season"])

def format_list_for_display(items: List[str], bullet: str = "•") -> str:
    """Format a list of items for display"""
    try:
        if not items:
            return ""
        return "\n".join(f"{bullet} {item}" for item in items)
    except Exception as e:
        logger.error(f"Error formatting list: {e}")
        return str(items)

def parse_location_string(location: str) -> Set[str]:
    """Parse location string into set of normalized location names"""
    try:
        if not location:
            return set()
            
        # Split on commas and clean each location
        locations = {
            clean_text(loc)
            for loc in location.split(',')
            if clean_text(loc)
        }
        return locations
    except Exception as e:
        logger.error(f"Error parsing location string: {e}")
        return set()

def format_date_for_sheet(date: datetime) -> str:
    """Format date for Google Sheets"""
    try:
        return date.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return str(date) 