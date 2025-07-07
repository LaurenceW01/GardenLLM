"""
Test file for Phase 2: Plant List Caching System

This file contains unit tests for the plant list caching functionality
to ensure efficient database access for the query analyzer.

Author: GardenLLM Team
Date: December 2024
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from plant_operations import (
    get_plant_names_from_database,
    invalidate_plant_list_cache,
    get_plant_list_cache_info,
    _plant_list_cache
)

class TestPlantListCaching(unittest.TestCase):
    """Test cases for the Plant List Caching system"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset cache before each test
        _plant_list_cache['names'] = []
        _plant_list_cache['last_updated'] = 0

    def test_cache_initialization(self):
        """Test that cache is properly initialized"""
        cache_info = get_plant_list_cache_info()
        
        self.assertEqual(cache_info['plant_count'], 0)
        self.assertEqual(cache_info['last_updated'], 0)
        self.assertFalse(cache_info['is_valid'])
        self.assertEqual(cache_info['cache_duration_seconds'], 300)

    def test_cache_invalidation(self):
        """Test cache invalidation functionality"""
        # Set up some cached data
        _plant_list_cache['names'] = ['tomato', 'basil']
        _plant_list_cache['last_updated'] = time.time()
        
        # Verify cache is valid
        cache_info = get_plant_list_cache_info()
        self.assertTrue(cache_info['is_valid'])
        self.assertEqual(cache_info['plant_count'], 2)
        
        # Invalidate cache
        invalidate_plant_list_cache()
        
        # Verify cache is invalid
        cache_info = get_plant_list_cache_info()
        self.assertFalse(cache_info['is_valid'])
        self.assertEqual(cache_info['plant_count'], 2)  # Names still there but cache invalid

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_fetch_plant_names_from_database(self, mock_rate_limit, mock_sheets):
        """Test fetching plant names from database"""
        # Mock successful database response
        mock_response = Mock()
        mock_response.execute.return_value = {
            'values': [
                ['ID', 'Plant Name', 'Location', 'Description'],  # Header row
                ['1', 'Tomato', 'Front Garden', 'Red tomatoes'],
                ['2', 'Basil', 'Back Patio', 'Sweet basil'],
                ['3', 'Rose', 'Side Yard', 'Pink roses']
            ]
        }
        mock_sheets.return_value.get.return_value = mock_response
        
        # Fetch plant names
        plant_names = get_plant_names_from_database()
        
        # Verify results
        self.assertEqual(len(plant_names), 3)
        self.assertIn('Tomato', plant_names)
        self.assertIn('Basil', plant_names)
        self.assertIn('Rose', plant_names)
        
        # Verify cache was updated
        cache_info = get_plant_list_cache_info()
        self.assertTrue(cache_info['is_valid'])
        self.assertEqual(cache_info['plant_count'], 3)

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_cache_usage_on_subsequent_calls(self, mock_rate_limit, mock_sheets):
        """Test that subsequent calls use cached data"""
        # Mock successful database response
        mock_response = Mock()
        mock_response.execute.return_value = {
            'values': [
                ['ID', 'Plant Name', 'Location', 'Description'],
                ['1', 'Tomato', 'Front Garden', 'Red tomatoes'],
                ['2', 'Basil', 'Back Patio', 'Sweet basil']
            ]
        }
        mock_sheets.return_value.get.return_value = mock_response
        
        # First call - should fetch from database
        plant_names1 = get_plant_names_from_database()
        self.assertEqual(len(plant_names1), 2)
        
        # Second call - should use cache
        plant_names2 = get_plant_names_from_database()
        self.assertEqual(len(plant_names2), 2)
        
        # Verify database was only called once
        mock_sheets.return_value.get.assert_called_once()

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_cache_expiration(self, mock_rate_limit, mock_sheets):
        """Test that cache expires after the configured duration"""
        # Mock successful database response
        mock_response = Mock()
        mock_response.execute.return_value = {
            'values': [
                ['ID', 'Plant Name', 'Location', 'Description'],
                ['1', 'Tomato', 'Front Garden', 'Red tomatoes']
            ]
        }
        mock_sheets.return_value.get.return_value = mock_response
        
        # First call - should fetch from database
        plant_names1 = get_plant_names_from_database()
        self.assertEqual(len(plant_names1), 1)
        
        # Manually expire cache by setting last_updated to old time
        _plant_list_cache['last_updated'] = time.time() - 400  # 400 seconds ago (older than 300s cache)
        
        # Second call - should fetch from database again due to expiration
        plant_names2 = get_plant_names_from_database()
        self.assertEqual(len(plant_names2), 1)
        
        # Verify database was called twice
        self.assertEqual(mock_sheets.return_value.get.call_count, 2)

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_database_error_fallback_to_cache(self, mock_rate_limit, mock_sheets):
        """Test that database errors fall back to cached data"""
        # First, populate cache with some data
        _plant_list_cache['names'] = ['Cached Tomato', 'Cached Basil']
        _plant_list_cache['last_updated'] = time.time()
        
        # Mock database error
        mock_sheets.return_value.get.side_effect = Exception("Database error")
        
        # Call should return cached data
        plant_names = get_plant_names_from_database()
        
        # Verify cached data was returned
        self.assertEqual(len(plant_names), 2)
        self.assertIn('Cached Tomato', plant_names)
        self.assertIn('Cached Basil', plant_names)

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_empty_database_handling(self, mock_rate_limit, mock_sheets):
        """Test handling of empty database"""
        # Mock empty database response
        mock_response = Mock()
        mock_response.execute.return_value = {
            'values': [['ID', 'Plant Name', 'Location', 'Description']]  # Only header
        }
        mock_sheets.return_value.get.return_value = mock_response
        
        # Fetch plant names
        plant_names = get_plant_names_from_database()
        
        # Verify empty list returned
        self.assertEqual(len(plant_names), 0)
        
        # Verify cache was updated
        cache_info = get_plant_list_cache_info()
        self.assertEqual(cache_info['plant_count'], 0)

    @patch('plant_operations.sheets_client.values')
    @patch('plant_operations.check_rate_limit')
    def test_missing_plant_name_column(self, mock_rate_limit, mock_sheets):
        """Test handling when Plant Name column is missing"""
        # Mock response without Plant Name column
        mock_response = Mock()
        mock_response.execute.return_value = {
            'values': [
                ['ID', 'Location', 'Description'],  # No Plant Name column
                ['1', 'Front Garden', 'Red tomatoes'],
                ['2', 'Back Patio', 'Sweet basil']
            ]
        }
        mock_sheets.return_value.get.return_value = mock_response
        
        # Fetch plant names
        plant_names = get_plant_names_from_database()
        
        # Should handle gracefully (fall back to index 1)
        # This depends on the actual data structure

    def test_cache_info_accuracy(self):
        """Test that cache info provides accurate information"""
        # Set up cache with known data
        _plant_list_cache['names'] = ['Plant1', 'Plant2', 'Plant3']
        _plant_list_cache['last_updated'] = time.time()
        
        cache_info = get_plant_list_cache_info()
        
        self.assertEqual(cache_info['plant_count'], 3)
        self.assertTrue(cache_info['is_valid'])
        self.assertGreaterEqual(cache_info['cache_age_seconds'], 0)
        self.assertLess(cache_info['cache_age_seconds'], 1)  # Should be very recent

    def test_cache_copy_return(self):
        """Test that cache returns a copy, not the original list"""
        # Set up cache
        _plant_list_cache['names'] = ['Original Plant']
        _plant_list_cache['last_updated'] = time.time()
        
        # Get plant names
        plant_names = get_plant_names_from_database()
        
        # Modify the returned list
        plant_names.append('Modified Plant')
        
        # Verify original cache is unchanged
        self.assertEqual(len(_plant_list_cache['names']), 1)
        self.assertNotIn('Modified Plant', _plant_list_cache['names'])

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 