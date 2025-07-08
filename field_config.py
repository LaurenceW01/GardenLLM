"""
Centralized field configuration for GardenLLM.
Defines all database field names, user-friendly aliases, field categories, and provides mapping/validation functions.
Every line is documented inline.
"""

from typing import Optional

# List of all database field names as they appear in the Google Sheet
FIELD_NAMES = [
    # Unique identifier for each plant
    'ID',
    # The name of the plant (required field)
    'Plant Name',
    # Description of the plant
    'Description',
    # Location(s) of the plant in the garden
    'Location',
    # Light requirements for the plant
    'Light Requirements',
    # Frost tolerance information
    'Frost Tolerance',
    # Watering needs for the plant
    'Watering Needs',
    # Soil preferences for the plant
    'Soil Preferences',
    # Pruning instructions for the plant
    'Pruning Instructions',
    # Mulching needs for the plant
    'Mulching Needs',
    # Fertilizing schedule for the plant
    'Fertilizing Schedule',
    # Winterizing instructions for the plant
    'Winterizing Instructions',
    # Spacing requirements for the plant
    'Spacing Requirements',
    # Additional care notes
    'Care Notes',
    # Photo URL (as an IMAGE formula in the sheet)
    'Photo URL',
    # Raw Photo URL (direct link to the image)
    'Raw Photo URL',
    # Last updated timestamp
    'Last Updated',
]

# User-friendly aliases for each field (all lowercased for matching)
FIELD_ALIASES = {
    # ID field aliases
    'id': 'ID',
    'identifier': 'ID',
    # Plant Name field aliases
    'name': 'Plant Name',
    'plant': 'Plant Name',
    'plant name': 'Plant Name',
    # Description field aliases
    'desc': 'Description',
    'description': 'Description',
    # Location field aliases
    'location': 'Location',
    'where': 'Location',
    'place': 'Location',
    # Light Requirements field aliases
    'light': 'Light Requirements',
    'light requirements': 'Light Requirements',
    'sun': 'Light Requirements',
    'sunlight': 'Light Requirements',
    # Frost Tolerance field aliases
    'frost': 'Frost Tolerance',
    'frost tolerance': 'Frost Tolerance',
    'cold': 'Frost Tolerance',
    'temperature': 'Frost Tolerance',
    # Watering Needs field aliases
    'water': 'Watering Needs',
    'watering': 'Watering Needs',
    'watering needs': 'Watering Needs',
    # Soil Preferences field aliases
    'soil': 'Soil Preferences',
    'soil preferences': 'Soil Preferences',
    # Pruning Instructions field aliases
    'prune': 'Pruning Instructions',
    'pruning': 'Pruning Instructions',
    'pruning instructions': 'Pruning Instructions',
    # Mulching Needs field aliases
    'mulch': 'Mulching Needs',
    'mulching': 'Mulching Needs',
    'mulching needs': 'Mulching Needs',
    # Fertilizing Schedule field aliases
    'fertilize': 'Fertilizing Schedule',
    'fertilizing': 'Fertilizing Schedule',
    'fertilizing schedule': 'Fertilizing Schedule',
    # Winterizing Instructions field aliases
    'winter': 'Winterizing Instructions',
    'winterizing': 'Winterizing Instructions',
    'winterizing instructions': 'Winterizing Instructions',
    'winter care': 'Winterizing Instructions',
    # Spacing Requirements field aliases
    'spacing': 'Spacing Requirements',
    'spacing requirements': 'Spacing Requirements',
    # Care Notes field aliases
    'notes': 'Care Notes',
    'care notes': 'Care Notes',
    # Photo URL field aliases
    'photo': 'Photo URL',
    'photo url': 'Photo URL',
    'image': 'Photo URL',
    'picture': 'Photo URL',
    'url': 'Photo URL',
    # Raw Photo URL field aliases
    'raw photo url': 'Raw Photo URL',
    'direct photo url': 'Raw Photo URL',
    'image url': 'Raw Photo URL',
    # Last Updated field aliases
    'last updated': 'Last Updated',
    'updated': 'Last Updated',
}

# Field categories for organization and validation
FIELD_CATEGORIES = {
    # Basic information fields
    'basic': [
        'ID',
        'Plant Name',
        'Description',
        'Location',
    ],
    # Care requirement fields
    'care': [
        'Light Requirements',
        'Frost Tolerance',
        'Watering Needs',
        'Soil Preferences',
        'Pruning Instructions',
        'Mulching Needs',
        'Fertilizing Schedule',
        'Winterizing Instructions',
        'Spacing Requirements',
        'Care Notes',
    ],
    # Media fields
    'media': [
        'Photo URL',
        'Raw Photo URL',
    ],
    # Metadata fields
    'metadata': [
        'Last Updated',
    ],
}

# Function to get the canonical field name from an alias
# Returns the canonical field name if found, else None
def get_canonical_field_name(alias: str) -> Optional[str]:
    """Return the canonical field name for a given alias (case-insensitive), or None if not found."""
    # Lowercase the alias for matching
    alias_lc = alias.strip().lower()
    # Check if alias is a direct field name
    if alias_lc in (name.lower() for name in FIELD_NAMES):
        # Return the properly cased field name
        for name in FIELD_NAMES:
            if name.lower() == alias_lc:
                return name
    # Check if alias is in the alias mapping
    return FIELD_ALIASES.get(alias_lc)

# Function to validate if a field name or alias is valid
def is_valid_field(field: str) -> bool:
    """Return True if the field or alias is valid, False otherwise."""
    # Try to get the canonical field name
    return get_canonical_field_name(field) is not None

# Function to get all canonical field names
def get_all_field_names() -> list:
    """Return a list of all canonical field names."""
    return FIELD_NAMES.copy()

# Function to get all aliases for a canonical field name
def get_aliases_for_field(field_name: str) -> list:
    """
    Get all aliases for a given canonical field name.
    
    Args:
        field_name (str): The canonical field name
        
    Returns:
        list: List of aliases for the field
    """
    aliases = []
    for alias, canonical in FIELD_ALIASES.items():
        if canonical == field_name:
            aliases.append(alias)
    return aliases

def get_field_alias(field_name: str) -> str:
    """
    Get the primary user-friendly alias for a given canonical field name.
    
    Args:
        field_name (str): The canonical field name
        
    Returns:
        str: The primary alias for the field, or the field name itself if no alias exists
    """
    # First check if the field name itself is an alias
    if field_name in FIELD_ALIASES:
        return field_name
    
    # Look for aliases that map to this field name
    for alias, canonical in FIELD_ALIASES.items():
        if canonical == field_name:
            return alias
    
    # If no alias found, return the field name itself
    return field_name

# Function to get the category for a field name
def get_field_category(field_name: str) -> Optional[str]:
    """Return the category for a given canonical field name, or None if not found."""
    for category, fields in FIELD_CATEGORIES.items():
        if field_name in fields:
            return category
    return None 