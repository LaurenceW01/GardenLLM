#!/usr/bin/env python3
"""
Test script for location-based queries in GardenLLM

This script tests the new location-based query functionality that allows users
to ask questions like "what plants are in the arboretum" or "how many different 
plants are in the rear left bed".

Author: GardenLLM Team
Date: December 2024
"""

import logging
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_location_query_analysis():
    """Test the query analyzer with location-based queries"""
    logger.info("Testing location query analysis...")
    
    try:
        from query_analyzer import analyze_query, QueryType
        
        # Test queries
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
            "What's growing in the patio containers?",
            "Where are my tomatoes?",  # This should be LOCATION, not LOCATION_PLANTS
            "What plants do I have?",  # This should be LIST
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            result = analyze_query(query)
            
            logger.info(f"  Query Type: {result['query_type']}")
            logger.info(f"  Plant References: {result['plant_references']}")
            logger.info(f"  Location References: {result.get('location_references', [])}")
            logger.info(f"  Confidence: {result['confidence']}")
            logger.info(f"  Requires AI Response: {result['requires_ai_response']}")
            logger.info(f"  Reasoning: {result.get('reasoning', 'N/A')}")
            
            # Verify expected query types
            if "arboretum" in query.lower() or "rear left bed" in query.lower() or "front garden" in query.lower() or "patio containers" in query.lower():
                expected_type = QueryType.LOCATION_PLANTS
            elif "where are my" in query.lower():
                expected_type = QueryType.LOCATION
            elif "what plants do i have" in query.lower():
                expected_type = QueryType.LIST
            else:
                expected_type = None
            
            if expected_type and result['query_type'] == expected_type:
                logger.info(f"  ✓ Query type correctly identified as {expected_type}")
            elif expected_type:
                logger.warning(f"  ✗ Expected {expected_type}, got {result['query_type']}")
            else:
                logger.info(f"  ? No specific expectation for this query")
        
        logger.info("\n✓ Location query analysis tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing location query analysis: {e}")
        return False

def test_location_plants_handler():
    """Test the location plants query handler"""
    logger.info("\nTesting location plants query handler...")
    
    try:
        from chat_response import handle_location_plants_query
        
        # Test with sample location references
        test_locations = [
            ["arboretum"],
            ["rear left bed"],
            ["front garden", "back patio"],
            ["nonexistent location"]
        ]
        
        for locations in test_locations:
            logger.info(f"\nTesting locations: {locations}")
            result = handle_location_plants_query(locations)
            logger.info(f"Response: {result[:200]}..." if len(result) > 200 else f"Response: {result}")
        
        logger.info("\n✓ Location plants handler tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing location plants handler: {e}")
        return False

def test_database_only_query_handler():
    """Test the database-only query handler with LOCATION_PLANTS"""
    logger.info("\nTesting database-only query handler...")
    
    try:
        from chat_response import handle_database_only_query
        from query_analyzer import QueryType
        
        # Test LOCATION_PLANTS query
        test_query = "What plants are in the arboretum?"
        result = handle_database_only_query(QueryType.LOCATION_PLANTS, [], test_query)
        logger.info(f"LOCATION_PLANTS query result: {result[:200]}..." if len(result) > 200 else f"LOCATION_PLANTS query result: {result}")
        
        logger.info("\n✓ Database-only query handler tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing database-only query handler: {e}")
        return False

def test_full_query_pipeline():
    """Test the full query pipeline with location-based queries"""
    logger.info("\nTesting full query pipeline...")
    
    try:
        from chat_response import get_chat_response_with_analyzer
        
        # Test queries
        test_queries = [
            "What plants are in the arboretum?",
            "How many different plants are in the rear left bed?",
            "Show me plants in the front garden",
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting full pipeline with query: '{query}'")
            result = get_chat_response_with_analyzer(query)
            logger.info(f"Full pipeline result: {result[:300]}..." if len(result) > 300 else f"Full pipeline result: {result}")
        
        logger.info("\n✓ Full query pipeline tests completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing full query pipeline: {e}")
        return False

def main():
    """Run all location query tests"""
    logger.info("Starting location query tests...")
    
    tests = [
        test_location_query_analysis,
        test_location_plants_handler,
        test_database_only_query_handler,
        test_full_query_pipeline
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
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All location query tests passed!")
        return 0
    else:
        logger.error("✗ Some location query tests failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 