"""
Phase 2 Integration Test

This test demonstrates the Phase 2 integration working with real database data.
It shows how the query analyzer now has access to actual plant names from the database.

Author: GardenLLM Team
Date: December 2024
"""

import logging
from query_analyzer import analyze_query
from plant_operations import get_plant_names_from_database, get_plant_list_cache_info

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_phase2_integration():
    """Test Phase 2 integration with real database data"""
    print("=" * 60)
    print("PHASE 2 INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Get plant names from database
    print("\n1. Testing plant list retrieval from database...")
    plant_names = get_plant_names_from_database()
    print(f"   Retrieved {len(plant_names)} plant names from database")
    
    if plant_names:
        print(f"   Sample plants: {', '.join(plant_names[:5])}")
        if len(plant_names) > 5:
            print(f"   ... and {len(plant_names) - 5} more")
    else:
        print("   No plants found in database")
    
    # Test 2: Check cache info
    print("\n2. Testing cache information...")
    cache_info = get_plant_list_cache_info()
    print(f"   Cache status: {'Valid' if cache_info['is_valid'] else 'Invalid'}")
    print(f"   Cache age: {cache_info['cache_age_seconds']:.1f} seconds")
    print(f"   Cache duration: {cache_info['cache_duration_seconds']} seconds")
    
    # Test 3: Test query analysis with real plant data
    print("\n3. Testing query analysis with real plant data...")
    
    # Test queries that might reference real plants
    test_queries = [
        "Where are my tomatoes?",
        "How do I care for my basil?",
        "Show me my roses",
        "What plants do I have?",
        "Why are my hibiscus leaves turning yellow?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Test {i}: '{query}'")
        try:
            result = analyze_query(query)
            print(f"      Plant references: {result['plant_references']}")
            print(f"      Query type: {result['query_type']}")
            print(f"      Confidence: {result['confidence']}")
            print(f"      Requires AI response: {result['requires_ai_response']}")
            print(f"      Plant list provided: {result['plant_list_provided']} plants")
        except Exception as e:
            print(f"      Error: {e}")
    
    # Test 4: Test cache efficiency
    print("\n4. Testing cache efficiency...")
    print("   Making second call to test cache usage...")
    
    start_time = time.time()
    plant_names2 = get_plant_names_from_database()
    end_time = time.time()
    
    print(f"   Retrieved {len(plant_names2)} plants in {end_time - start_time:.3f} seconds")
    print(f"   Cache should be used if time is very fast (< 0.1 seconds)")
    
    # Test 5: Cache invalidation
    print("\n5. Testing cache invalidation...")
    from plant_operations import invalidate_plant_list_cache
    invalidate_plant_list_cache()
    
    cache_info_after = get_plant_list_cache_info()
    print(f"   Cache status after invalidation: {'Valid' if cache_info_after['is_valid'] else 'Invalid'}")
    
    print("\n" + "=" * 60)
    print("PHASE 2 INTEGRATION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    import time
    test_phase2_integration() 