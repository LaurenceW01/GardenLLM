"""
Tests for climate_config.py module.
Tests all climate configuration and context functions.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import climate_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from climate_config import (
    DEFAULT_LOCATION,
    HOUSTON_CLIMATE,
    get_default_location,
    get_climate_params,
    get_climate_context,
    get_climate_param,
    get_hardiness_zone,
    get_growing_seasons,
    get_soil_info,
    is_location_supported,
    get_supported_locations
)

class TestClimateConfig(unittest.TestCase):
    """Test cases for climate configuration module."""

    def test_default_location(self):
        """Test that default location is Houston, TX, USA."""
        self.assertEqual(DEFAULT_LOCATION, "Houston, TX, USA")
        self.assertEqual(get_default_location(), "Houston, TX, USA")

    def test_houston_climate_parameters(self):
        """Test that Houston climate parameters are properly defined."""
        # Test that all expected climate parameters are present
        expected_params = [
            'hardiness_zone', 'zone_description', 'summer_highs', 'winter_lows',
            'temperature_description', 'humidity', 'humidity_description',
            'annual_rainfall', 'rainfall_pattern', 'rainfall_description',
            'soil_type', 'soil_ph', 'soil_description', 'spring_season',
            'fall_season', 'summer_avoidance', 'growing_seasons_description',
            'frost_dates', 'freeze_frequency', 'frost_description', 'climate_summary'
        ]
        
        for param in expected_params:
            self.assertIn(param, HOUSTON_CLIMATE, f"Climate parameter '{param}' not found")

    def test_get_climate_params(self):
        """Test the get_climate_params function."""
        # Test with None (should use default)
        params = get_climate_params()
        self.assertEqual(params['hardiness_zone'], '9a/9b')
        self.assertEqual(params['temperature_description'], 'Hot and humid subtropical climate with mild winters')
        
        # Test with Houston variations
        houston_variations = [
            'Houston, TX, USA',
            'Houston, TX',
            'Houston, Texas, USA',
            'Houston, Texas',
            'Houston',
            'houston, tx, usa',
            'houston, tx',
            'houston'
        ]
        
        for variation in houston_variations:
            params = get_climate_params(variation)
            self.assertEqual(params['hardiness_zone'], '9a/9b')
            self.assertEqual(params['climate_summary'], 'Hot and humid subtropical climate with mild winters, high humidity, and clay soil')
        
        # Test with unsupported location (should return Houston as default)
        params = get_climate_params('New York, NY')
        self.assertEqual(params['hardiness_zone'], '9a/9b')  # Should return Houston climate

    def test_get_climate_context(self):
        """Test the get_climate_context function."""
        # Test with default location
        context = get_climate_context()
        
        # Check that context contains expected information
        self.assertIn('Location: Houston, TX, USA', context)
        self.assertIn('Climate: Hot and humid subtropical climate with mild winters', context)
        self.assertIn('Growing season: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat', context)
        self.assertIn('Hardiness Zone: 9a/9b', context)
        self.assertIn('Temperature Range: Summer 90-100°F (32-38°C), Winter 30-40°F (-1-4°C)', context)
        self.assertIn('Humidity: 60-80%', context)
        self.assertIn('Rainfall: 50+ inches annually, heavy spring/fall rains', context)
        self.assertIn('Soil: Clay soil, alkaline pH (7.0-8.0)', context)
        self.assertIn('Frost: Occasional freezes, protect sensitive plants', context)
        
        # Test with specific location
        context = get_climate_context('Houston, TX')
        self.assertIn('Location: Houston, TX', context)

    def test_get_climate_param(self):
        """Test the get_climate_param function."""
        # Test getting specific parameters
        self.assertEqual(get_climate_param('hardiness_zone'), '9a/9b')
        self.assertEqual(get_climate_param('summer_highs'), '90-100°F (32-38°C)')
        self.assertEqual(get_climate_param('soil_description'), 'Clay soil, alkaline pH (7.0-8.0)')
        
        # Test with specific location
        self.assertEqual(get_climate_param('hardiness_zone', 'Houston, TX'), '9a/9b')
        
        # Test with invalid parameter
        self.assertIsNone(get_climate_param('invalid_param'))

    def test_get_hardiness_zone(self):
        """Test the get_hardiness_zone function."""
        # Test with default location
        self.assertEqual(get_hardiness_zone(), '9a/9b')
        
        # Test with specific location
        self.assertEqual(get_hardiness_zone('Houston, TX'), '9a/9b')
        
        # Test with unsupported location (should return default)
        self.assertEqual(get_hardiness_zone('New York, NY'), '9a/9b')

    def test_get_growing_seasons(self):
        """Test the get_growing_seasons function."""
        # Test with default location
        expected = 'Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat'
        self.assertEqual(get_growing_seasons(), expected)
        
        # Test with specific location
        self.assertEqual(get_growing_seasons('Houston, TX'), expected)

    def test_get_soil_info(self):
        """Test the get_soil_info function."""
        # Test with default location
        expected = 'Clay soil, alkaline pH (7.0-8.0)'
        self.assertEqual(get_soil_info(), expected)
        
        # Test with specific location
        self.assertEqual(get_soil_info('Houston, TX'), expected)

    def test_is_location_supported(self):
        """Test the is_location_supported function."""
        # Test supported locations
        supported_locations = [
            'Houston, TX, USA',
            'Houston, TX',
            'Houston, Texas, USA',
            'Houston, Texas',
            'Houston',
            'houston, tx, usa',
            'houston, tx',
            'houston'
        ]
        
        for location in supported_locations:
            self.assertTrue(is_location_supported(location), f"Location '{location}' should be supported")
        
        # Test unsupported locations
        unsupported_locations = [
            'New York, NY',
            'Los Angeles, CA',
            'Chicago, IL',
            'Miami, FL',
            'Seattle, WA'
        ]
        
        for location in unsupported_locations:
            self.assertFalse(is_location_supported(location), f"Location '{location}' should not be supported")

    def test_get_supported_locations(self):
        """Test the get_supported_locations function."""
        supported = get_supported_locations()
        
        # Test that we get a list
        self.assertIsInstance(supported, list)
        
        # Test that Houston variations are included
        expected_locations = [
            'Houston, TX, USA',
            'Houston, TX',
            'Houston, Texas, USA',
            'Houston, Texas',
            'Houston'
        ]
        
        for location in expected_locations:
            self.assertIn(location, supported, f"Location '{location}' should be in supported locations")

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty string
        params = get_climate_params('')
        self.assertEqual(params['hardiness_zone'], '9a/9b')  # Should return Houston climate
        
        # Test with whitespace
        params = get_climate_params('   houston   ')
        self.assertEqual(params['hardiness_zone'], '9a/9b')
        
        # Test case sensitivity
        self.assertTrue(is_location_supported('HOUSTON'))
        self.assertTrue(is_location_supported('Houston'))
        self.assertTrue(is_location_supported('houston'))

if __name__ == '__main__':
    unittest.main() 