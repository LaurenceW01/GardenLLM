import logging
import re
from typing import List, Dict, Optional
from config import openai_client
from plant_operations import get_plant_data

logger = logging.getLogger(__name__)

# Stop words for search term filtering
stop_words = {'what', 'does', 'do', 'a', 'an', 'the', 'show', 'me', 'pictures', 'picture', 'photos', 'photo', 'of', 'look', 'like', 'in', 'my', 'garden', 'tell', 'about', 'can', 'you', 'describe', 'how', 'is', 'are', 'there', 'any', 'some', 'have', 'has', 'with', 'without', 'and', 'or', 'but', 'for', 'to', 'at', 'by', 'up', 'down', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'}

def extract_search_terms(message: str) -> str:
    """Extract search terms from the user's message"""
    print("\n=== DEBUG: Query Analysis ===")
    msg_lower = message.lower()
    print(f"Original message (lowercase): {msg_lower}")
    
    # Check for image-related patterns
    is_image_query = any(pattern in msg_lower for pattern in ['look like', 'show me', 'picture of', 'photo of'])
    print(f"Is image query: {is_image_query}")
    
    # Extract search text based on patterns
    search_text = ""
    if 'look like' in msg_lower:
        search_text = msg_lower.split('look like')[0]
        print(f"Found 'look like' pattern. Initial search text: {repr(search_text)}")
    elif any(pattern in msg_lower for pattern in ['show me', 'picture of', 'photo of']):
        for pattern in ['show me', 'picture of', 'photo of']:
            if pattern in msg_lower:
                search_text = msg_lower.split(pattern)[1]
                print(f"Found '{pattern}' pattern. Initial search text: {repr(search_text)}")
                break
    else:
        search_text = msg_lower
        print(f"No specific pattern found. Using full message: {repr(search_text)}")
    
    # Remove stop words and clean up search terms
    print("\n=== DEBUG: Search Terms Processing ===")
    print(f"Stop words being removed: {stop_words}")
    search_terms = [term.strip() for term in search_text.split() if term.strip() and term.strip() not in stop_words]
    print(f"Terms after stop word removal: {search_terms}")
    
    search_term = ' '.join(search_terms).strip()
    print(f"Final search term: {repr(search_term)}")
    return search_term

def get_chat_response(message: str) -> str:
    """Get a response from the chatbot"""
    try:
        # First check if this is an image-specific query
        msg_lower = message.lower()
        is_image_query = any(pattern in msg_lower for pattern in ['look like', 'show me', 'picture of', 'photo of'])
        
        # Extract search terms and get plant data
        search_term = extract_search_terms(message)
        if not search_term:
            return "I couldn't identify which plant you're asking about. Could you please specify the plant name?"
        
        plant_data = get_plant_data([search_term])
        if not plant_data or not isinstance(plant_data, list):
            return f"I couldn't find any information about '{search_term}'. Could you please check the plant name and try again?"
        
        # Handle image-specific queries differently
        if is_image_query:
            response_parts = []
            for plant in plant_data:
                plant_name = plant.get('Plant Name', '')
                raw_photo_url = plant.get('Raw Photo URL', '')
                
                if raw_photo_url:
                    # Format Google Photos URLs for public access if needed
                    if 'photos.google.com' in raw_photo_url:
                        # Remove any parameters and add authuser=0 for public access
                        raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                    response_parts.append(f"Here's what {plant_name} looks like:\n{raw_photo_url}")
                else:
                    response_parts.append(f"I found {plant_name}, but there's no photo available.")
            
            return "\n\n".join(response_parts)
        
        # For non-image queries, provide detailed information with photos as supplementary
        formatted_data = []
        for plant in plant_data:
            # Create a copy of plant data without photo URLs
            plant_info = {k: v for k, v in plant.items() if k not in ['Photo URL', 'Raw Photo URL']}
            formatted_data.append(plant_info)
        
        # Create the prompt
        prompt = f"Based on this plant data: {formatted_data}\n\nPlease answer this question about the plant(s): {message}"
        
        # Get response from OpenAI
        response = get_openai_response(prompt)
        
        # Add photo information if available
        photo_info = []
        for plant in plant_data:
            raw_photo_url = plant.get('Raw Photo URL', '')
            if raw_photo_url:
                # Format Google Photos URLs for public access if needed
                if 'photos.google.com' in raw_photo_url:
                    # Remove any parameters and add authuser=0 for public access
                    raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                photo_info.append(f"\n\nYou can also see a photo of {plant['Plant Name']} here: {raw_photo_url}")
        
        if photo_info:
            response += ''.join(photo_info)
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting chat response: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."

def get_openai_response(prompt: str) -> str:
    """Get a response from OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable gardening assistant. Provide helpful, accurate information about plants in a natural, conversational way."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm sorry, but I couldn't get a response from the OpenAI API. Please try again later." 