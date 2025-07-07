"""
Query Analyzer Module for GardenLLM

This module provides AI-powered query analysis that extracts plant names and classifies
query types in a single AI call. It integrates with the existing chat response system
to provide enhanced natural language processing capabilities.

Author: GardenLLM Team
Date: December 2024
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from config import openai_client

logger = logging.getLogger(__name__)

# Query type constants for classification
class QueryType:
    """Constants for different query types that can be classified"""
    LOCATION = "LOCATION"      # Where is/are my [plants]?
    PHOTO = "PHOTO"           # Show me/picture of my [plants]
    LIST = "LIST"             # What plants do I have?
    CARE = "CARE"             # How do I care for my [plants]?
    DIAGNOSIS = "DIAGNOSIS"   # Why are my [plants] [symptom]?
    ADVICE = "ADVICE"         # How do I [action] my [plants]?
    GENERAL = "GENERAL"       # General gardening questions

def get_plant_list_from_database() -> List[str]:
    """
    Get the current list of plant names from the database.
    
    This function uses the cached plant list from plant_operations
    to provide efficient access to plant names for query analysis.
    
    Returns:
        List[str]: List of plant names currently in the database
    """
    try:
        # Phase 2: Use the new cached plant list function
        from plant_operations import get_plant_names_from_database
        plant_names = get_plant_names_from_database()
        logger.info(f"Retrieved {len(plant_names)} plant names from database")
        return plant_names
    except ImportError as e:
        logger.error(f"Could not import plant_operations: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting plant list from database: {e}")
        return []

def analyze_query(user_query: str, plant_list: Optional[List[str]] = None) -> Dict:
    """
    Analyze a user query using AI to extract plant references and classify query type.
    
    This function makes a single AI call to:
    1. Extract plant names referenced in the query
    2. Classify the query type (LOCATION, PHOTO, LIST, CARE, DIAGNOSIS, ADVICE, GENERAL)
    
    Args:
        user_query (str): The user's question or request
        plant_list (Optional[List[str]]): List of plant names from database. 
                                        If None, will be fetched from database.
    
    Returns:
        Dict: Analysis result containing:
            - 'plant_references': List of plant names found in query
            - 'query_type': Classified query type
            - 'confidence': Confidence score (0-1)
            - 'requires_ai_response': Boolean indicating if second AI call needed
    """
    logger.info(f"Analyzing query: {user_query}")
    
    try:
        # Get plant list if not provided
        if plant_list is None:
            plant_list = get_plant_list_from_database()
        
        # Create the AI prompt for analysis
        prompt = _build_analysis_prompt(user_query, plant_list)
        
        # Make AI call for analysis
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a gardening assistant that analyzes user queries to extract plant references and classify query types."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=200
        )
        
        # Parse the AI response
        ai_response_content = response.choices[0].message.content
        if ai_response_content is None:
            raise ValueError("AI response content is None")
        analysis_result = _parse_analysis_response(ai_response_content)
        
        # Add metadata
        analysis_result['original_query'] = user_query
        analysis_result['plant_list_provided'] = len(plant_list) if plant_list else 0
        
        # Determine if second AI call is required
        analysis_result['requires_ai_response'] = analysis_result['query_type'] in [
            QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL
        ]
        
        logger.info(f"Query analysis result: {analysis_result}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        # Return fallback analysis
        return _get_fallback_analysis(user_query)

def _build_analysis_prompt(user_query: str, plant_list: List[str]) -> str:
    """
    Build the AI prompt for query analysis.
    
    Args:
        user_query (str): The user's query
        plant_list (List[str]): List of plant names from database
    
    Returns:
        str: Formatted prompt for AI analysis
    """
    plant_list_text = ", ".join(plant_list) if plant_list else "No plants in database"
    
    prompt = f"""
Analyze the following user query and provide a JSON response with the following structure:

{{
    "plant_references": ["list", "of", "plant", "names", "referenced"],
    "query_type": "CLASSIFICATION",
    "confidence": 0.95,
    "reasoning": "brief explanation of classification"
}}

Query Types:
- LOCATION: Questions about where plants are located (e.g., "Where are my tomatoes?")
- PHOTO: Requests for plant photos (e.g., "Show me my roses")
- LIST: Requests to list all plants (e.g., "What plants do I have?")
- CARE: Questions about plant care (e.g., "How do I water my basil?")
- DIAGNOSIS: Questions about plant problems (e.g., "Why are my leaves yellow?")
- ADVICE: Requests for gardening advice (e.g., "How do I prune my roses?")
- GENERAL: General gardening questions not about specific plants

Available plants in database: {plant_list_text}

User query: "{user_query}"

Respond with ONLY the JSON object, no additional text.
"""
    return prompt

def _parse_analysis_response(ai_response: str) -> Dict:
    """
    Parse the AI response into a structured analysis result.
    
    Args:
        ai_response (str): Raw response from AI
    
    Returns:
        Dict: Parsed analysis result
    """
    try:
        # Clean the response and extract JSON
        cleaned_response = ai_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        # Parse JSON
        result = json.loads(cleaned_response.strip())
        
        # Validate required fields
        required_fields = ['plant_references', 'query_type', 'confidence']
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing required field '{field}' in AI response")
                result[field] = [] if field == 'plant_references' else 'GENERAL' if field == 'query_type' else 0.5
        
        # Ensure plant_references is a list
        if not isinstance(result['plant_references'], list):
            result['plant_references'] = []
        
        # Validate query type
        valid_types = [QueryType.LOCATION, QueryType.PHOTO, QueryType.LIST, 
                      QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL]
        if result['query_type'] not in valid_types:
            logger.warning(f"Invalid query type '{result['query_type']}', defaulting to GENERAL")
            result['query_type'] = QueryType.GENERAL
        
        # Ensure confidence is a number between 0 and 1
        try:
            confidence = float(result['confidence'])
            result['confidence'] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            result['confidence'] = 0.5
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"Raw response: {ai_response}")
        return _get_fallback_analysis("")

def _get_fallback_analysis(user_query: str) -> Dict:
    """
    Provide fallback analysis when AI analysis fails.
    
    Args:
        user_query (str): The user's query
    
    Returns:
        Dict: Fallback analysis result
    """
    logger.warning("Using fallback analysis due to AI analysis failure")
    
    # Simple fallback logic
    query_lower = user_query.lower()
    
    # Check for list queries
    if any(word in query_lower for word in ['what plants', 'list', 'all plants', 'which plants']):
        return {
            'plant_references': [],
            'query_type': QueryType.LIST,
            'confidence': 0.7,
            'reasoning': 'Fallback: detected list-related keywords',
            'requires_ai_response': False,
            'original_query': user_query,
            'plant_list_provided': 0
        }
    
    # Check for location queries
    if any(word in query_lower for word in ['where', 'location']):
        return {
            'plant_references': [],
            'query_type': QueryType.LOCATION,
            'confidence': 0.6,
            'reasoning': 'Fallback: detected location-related keywords',
            'requires_ai_response': False,
            'original_query': user_query,
            'plant_list_provided': 0
        }
    
    # Check for photo queries
    if any(word in query_lower for word in ['show me', 'picture', 'photo', 'see']):
        return {
            'plant_references': [],
            'query_type': QueryType.PHOTO,
            'confidence': 0.6,
            'reasoning': 'Fallback: detected photo-related keywords',
            'requires_ai_response': False,
            'original_query': user_query,
            'plant_list_provided': 0
        }
    
    # Default to general query
    return {
        'plant_references': [],
        'query_type': QueryType.GENERAL,
        'confidence': 0.5,
        'reasoning': 'Fallback: defaulting to general query',
        'requires_ai_response': True,
        'original_query': user_query,
        'plant_list_provided': 0
    }

def is_database_only_query(query_type: str) -> bool:
    """
    Determine if a query type can be answered using only the database.
    
    Args:
        query_type (str): The classified query type
    
    Returns:
        bool: True if query can be answered from database only
    """
    return query_type in [QueryType.LOCATION, QueryType.PHOTO, QueryType.LIST]

def is_ai_response_required(query_type: str) -> bool:
    """
    Determine if a query type requires a second AI call for response.
    
    Args:
        query_type (str): The classified query type
    
    Returns:
        bool: True if query requires second AI call
    """
    return query_type in [QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL]

# Test function for development
def test_query_analysis():
    """
    Test function to validate query analysis functionality.
    This will be replaced with proper unit tests in the testing phase.
    """
    test_queries = [
        "Where are my tomatoes?",
        "Show me my roses",
        "What plants do I have?",
        "How do I water my basil?",
        "Why are my leaves turning yellow?",
        "How do I prune my roses?",
        "What should I plant in spring?"
    ]
    
    print("Testing Query Analysis:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = analyze_query(query)
        print(f"Plant References: {result['plant_references']}")
        print(f"Query Type: {result['query_type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Requires AI Response: {result['requires_ai_response']}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")

if __name__ == "__main__":
    # Run test if module is executed directly
    test_query_analysis() 