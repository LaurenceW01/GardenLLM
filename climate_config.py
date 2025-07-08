"""
Centralized climate configuration for GardenLLM.
Defines all climate parameters with Houston, TX, USA as the default location.
Provides functions to retrieve climate context for prompts and logic.
Every line is documented inline.
"""

from typing import Dict, Optional

# Default climate location (Houston, TX, USA)
DEFAULT_LOCATION = "Houston, TX, USA"

# Climate parameters for Houston, TX, USA (default location)
HOUSTON_CLIMATE = {
    # Hardiness zone information
    'hardiness_zone': '9a/9b',
    'zone_description': 'Zone 9a/9b specific advice',
    
    # Temperature ranges throughout the year
    'summer_highs': '90-100°F (32-38°C)',
    'winter_lows': '30-40°F (-1-4°C)',
    'temperature_description': 'Hot and humid subtropical climate with mild winters',
    
    # Humidity levels
    'humidity': '60-80%',
    'humidity_description': 'High humidity considerations',
    
    # Rainfall patterns
    'annual_rainfall': '50+ inches',
    'rainfall_pattern': 'Heavy spring/fall rains',
    'rainfall_description': '50+ inches annually, heavy spring/fall rains',
    
    # Soil conditions
    'soil_type': 'Clay soil',
    'soil_ph': '7.0-8.0',
    'soil_description': 'Clay soil, alkaline pH (7.0-8.0)',
    
    # Growing seasons
    'spring_season': 'February-May',
    'fall_season': 'September-November',
    'summer_avoidance': 'Avoid peak summer heat',
    'growing_seasons_description': 'Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat',
    
    # Frost and freeze information
    'frost_dates': 'Late November to early March',
    'freeze_frequency': 'Occasional freezes',
    'frost_description': 'Occasional freezes, protect sensitive plants',
    
    # General climate summary
    'climate_summary': 'Hot and humid subtropical climate with mild winters, high humidity, and clay soil',
}

# Function to get the default climate location
def get_default_location() -> str:
    """Return the default climate location (Houston, TX, USA)."""
    return DEFAULT_LOCATION

# Function to get all climate parameters for a location (currently only Houston supported)
def get_climate_params(location: Optional[str] = None) -> Dict[str, str]:
    """
    Get climate parameters for the specified location.
    Currently only supports Houston, TX, USA (default).
    
    Args:
        location (Optional[str]): Location to get climate for. If None, uses default.
    
    Returns:
        Dict[str, str]: Climate parameters for the location
    """
    # For now, only Houston is supported
    # In the future, this could be expanded to support other locations
    if location is None:
        location = DEFAULT_LOCATION
    
    # Normalize location for comparison
    location_lower = location.lower().strip()
    houston_variations = [
        'houston, tx, usa',
        'houston, tx',
        'houston, texas, usa',
        'houston, texas',
        'houston',
        'houston tx',
        'houston texas'
    ]
    
    # Check if the location is a Houston variation
    if location_lower in houston_variations:
        return HOUSTON_CLIMATE.copy()
    else:
        # For now, return Houston climate as default
        # In the future, this could return climate for other locations
        return HOUSTON_CLIMATE.copy()

# Function to get climate context for AI prompts
def get_climate_context(location: Optional[str] = None) -> str:
    """
    Get formatted climate context for use in AI prompts.
    
    Args:
        location (Optional[str]): Location to get climate context for. If None, uses default.
    
    Returns:
        str: Formatted climate context string
    """
    # Get climate parameters for the location
    climate = get_climate_params(location)
    
    # Build the climate context string
    context_parts = [
        f"Location: {location or DEFAULT_LOCATION}",
        f"Climate: {climate['temperature_description']}",
        f"Growing season: {climate['growing_seasons_description']}",
        f"Hardiness Zone: {climate['hardiness_zone']}",
        f"Temperature Range: Summer {climate['summer_highs']}, Winter {climate['winter_lows']}",
        f"Humidity: {climate['humidity']}",
        f"Rainfall: {climate['rainfall_description']}",
        f"Soil: {climate['soil_description']}",
        f"Frost: {climate['frost_description']}"
    ]
    
    return "\n".join(context_parts)

# Function to get specific climate parameter
def get_climate_param(param_name: str, location: Optional[str] = None) -> Optional[str]:
    """
    Get a specific climate parameter for the location.
    
    Args:
        param_name (str): Name of the climate parameter to retrieve
        location (Optional[str]): Location to get parameter for. If None, uses default.
    
    Returns:
        Optional[str]: The climate parameter value, or None if not found
    """
    # Get climate parameters for the location
    climate = get_climate_params(location)
    
    # Return the specific parameter
    return climate.get(param_name)

# Function to get hardiness zone for a location
def get_hardiness_zone(location: Optional[str] = None) -> str:
    """
    Get the hardiness zone for the specified location.
    
    Args:
        location (Optional[str]): Location to get hardiness zone for. If None, uses default.
    
    Returns:
        str: Hardiness zone for the location
    """
    return get_climate_param('hardiness_zone', location) or '9a/9b'

# Function to get growing seasons for a location
def get_growing_seasons(location: Optional[str] = None) -> str:
    """
    Get the growing seasons for the specified location.
    
    Args:
        location (Optional[str]): Location to get growing seasons for. If None, uses default.
    
    Returns:
        str: Growing seasons description for the location
    """
    return get_climate_param('growing_seasons_description', location) or 'Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat'

# Function to get soil information for a location
def get_soil_info(location: Optional[str] = None) -> str:
    """
    Get soil information for the specified location.
    
    Args:
        location (Optional[str]): Location to get soil info for. If None, uses default.
    
    Returns:
        str: Soil information for the location
    """
    return get_climate_param('soil_description', location) or 'Clay soil, alkaline pH (7.0-8.0)'

# Function to check if a location is supported
def is_location_supported(location: str) -> bool:
    """
    Check if climate data is available for the specified location.
    
    Args:
        location (str): Location to check
    
    Returns:
        bool: True if location is supported, False otherwise
    """
    # Normalize location for comparison
    location_lower = location.lower().strip()
    houston_variations = [
        'houston, tx, usa',
        'houston, tx',
        'houston, texas, usa',
        'houston, texas',
        'houston',
        'houston tx',
        'houston texas'
    ]
    
    return location_lower in houston_variations

# Function to get all supported locations
def get_supported_locations() -> list:
    """
    Get a list of all supported climate locations.
    
    Returns:
        list: List of supported location names
    """
    return [
        'Houston, TX, USA',
        'Houston, TX',
        'Houston, Texas, USA',
        'Houston, Texas',
        'Houston'
    ] 