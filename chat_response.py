import logging
from typing import List, Dict, Optional
import re
from plant_operations import get_plant_data, find_plant_by_id_or_name, update_plant_field
from config import openai_client

logger = logging.getLogger(__name__)

def extract_search_terms(message: str) -> Optional[str]:
    """Extract plant names from the message using basic pattern matching"""
    # Check for general plant list queries
    general_patterns = [
        r'what plants',
        r'list of plants',
        r'all plants',
        r'which plants',
        r'show all plants',
        r'tell me about the plants'
    ]
    
    # Check for location queries
    location_patterns = [
        r'where (?:is|are) (?:the\s+)?([a-zA-Z\s]+)',
        r'location of (?:the\s+)?([a-zA-Z\s]+)',
        r'where can i find (?:the\s+)?([a-zA-Z\s]+)'
    ]
    
    msg_lower = message.lower()
    
    # Return None with a special flag for general plant queries
    if any(pattern in msg_lower for pattern in general_patterns):
        return '*'
    
    # Check location patterns first
    for pattern in location_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return match.group(1).strip()
        
    # Common patterns for specific plant queries
    patterns = [
        r'about\s+(?:the\s+)?([a-zA-Z\s]+\b)',
        r'how\s+(?:do\s+)?(?:I\s+)?(?:grow|care\s+for|plant|maintain)\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'show\s+me\s+(?:the\s+)?([a-zA-Z\s]+\b)',
        r'what\s+does\s+(?:a\s+)?([a-zA-Z\s]+)\s+look\s+like',
        r'picture\s+of\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'photo\s+of\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'^([a-zA-Z\s]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return match.group(1).strip()
    return None

def parse_update_command(message: str) -> Optional[Dict]:
    """Parse update plant commands - supports multiple field updates"""
    msg_lower = message.lower()
    
    # Check if this is an update command
    if not msg_lower.startswith('update plant '):
        return None
    
    try:
        # Extract the command parts after "update plant"
        command_parts = message[len('update plant '):].strip()
        
        # Find the plant identifier (first part before any field keyword)
        field_keywords = ['location', 'url', 'photo url', 'raw photo url', 'description', 'light requirements', 'frost tolerance', 
                         'watering needs', 'soil preferences', 'pruning instructions', 'mulching needs',
                         'fertilizing schedule', 'winterizing instructions', 'spacing requirements', 'care notes']
        
        # Find the first field keyword to identify plant identifier
        first_field_index = -1
        first_field = None
        
        for field in field_keywords:
            index = command_parts.lower().find(field)
            if index != -1 and (first_field_index == -1 or index < first_field_index):
                first_field_index = index
                first_field = field
        
        if first_field_index == -1:
            return None
        
        # Extract plant identifier (everything before the first field)
        plant_identifier = command_parts[:first_field_index].strip()
        
        if not plant_identifier:
            return None
        
        # Parse all field updates in the command
        updates = []
        remaining_command = command_parts[first_field_index:].strip()
        
        while remaining_command:
            # Find the next field keyword
            next_field_index = -1
            next_field = None
            
            for field in field_keywords:
                index = remaining_command.lower().find(field)
                if index != -1 and (next_field_index == -1 or index < next_field_index):
                    next_field_index = index
                    next_field = field
            
            if next_field_index == -1:
                break
            
            # Find the end of this field's value (start of next field or end of command)
            field_start = next_field_index
            field_end = field_start + len(next_field) if next_field else field_start
            
            # Find the next field to determine where this field's value ends
            next_field_start = -1
            for field in field_keywords:
                if field != next_field:  # Don't match the same field
                    index = remaining_command.lower().find(field, field_end)
                    if index != -1 and (next_field_start == -1 or index < next_field_start):
                        next_field_start = index
            
            # Extract the value for this field
            if next_field_start != -1:
                field_value = remaining_command[field_end:next_field_start].strip()
                remaining_command = remaining_command[next_field_start:].strip()
            else:
                field_value = remaining_command[field_end:].strip()
                remaining_command = ""
            
            if field_value:
                updates.append({
                    'field': next_field,
                    'value': field_value
                })
        
        if not updates:
            return None
        
        # Map user-friendly field names to actual database field names
        field_mapping = {
            'location': 'Location',
            'url': 'Photo URL',  # Alias for photo url
            'photo url': 'Photo URL',
            'raw photo url': 'Raw Photo URL',
            'description': 'Description',
            'light requirements': 'Light Requirements',
            'frost tolerance': 'Frost Tolerance',
            'watering needs': 'Watering Needs',
            'soil preferences': 'Soil Preferences',
            'pruning instructions': 'Pruning Instructions',
            'mulching needs': 'Mulching Needs',
            'fertilizing schedule': 'Fertilizing Schedule',
            'winterizing instructions': 'Winterizing Instructions',
            'spacing requirements': 'Spacing Requirements',
            'care notes': 'Care Notes'
        }
        
        # Convert updates to use actual field names
        actual_updates = []
        for update in updates:
            actual_field_name = field_mapping.get(update['field'].lower(), update['field'].title())
            actual_updates.append({
                'field_name': actual_field_name,
                'new_value': update['value']
            })
        
        return {
            'plant_identifier': plant_identifier,
            'updates': actual_updates
        }
        
    except Exception as e:
        logger.error(f"Error parsing update command: {e}")
        return None

def get_chat_response(message: str) -> str:
    """Generate a chat response based on the user's message"""
    logger.info(f"Processing message: {message}")
    
    try:
        # Check for update commands first
        update_data = parse_update_command(message)
        if update_data:
            try:
                # Find the plant by ID or name
                plant_row, plant_data = find_plant_by_id_or_name(update_data['plant_identifier'])
                
                if plant_row is None:
                    return f"Plant '{update_data['plant_identifier']}' not found. Please check the plant name or ID and try again."
                
                # Process multiple updates
                results = []
                plant_name = plant_data[1] if plant_data and len(plant_data) > 1 else update_data['plant_identifier']
                
                for update in update_data['updates']:
                    success = update_plant_field(plant_row, update['field_name'], update['new_value'])
                    
                    if success:
                        results.append(f"Successfully updated {update['field_name']} to: {update['new_value']}")
                    else:
                        results.append(f"Failed to update {update['field_name']}")
                
                return f"Updates for {plant_name}:\n" + "\n".join(results)
                    
            except Exception as e:
                logger.error(f"Error processing update command: {e}")
                return f"Error processing update command: {str(e)}"
        
        msg_lower = message.lower()
        search_term = extract_search_terms(message)
        logger.info(f"Extracted search term: {search_term}")
        
        # Handle image-related queries
        is_image_query = any(pattern in msg_lower for pattern in ['look like', 'show me', 'picture of', 'photo of'])
        # Handle location queries
        is_location_query = any(pattern in msg_lower for pattern in ['where is', 'where are', 'location of', 'where can i find'])
        
        # Special handling for general plant list query
        if search_term == '*':
            try:
                # Get all plants
                plant_data = get_plant_data([])  # Empty list should return all plants
                logger.info(f"Retrieved data for all plants, count: {len(plant_data) if isinstance(plant_data, list) else 'error'}")
                
                if not isinstance(plant_data, list):
                    return "I encountered an error while retrieving the plant list. Please try again."
                
                if not plant_data:
                    return "There are currently no plants in the database."
                
                # Generate response using OpenAI
                plant_names = [plant.get('Plant Name', '') for plant in plant_data if plant.get('Plant Name')]
                plant_names_str = ", ".join(plant_names)
                
                prompt = f"The following plants are in the garden: {plant_names_str}. Please provide a natural, conversational response listing these plants and mentioning that these are the plants currently in the database."
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful gardening assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                return response.choices[0].message.content or "No response generated"
                
            except Exception as e:
                logger.error(f"Error handling general plant query: {e}", exc_info=True)
                # Fallback to simple list if OpenAI fails
                plant_names = [plant.get('Plant Name', '') for plant in plant_data if plant.get('Plant Name')]
                return "Here are the plants currently in the database:\n\n" + "\n".join(f"- {name}" for name in plant_names)
        
        if search_term:
            plant_data = get_plant_data([search_term])
            logger.info(f"Retrieved plant data for query: {plant_data}")
            
            if isinstance(plant_data, str):  # Error message
                return plant_data
            
            if not plant_data:
                return f"I couldn't find any plants matching '{search_term}' in the database."
            
            # Log available data for debugging
            for plant in plant_data:
                logger.info(f"Plant data - Name: {plant.get('Plant Name')}")
                logger.info(f"Photo URL: {plant.get('Photo URL')}")
                logger.info(f"Raw Photo URL: {plant.get('Raw Photo URL')}")
            
            # Handle location queries
            if is_location_query:
                response_parts = []
                for plant in plant_data:
                    plant_name = plant.get('Plant Name', '')
                    location = plant.get('Location', '')
                    if location:
                        response_parts.append(f"The {plant_name} is located in the {location}.")
                    else:
                        response_parts.append(f"I found {plant_name}, but its location is not specified.")
                
                # Add photos to location responses if available
                for plant in plant_data:
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    if raw_photo_url:
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        response_parts.append(f"\nYou can see a photo of the {plant['Plant Name']} here: {raw_photo_url}")
                
                return "\n".join(response_parts)
            
            # Handle image queries
            if is_image_query:
                response_parts = []
                for plant in plant_data:
                    plant_name = plant.get('Plant Name', '')
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    logger.info(f"Processing image query for {plant_name} - Raw Photo URL: {raw_photo_url}")
                    
                    if raw_photo_url:
                        # Format Google Photos URL if needed
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        response_parts.append(f"Here's what {plant_name} looks like:\n{raw_photo_url}")
                    else:
                        response_parts.append(f"I found {plant_name}, but there's no photo available.")
                
                return "\n\n".join(response_parts)
            
            # Handle general information queries
            try:
                # Generate response using OpenAI
                plant_info = []
                for plant in plant_data:
                    # Exclude photo URLs from the OpenAI prompt
                    info = {k: v for k, v in plant.items() if v and k not in ['Photo URL', 'Raw Photo URL']}
                    plant_info.append(info)
                
                prompt = f"Please provide information about the following plants in a natural, conversational way. Focus on the most relevant details for a gardener. Plant data: {plant_info}"
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful gardening assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                chat_response = response.choices[0].message.content or ""
                
                # Add photo URLs to the response if available
                for plant in plant_data:
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    if raw_photo_url:
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        chat_response += f"\n\nYou can see a photo of {plant.get('Plant Name', 'Unknown Plant')} here: {raw_photo_url}"
                
                return chat_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                # Fallback to basic response if API fails
                return "\n\n".join([f"Here's what I know about {plant.get('Plant Name')}:\n" + 
                                  "\n".join([f"{k}: {v}" for k, v in plant.items() if v and k not in ['Photo URL', 'Raw Photo URL']])
                                  for plant in plant_data])
        
        return "I'm not sure what you're asking about. Could you please rephrase your question or specify a plant name?"
        
    except Exception as e:
        logger.error(f"Error generating chat response: {e}", exc_info=True)
        return "Sorry, there was an error processing your request. Please try again." 