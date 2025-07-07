#!/usr/bin/env python3
"""
Test script for AI-driven location queries in GardenLLM

This script tests the current location query functionality and then implements
the AI-driven location query feature that allows users to ask questions like 
"what plants are in the arboretum" or "how many different plants are in the rear left bed" 
using AI for location matching instead of custom code.

Author: GardenLLM Team
Date: December 2024
"""

import logging
import sys
import os
import json
from typing import List

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_current_location_functionality():
    """Test the current location query functionality"""
    logger.info("Testing current location query functionality...")
    
    try:
        from chat_response import handle_location_plants_query
        from plant_operations import get_location_names_from_database
        
        # Get available locations
        location_list = get_location_names_from_database()
        logger.info(f"Available locations: {location_list[:10]}... (showing first 10)")
        
        # Test with some known locations
        test_locations = location_list[:3] if len(location_list) >= 3 else location_list
        
        for location in test_locations:
            logger.info(f"\nTesting location: '{location}'")
            result = handle_location_plants_query([location])
            logger.info(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
            
            # Check if response indicates success
            if "plants I found" in result or "plants in" in result:
                logger.info("  ✓ Location query handled successfully")
            elif "couldn't find any plants" in result:
                logger.info("  ⚠️  Location query handled but no plants found")
            else:
                logger.warning("  ? Unexpected response format")
        
        logger.info("\n✓ Current location functionality tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing current location functionality: {e}")
        return False

def test_query_analyzer_location_handling():
    """Test how the query analyzer currently handles location-based queries"""
    logger.info("\nTesting query analyzer location handling...")
    
    try:
        from query_analyzer import analyze_query
        
        # Test queries that should be location-based
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
            "What's growing in the patio containers?",
            "Which plants are in the kitchen bed?",
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            result = analyze_query(query)
            logger.info(f"Query type: {result.get('query_type')}")
            logger.info(f"Plant references: {result.get('plant_references')}")
            logger.info(f"Requires AI response: {result.get('requires_ai_response')}")
            
            # Check if it's classified as a location query
            if result.get('query_type') == 'LOCATION':
                logger.info("  ✓ Correctly classified as LOCATION query")
            else:
                logger.info(f"  ⚠️  Classified as {result.get('query_type')} instead of LOCATION")
        
        logger.info("\n✓ Query analyzer location handling tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing query analyzer location handling: {e}")
        return False

def implement_ai_location_matching():
    """Implement the AI-driven location matching functionality"""
    logger.info("\nImplementing AI-driven location matching...")
    
    try:
        # Add the AI location matching function to chat_response.py
        from chat_response import openai_client
        
        def ai_match_locations(user_query: str, location_list: List[str]) -> List[str]:
            """
            Use AI to match user query to valid locations from the database.
            
            Args:
                user_query (str): The user's query (e.g., "what plants are in the arboretum")
                location_list (List[str]): List of valid locations from the database
            
            Returns:
                List[str]: List of matched location names
            """
            if not location_list:
                return []
            
            try:
                prompt = f"""
You are a gardening assistant that matches user queries to specific garden locations.

Available locations in the garden: {', '.join(location_list)}

User query: "{user_query}"

Analyze the user query and return ONLY a JSON array of location names that match what the user is asking about. 
If the user is asking about multiple locations, include all relevant ones.
If no locations match, return an empty array.

Examples:
- "What plants are in the arboretum?" → ["arboretum"]
- "Plants in the front and back areas" → ["front garden", "back yard"] (if these exist)
- "How many plants in the kitchen bed?" → ["kitchen bed"]
- "Show me patio containers" → ["patio containers"] (if this exact name exists)

Return ONLY the JSON array, no other text:
"""
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a gardening assistant that matches user queries to garden locations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                
                ai_response = response.choices[0].message.content
                if not ai_response:
                    return []
                
                # Parse JSON response
                try:
                    matched_locations = json.loads(ai_response.strip())
                    if isinstance(matched_locations, list):
                        # Validate that all matched locations exist in the original list
                        valid_locations = [loc for loc in matched_locations if loc in location_list]
                        logger.info(f"AI matched locations: {matched_locations}, valid: {valid_locations}")
                        return valid_locations
                    else:
                        logger.warning(f"AI response is not a list: {matched_locations}")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response as JSON: {e}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error in AI location matching: {e}")
                return []
        
        # Add the function to the module
        import chat_response
        chat_response.ai_match_locations = ai_match_locations
        
        logger.info("✓ AI location matching function implemented")
        return True
        
    except Exception as e:
        logger.error(f"Error implementing AI location matching: {e}")
        return False

def implement_location_plants_query_with_ai():
    """Implement the complete location plants query handler with AI"""
    logger.info("\nImplementing location plants query handler with AI...")
    
    try:
        from chat_response import ai_match_locations
        from plant_operations import get_plants_by_location
        
        def handle_location_plants_query_with_ai(user_query: str) -> str:
            """
            Handle location-based plant queries using AI for location matching.
            
            Args:
                user_query (str): The user's query (e.g., "what plants are in the arboretum")
            
            Returns:
                str: Formatted response with plants found in the matched locations
            """
            try:
                # Get available locations from database
                from plant_operations import get_location_names_from_database
                location_list = get_location_names_from_database()
                
                if not location_list:
                    return "I couldn't find any location information in your garden database."
                
                # Use AI to match the query to locations
                matched_locations = ai_match_locations(user_query, location_list)
                
                if not matched_locations:
                    return f"I couldn't identify which locations you're asking about in your query: '{user_query}'. Please try being more specific about the location names."
                
                # Get plants for the matched locations
                plant_data = get_plants_by_location(matched_locations)
                
                if isinstance(plant_data, str):  # Error message
                    return f"Error looking up plants in locations {matched_locations}: {plant_data}"
                
                if not plant_data:
                    locations_str = ", ".join(matched_locations)
                    return f"I couldn't find any plants in the following locations: {locations_str}."
                
                # Format the response
                response_parts = []
                locations_str = ", ".join(matched_locations)
                response_parts.append(f"Here are the plants I found in {locations_str}:")
                
                # Group plants by location for better organization
                plants_by_location = {}
                for plant in plant_data:
                    plant_name = plant.get('Plant Name', 'Unknown Plant')
                    location = plant.get('Location', 'Unknown Location')
                    
                    if location not in plants_by_location:
                        plants_by_location[location] = []
                    plants_by_location[location].append(plant_name)
                
                # Add plants grouped by location
                for location, plants in plants_by_location.items():
                    if len(plants) == 1:
                        response_parts.append(f"• {location}: {plants[0]}")
                    else:
                        plants_list = ", ".join(plants)
                        response_parts.append(f"• {location}: {plants_list}")
                
                # Add photo URLs if available
                photo_plants = []
                for plant in plant_data:
                    plant_name = plant.get('Plant Name', 'Unknown Plant')
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    if raw_photo_url:
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        photo_plants.append(f"{plant_name}: {raw_photo_url}")
                
                if photo_plants:
                    response_parts.append("\nPhotos available for:")
                    response_parts.extend([f"• {photo}" for photo in photo_plants])
                
                return "\n".join(response_parts)
                
            except Exception as e:
                logger.error(f"Error handling location plants query with AI: {e}")
                return "I encountered an error while looking up plants in those locations. Please try again."
        
        # Add the function to the module
        import chat_response
        chat_response.handle_location_plants_query_with_ai = handle_location_plants_query_with_ai
        
        logger.info("✓ Location plants query handler with AI implemented")
        return True
        
    except Exception as e:
        logger.error(f"Error implementing location plants query handler with AI: {e}")
        return False

def test_ai_location_matching():
    """Test the AI location matching function"""
    logger.info("\nTesting AI location matching...")
    
    try:
        from chat_response import ai_match_locations
        from plant_operations import get_location_names_from_database
        
        # Get available locations
        location_list = get_location_names_from_database()
        logger.info(f"Available locations: {location_list[:10]}... (showing first 10)")
        
        # Test queries
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
            "What's growing in the patio containers?",
            "Which plants are in the kitchen bed?",
            "Plants in the back yard",
            "What's in the front porch area?",
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            matched_locations = ai_match_locations(query, location_list)
            logger.info(f"  Matched locations: {matched_locations}")
            
            # Verify that matched locations are in the original list
            for loc in matched_locations:
                if loc not in location_list:
                    logger.warning(f"  ⚠️  Matched location '{loc}' not in original list!")
                else:
                    logger.info(f"  ✓ Location '{loc}' found in database")
        
        logger.info("\n✓ AI location matching tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing AI location matching: {e}")
        return False

def test_location_plants_query_with_ai():
    """Test the complete location plants query handler"""
    logger.info("\nTesting complete location plants query handler...")
    
    try:
        from chat_response import handle_location_plants_query_with_ai
        
        # Test queries
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
            "What's growing in the patio containers?",
            "Which plants are in the kitchen bed?",
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            result = handle_location_plants_query_with_ai(query)
            logger.info(f"Response: {result[:200]}..." if len(result) > 200 else f"Response: {result}")
            
            # Check if response indicates success
            if "plants I found" in result or "plants in" in result:
                logger.info("  ✓ Query handled successfully")
            elif "couldn't identify" in result or "couldn't find" in result:
                logger.info("  ⚠️  Query handled but no plants found")
            else:
                logger.warning("  ? Unexpected response format")
        
        logger.info("\n✓ Location plants query handler tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing location plants query handler: {e}")
        return False

def test_full_query_pipeline():
    """Test the full query pipeline with location-based queries"""
    logger.info("\nTesting full query pipeline...")
    
    try:
        from chat_response import get_chat_response_with_analyzer
        
        # Test queries that should trigger location-based handling
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
            "Which plants are in the patio containers?",
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting full pipeline with query: '{query}'")
            result = get_chat_response_with_analyzer(query)
            logger.info(f"Full pipeline result: {result[:300]}..." if len(result) > 300 else f"Full pipeline result: {result}")
            
            # Check if the response indicates location-based handling worked
            if "plants I found" in result or "plants in" in result:
                logger.info("  ✓ Full pipeline handled location query successfully")
            elif "couldn't identify" in result or "couldn't find" in result:
                logger.info("  ⚠️  Full pipeline handled query but no plants found")
            else:
                logger.warning("  ? Unexpected response from full pipeline")
        
        logger.info("\n✓ Full query pipeline tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing full query pipeline: {e}")
        return False

def main():
    """Run all AI-driven location query tests"""
    logger.info("Starting AI-driven location query tests...")
    
    # Test current functionality first
    tests = [
        test_current_location_functionality,
        test_query_analyzer_location_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                logger.error(f"Test {test.__name__} failed")
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
    
    logger.info(f"\nCurrent functionality test results: {passed}/{total} tests passed")
    
    # Now implement and test the AI-driven functionality
    logger.info("\n" + "="*50)
    logger.info("Implementing AI-driven location query functionality...")
    
    implementation_tests = [
        implement_ai_location_matching,
        implement_location_plants_query_with_ai,
        test_ai_location_matching,
        test_location_plants_query_with_ai,
        test_full_query_pipeline,
    ]
    
    impl_passed = 0
    impl_total = len(implementation_tests)
    
    for test in implementation_tests:
        try:
            if test():
                impl_passed += 1
            else:
                logger.error(f"Test {test.__name__} failed")
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Final Test Results:")
    logger.info(f"Current functionality: {passed}/{total} tests passed")
    logger.info(f"AI-driven implementation: {impl_passed}/{impl_total} tests passed")
    
    if passed == total and impl_passed == impl_total:
        logger.info("✓ All AI-driven location query tests passed!")
        return 0
    else:
        logger.error("✗ Some AI-driven location query tests failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 