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

# Remove location_references and LOCATION_PLANTS from prompt and fallback
# Only support plant_references and the original query types
# The AI will be used for location matching in a separate call, not as part of the main query analyzer

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
        if plant_list is None:
            plant_list = get_plant_list_from_database()
        prompt = _build_analysis_prompt(user_query, plant_list)
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a gardening assistant that analyzes user queries to extract plant references and classify query types."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        ai_response_content = response.choices[0].message.content
        if ai_response_content is None:
            raise ValueError("AI response content is None")
        analysis_result = _parse_analysis_response(ai_response_content)
        analysis_result['original_query'] = user_query
        analysis_result['plant_list_provided'] = len(plant_list) if plant_list else 0
        analysis_result['requires_ai_response'] = analysis_result['query_type'] in [
            QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL
        ]
        logger.info(f"Query analysis result: {analysis_result}")
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        return _get_fallback_analysis(user_query)

def _build_analysis_prompt(user_query: str, plant_list: List[str]) -> str:
    plant_list_text = _get_smart_plant_list(user_query, plant_list)
    prompt = f"""
You are a gardening assistant that analyzes user queries to extract plant references and classify query types. You have access to the user's garden database.

IMPORTANT PLANT NAME MATCHING RULES:
1. **Generic vs Specific Names**: 
   - If user asks about "roses" (generic), match ALL rose varieties in the database
   - If user asks about "Peggy Martin Rose" (specific), match only that exact variety
   - If user asks about "cherry" from "cherry tomato", do NOT match "cherry tomato" unless they specifically mention "cherry tomato"
2. **Compound Plant Names**:
   - "Peggy Martin Rose" should only match when user asks about "Peggy Martin Rose" or "Peggy Martin"
   - "Cherry Tomato" should only match when user asks about "cherry tomato" or "tomato" (generic)
   - "Basil" should match "Sweet Basil", "Thai Basil", etc. when user asks about "basil" (generic)
3. **Context Matters**:
   - "How do I care for my roses?" → match all rose varieties
   - "Where is my Peggy Martin Rose?" → match only "Peggy Martin Rose"
   - "Show me cherry" → do NOT match "cherry tomato" (too specific)
   - "How do I grow tomatoes?" → match all tomato varieties
Analyze this query and respond with ONLY a JSON object:
{{
    "plant_references": ["exact", "plant", "names", "from", "database"],
    "query_type": "TYPE",
    "confidence": 0.95,
    "reasoning": "brief explanation of matching logic"
}}
Query Types:
- LIST: "What plants do I have?", "Show all plants", "List my plants"
- LOCATION: "Where is my tomato?", "Location of roses"
- PHOTO: "Show me tomato", "Picture of basil", "Photo of roses"
- CARE: "How to water", "Care for plants"
- DIAGNOSIS: "Why yellow leaves", "Plant problems"
- ADVICE: "How to prune", "Gardening tips"
- GENERAL: Other gardening questions
Available plants in database: {plant_list_text}
Query: "{user_query}"
JSON only:
"""
    return prompt

def _get_smart_plant_list(user_query: str, plant_list: List[str]) -> str:
    """
    Get a smart selection of plants for the AI prompt, prioritizing potential matches.
    
    Args:
        user_query (str): The user's query
        plant_list (List[str]): Full list of plant names from database
    
    Returns:
        str: Formatted plant list for AI prompt
    """
    if not plant_list:
        return "No plants in database"
    
    query_lower = user_query.lower().strip()
    
    # First, try to find exact or partial matches in the full plant list
    matching_plants = []
    for plant in plant_list:
        plant_lower = plant.lower()
        # Check for exact match or if query contains plant name or vice versa
        if (query_lower == plant_lower or 
            query_lower in plant_lower or 
            plant_lower in query_lower):
            matching_plants.append(plant)
    
    # If we found matches, include them plus some context plants
    if matching_plants:
        # Get the indices of matching plants
        matching_indices = [i for i, plant in enumerate(plant_list) if plant in matching_plants]
        
        # Include matching plants plus some surrounding context
        context_plants = set()
        for idx in matching_indices:
            # Add the matching plant
            context_plants.add(plant_list[idx])
            # Add some plants before and after for context
            start_idx = max(0, idx - 2)
            end_idx = min(len(plant_list), idx + 3)
            for i in range(start_idx, end_idx):
                context_plants.add(plant_list[i])
        
        # Convert to list and sort to maintain some order
        context_plant_list = sorted(list(context_plants))
        
        # If we have too many context plants, limit them
        if len(context_plant_list) > 40:
            context_plant_list = context_plant_list[:40]
        
        return ", ".join(context_plant_list) + f" (and {len(plant_list) - len(context_plant_list)} more plants)"
    
    # If no matches found, use the original truncation approach
    if len(plant_list) > 30:
        return ", ".join(plant_list[:30]) + f" (and {len(plant_list) - 30} more plants)"
    else:
        return ", ".join(plant_list)

def _parse_analysis_response(ai_response: str) -> Dict:
    try:
        cleaned_response = ai_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        result = json.loads(cleaned_response.strip())
        required_fields = ['plant_references', 'query_type', 'confidence']
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing required field '{field}' in AI response")
                result[field] = [] if field == 'plant_references' else 'GENERAL' if field == 'query_type' else 0.5
        if not isinstance(result['plant_references'], list):
            result['plant_references'] = []
        valid_types = [QueryType.LOCATION, QueryType.PHOTO, QueryType.LIST, QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL]
        if result['query_type'] not in valid_types:
            logger.warning(f"Invalid query type '{result['query_type']}', defaulting to GENERAL")
            result['query_type'] = QueryType.GENERAL
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
    logger.warning("Using fallback analysis due to AI analysis failure")
    query_lower = user_query.lower()
    if any(word in query_lower for word in ['what plants', 'list', 'all plants', 'which plants', 'show all', 'tell me about the plants']):
        return {
            'plant_references': [],
            'query_type': QueryType.LIST,
            'confidence': 0.8,
            'reasoning': 'Fallback: detected list-related keywords',
            'requires_ai_response': False,
            'original_query': user_query,
            'plant_list_provided': 0
        }
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
    if any(word in query_lower for word in ['show me', 'picture', 'photo', 'see', 'look like', 'what does']):
        return {
            'plant_references': [],
            'query_type': QueryType.PHOTO,
            'confidence': 0.7,
            'reasoning': 'Fallback: detected photo-related keywords',
            'requires_ai_response': False,
            'original_query': user_query,
            'plant_list_provided': 0
        }
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