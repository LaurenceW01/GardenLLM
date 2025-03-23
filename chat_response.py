import logging
from typing import List, Dict, Optional
import re
from plant_operations import get_plant_data
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

def get_chat_response(message: str) -> str:
    """Generate a chat response based on the user's message"""
    logger.info(f"Processing message: {message}")
    
    try:
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
                
                return response.choices[0].message.content
                
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
                
                chat_response = response.choices[0].message.content
                
                # Add photo URLs to the response if available
                for plant in plant_data:
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    if raw_photo_url:
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        chat_response += f"\n\nYou can see a photo of {plant['Plant Name']} here: {raw_photo_url}"
                
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