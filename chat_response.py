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
    """Generate a chat response based on the user's message"""
    print("\n=== DEBUG: Raw Message ===")
    print(f"Message type: {type(message)}")
    print(f"Raw message: {repr(message)}")
    print("----------------------------------------")
    
    try:
        msg_lower = message.lower()
        search_term = extract_search_terms(message)
        
        # Handle image-related queries
        if any(pattern in msg_lower for pattern in ['look like', 'show me', 'picture of', 'photo of']):
            if not search_term:
                return "I couldn't identify which plant you're asking about. Could you please specify the plant name?"
            
            plant_data = get_plant_data([search_term])
            if isinstance(plant_data, str):  # Error message
                return plant_data
            
            if not plant_data:
                return f"I couldn't find any plants matching '{search_term}' in the database."
            
            response_parts = []
            for plant in plant_data:
                plant_name = plant.get('Plant Name', '')
                photo_url = plant.get('Raw Photo URL', '')  # Use Raw Photo URL field
                
                if photo_url:
                    # Format Google Photos URL if needed
                    if 'photos.google.com' in photo_url:
                        photo_url = photo_url.split('?')[0] + '?authuser=0'
                    response_parts.append(f"Here's what {plant_name} looks like:\n{photo_url}")
                else:
                    response_parts.append(f"I found {plant_name}, but there's no photo available.")
            
            return "\n\n".join(response_parts)
        
        # Handle general plant queries
        if search_term:
            plant_data = get_plant_data([search_term])
            if isinstance(plant_data, str):  # Error message
                return plant_data
            
            if not plant_data:
                return f"I couldn't find any plants matching '{search_term}' in the database."
            
            # Generate response using OpenAI
            plant_info = []
            for plant in plant_data:
                info = {k: v for k, v in plant.items() if v and k not in ['Photo URL', 'Raw Photo URL']}
                plant_info.append(info)
            
            prompt = f"Please provide information about the following plants in a natural, conversational way. Focus on the most relevant details for a gardener. Plant data: {plant_info}"
            
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
                # Fallback to basic response if API fails
                return "\n\n".join([f"Here's what I know about {plant.get('Plant Name')}:\n" + 
                                  "\n".join([f"{k}: {v}" for k, v in plant.items() if v and k not in ['Photo URL', 'Raw Photo URL']])
                                  for plant in plant_data])
        
        return "I'm not sure what you're asking about. Could you please rephrase your question or specify a plant name?"
        
    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        return f"I encountered an error while processing your request: {str(e)}" 