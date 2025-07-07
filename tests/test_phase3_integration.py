"""
Test Phase 3 Integration: Real Query Processing

This test verifies that Phase 3 database-only query processing
works correctly with real user queries through the main chat system.
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_response import get_chat_response

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPhase3Integration:
    """Test Phase 3 integration with real queries"""
    
    def test_list_query_integration(self):
        """Test list query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1'},
            {'Plant Name': 'Basil', 'Location': 'Herb Garden'},
            {'Plant Name': 'Lettuce', 'Location': 'Raised Bed'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            # Test various list query formats
            list_queries = [
                "What plants do I have?",
                "Show me all my plants",
                "List all plants in my garden",
                "Tell me about the plants I have"
            ]
            
            for query in list_queries:
                result = get_chat_response(query)
                logger.info(f"Query: '{query}'")
                logger.info(f"Result: {result[:100]}...")
                
                # Should contain plant count and names
                assert "You have 3 plants in your garden:" in result
                assert "• Tomato" in result
                assert "• Basil" in result
                assert "• Lettuce" in result
                
            logger.info("✓ List query integration test passed")
    
    def test_location_query_integration(self):
        """Test location query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1', 'Raw Photo URL': 'http://example.com/tomato.jpg'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            # Test various location query formats
            location_queries = [
                "Where is my tomato plant?",
                "Where can I find the tomato?",
                "What's the location of my tomato?",
                "Where are my tomatoes planted?"
            ]
            
            for query in location_queries:
                result = get_chat_response(query)
                logger.info(f"Query: '{query}'")
                logger.info(f"Result: {result[:100]}...")
                
                # Should contain location information
                assert "The Tomato is located in the Garden Bed 1." in result
                
            logger.info("✓ Location query integration test passed")
    
    def test_photo_query_integration(self):
        """Test photo query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Raw Photo URL': 'http://example.com/tomato.jpg'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            # Test various photo query formats
            photo_queries = [
                "Show me a picture of my tomato",
                "What does my tomato plant look like?",
                "Can I see a photo of the tomato?",
                "Show me the tomato plant"
            ]
            
            for query in photo_queries:
                result = get_chat_response(query)
                logger.info(f"Query: '{query}'")
                logger.info(f"Result: {result[:100]}...")
                
                # Should contain photo information
                assert "Here's what Tomato looks like:" in result
                assert "http://example.com/tomato.jpg" in result
                
            logger.info("✓ Photo query integration test passed")
    
    def test_mixed_query_types(self):
        """Test that different query types are handled correctly"""
        # Mock different plant data for different queries
        def mock_get_plant_data(search_terms):
            if not search_terms:  # List query
                return [
                    {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1'},
                    {'Plant Name': 'Basil', 'Location': 'Herb Garden'}
                ]
            elif 'tomato' in search_terms[0].lower():
                return [{'Plant Name': 'Tomato', 'Location': 'Garden Bed 1', 'Raw Photo URL': 'http://example.com/tomato.jpg'}]
            else:
                return []
        
        with patch('chat_response.get_plant_data', side_effect=mock_get_plant_data):
            # Test list query
            list_result = get_chat_response("What plants do I have?")
            assert "You have 2 plants in your garden:" in list_result
            
            # Test location query
            location_result = get_chat_response("Where is my tomato?")
            assert "The Tomato is located in the Garden Bed 1." in location_result
            
            # Test photo query
            photo_result = get_chat_response("Show me a picture of tomato")
            assert "Here's what Tomato looks like:" in photo_result
            
            logger.info("✓ Mixed query types test passed")
    
    def test_query_analyzer_fallback(self):
        """Test that system falls back to legacy processing when analyzer fails"""
        # Mock analyzer to fail
        with patch('chat_response.analyze_query', side_effect=Exception("Analyzer error")):
            with patch('chat_response.get_chat_response_legacy') as mock_legacy:
                mock_legacy.return_value = "Legacy response"
                
                result = get_chat_response("test query")
                
                assert result == "Legacy response"
                mock_legacy.assert_called_once_with("test query")
                
            logger.info("✓ Query analyzer fallback test passed")

def run_phase3_integration_tests():
    """Run all Phase 3 integration tests"""
    logger.info("Starting Phase 3 Integration Tests...")
    
    test_instance = TestPhase3Integration()
    
    # Run all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            logger.error(f"❌ Test {method_name} failed: {e}")
            failed += 1
    
    logger.info(f"\nPhase 3 Integration Test Results:")
    logger.info(f"✓ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All Phase 3 integration tests passed!")
        return True
    else:
        logger.error("💥 Some Phase 3 integration tests failed!")
        return False

if __name__ == "__main__":
    success = run_phase3_integration_tests()
    sys.exit(0 if success else 1) 