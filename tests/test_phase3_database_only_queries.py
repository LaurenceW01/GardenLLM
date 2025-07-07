"""
Test Phase 3: Database-Only Query Processing

This test suite verifies that the new database-only query processing
correctly handles LOCATION, PHOTO, and LIST queries without requiring AI calls.
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_response import (
    handle_database_only_query, 
    handle_list_query, 
    handle_location_query, 
    handle_photo_query
)
from query_analyzer import QueryType

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPhase3DatabaseOnlyQueries:
    """Test Phase 3 database-only query processing"""
    
    def test_handle_list_query_success(self):
        """Test successful list query processing"""
        # Mock plant data
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1'},
            {'Plant Name': 'Basil', 'Location': 'Herb Garden'},
            {'Plant Name': 'Lettuce', 'Location': 'Raised Bed'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_list_query()
            
            assert "You have 3 plants in your garden:" in result
            assert "• Tomato" in result
            assert "• Basil" in result
            assert "• Lettuce" in result
            logger.info("✓ List query test passed")
    
    def test_handle_list_query_empty_database(self):
        """Test list query with empty database"""
        with patch('chat_response.get_plant_data', return_value=[]):
            result = handle_list_query()
            
            assert "There are currently no plants in the database." in result
            logger.info("✓ Empty list query test passed")
    
    def test_handle_list_query_error(self):
        """Test list query with database error"""
        with patch('chat_response.get_plant_data', return_value="Database error"):
            result = handle_list_query()
            
            assert "I encountered an error while retrieving the plant list." in result
            logger.info("✓ List query error test passed")
    
    def test_handle_location_query_success(self):
        """Test successful location query processing"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1', 'Raw Photo URL': 'http://example.com/tomato.jpg'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_location_query(['tomato'])
            
            assert "The Tomato is located in the Garden Bed 1." in result
            assert "You can see a photo of the Tomato here:" in result
            logger.info("✓ Location query test passed")
    
    def test_handle_location_query_no_location(self):
        """Test location query for plant without location"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': '', 'Raw Photo URL': ''}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_location_query(['tomato'])
            
            assert "I found Tomato, but its location is not specified." in result
            logger.info("✓ Location query no location test passed")
    
    def test_handle_location_query_plant_not_found(self):
        """Test location query for non-existent plant"""
        with patch('chat_response.get_plant_data', return_value=[]):
            result = handle_location_query(['nonexistent'])
            
            assert "I couldn't find any plants matching 'nonexistent'" in result
            logger.info("✓ Location query plant not found test passed")
    
    def test_handle_location_query_no_plant_references(self):
        """Test location query with no plant references"""
        result = handle_location_query([])
        
        assert "I couldn't identify which plants you're asking about." in result
        logger.info("✓ Location query no references test passed")
    
    def test_handle_photo_query_success(self):
        """Test successful photo query processing"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Raw Photo URL': 'http://example.com/tomato.jpg'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_photo_query(['tomato'])
            
            assert "Here's what Tomato looks like:" in result
            assert "http://example.com/tomato.jpg" in result
            logger.info("✓ Photo query test passed")
    
    def test_handle_photo_query_no_photo(self):
        """Test photo query for plant without photo"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Raw Photo URL': ''}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_photo_query(['tomato'])
            
            assert "I found Tomato, but there's no photo available." in result
            logger.info("✓ Photo query no photo test passed")
    
    def test_handle_photo_query_google_photos_url(self):
        """Test photo query with Google Photos URL formatting"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Raw Photo URL': 'https://photos.google.com/photo/AF1QipM?authuser=1'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_photo_query(['tomato'])
            
            assert "Here's what Tomato looks like:" in result
            assert "https://photos.google.com/photo/AF1QipM?authuser=0" in result
            logger.info("✓ Photo query Google Photos URL test passed")
    
    def test_handle_photo_query_plant_not_found(self):
        """Test photo query for non-existent plant"""
        with patch('chat_response.get_plant_data', return_value=[]):
            result = handle_photo_query(['nonexistent'])
            
            assert "I couldn't find any plants matching 'nonexistent'" in result
            logger.info("✓ Photo query plant not found test passed")
    
    def test_handle_photo_query_no_plant_references(self):
        """Test photo query with no plant references"""
        result = handle_photo_query([])
        
        assert "I couldn't identify which plants you're asking about." in result
        logger.info("✓ Photo query no references test passed")
    
    def test_handle_database_only_query_list(self):
        """Test main database-only query handler with LIST type"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_database_only_query(QueryType.LIST, [], "show me all plants")
            
            assert "You have 1 plants in your garden:" in result
            assert "• Tomato" in result
            logger.info("✓ Database-only query LIST test passed")
    
    def test_handle_database_only_query_location(self):
        """Test main database-only query handler with LOCATION type"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Location': 'Garden Bed 1'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_database_only_query(QueryType.LOCATION, ['tomato'], "where is the tomato")
            
            assert "The Tomato is located in the Garden Bed 1." in result
            logger.info("✓ Database-only query LOCATION test passed")
    
    def test_handle_database_only_query_photo(self):
        """Test main database-only query handler with PHOTO type"""
        mock_plant_data = [
            {'Plant Name': 'Tomato', 'Raw Photo URL': 'http://example.com/tomato.jpg'}
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            result = handle_database_only_query(QueryType.PHOTO, ['tomato'], "show me a photo of tomato")
            
            assert "Here's what Tomato looks like:" in result
            logger.info("✓ Database-only query PHOTO test passed")
    
    def test_handle_database_only_query_unknown_type(self):
        """Test main database-only query handler with unknown type"""
        with patch('chat_response.get_chat_response_legacy') as mock_legacy:
            mock_legacy.return_value = "Legacy response"
            
            result = handle_database_only_query("UNKNOWN", [], "unknown query")
            
            assert result == "Legacy response"
            mock_legacy.assert_called_once_with("unknown query")
            logger.info("✓ Database-only query unknown type test passed")

def run_phase3_tests():
    """Run all Phase 3 tests"""
    logger.info("Starting Phase 3 Database-Only Query Tests...")
    
    test_instance = TestPhase3DatabaseOnlyQueries()
    
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
    
    logger.info(f"\nPhase 3 Test Results:")
    logger.info(f"✓ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All Phase 3 tests passed!")
        return True
    else:
        logger.error("💥 Some Phase 3 tests failed!")
        return False

if __name__ == "__main__":
    success = run_phase3_tests()
    sys.exit(0 if success else 1) 