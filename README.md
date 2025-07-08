# GardenLLM

A comprehensive gardening assistant that helps you manage your garden with AI-powered plant care advice, weather integration, and database management.

## Features

- **AI-Powered Plant Care**: Get personalized care advice for your plants
- **Weather Integration**: Receive weather-aware gardening recommendations
- **Database Management**: Track your plants with Google Sheets integration
- **Image Analysis**: Analyze plant photos for identification and care advice
- **Houston Climate Focus**: Optimized for Houston, Texas growing conditions

## Database Configuration

### Field Configuration
All database field names and mappings are centrally configured in `field_config.py`. This module serves as the single source of truth for:
- Database field names (matching Google Sheet columns)
- User-friendly field aliases
- Field categories (basic info, care, media, metadata)
- Field validation and mapping functions

**Usage:**
```python
from field_config import get_canonical_field_name, is_valid_field

# Get canonical field name from alias
field_name = get_canonical_field_name('name')  # Returns 'Plant Name'

# Validate field
is_valid = is_valid_field('location')  # Returns True
```

### Database Schema
The system uses a Google Sheet with 17 columns:
- ID, Plant Name, Description, Location
- Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences
- Pruning Instructions, Mulching Needs, Fertilizing Schedule
- Winterizing Instructions, Spacing Requirements, Care Notes
- Photo URL, Raw Photo URL, Last Updated

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the application: `python run_server.py`

## Usage

Start the web interface and interact with your garden assistant through the chat interface. The system supports natural language queries about your plants and provides AI-powered care advice.

## Testing

Run tests with:
```bash
python tests/test_field_config.py  # Field configuration tests
```

## Contributing

Please follow the existing code style and ensure all changes preserve existing functionality. 