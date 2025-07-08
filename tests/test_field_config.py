"""
Tests for field_config.py module.
Tests all field mapping and validation functions.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import field_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from field_config import (
    FIELD_NAMES,
    FIELD_ALIASES,
    FIELD_CATEGORIES,
    get_canonical_field_name,
    is_valid_field,
    get_all_field_names,
    get_aliases_for_field,
    get_field_category
)

class TestFieldConfig(unittest.TestCase):
    """Test cases for field configuration module."""

    def test_field_names_are_defined(self):
        """Test that all expected field names are defined."""
        # Test that we have the expected number of fields (17 total)
        self.assertEqual(len(FIELD_NAMES), 17)
        
        # Test that all expected fields are present
        expected_fields = [
            'ID', 'Plant Name', 'Description', 'Location', 'Light Requirements',
            'Frost Tolerance', 'Watering Needs', 'Soil Preferences', 'Pruning Instructions',
            'Mulching Needs', 'Fertilizing Schedule', 'Winterizing Instructions',
            'Spacing Requirements', 'Care Notes', 'Photo URL', 'Raw Photo URL', 'Last Updated'
        ]
        
        for field in expected_fields:
            self.assertIn(field, FIELD_NAMES, f"Field '{field}' not found in FIELD_NAMES")

    def test_field_aliases_are_defined(self):
        """Test that field aliases are properly defined."""
        # Test that we have aliases for all major fields
        self.assertIn('name', FIELD_ALIASES)
        self.assertIn('location', FIELD_ALIASES)
        self.assertIn('light', FIELD_ALIASES)
        self.assertIn('water', FIELD_ALIASES)
        self.assertIn('soil', FIELD_ALIASES)
        self.assertIn('photo', FIELD_ALIASES)
        
        # Test that aliases map to valid field names
        for alias, canonical in FIELD_ALIASES.items():
            self.assertIn(canonical, FIELD_NAMES, f"Alias '{alias}' maps to invalid field '{canonical}'")

    def test_field_categories_are_defined(self):
        """Test that field categories are properly defined."""
        # Test that all categories exist
        expected_categories = ['basic', 'care', 'media', 'metadata']
        for category in expected_categories:
            self.assertIn(category, FIELD_CATEGORIES)
        
        # Test that all fields are assigned to categories
        categorized_fields = []
        for fields in FIELD_CATEGORIES.values():
            categorized_fields.extend(fields)
        
        for field in FIELD_NAMES:
            if field != 'ID':  # ID might be in basic category
                self.assertIn(field, categorized_fields, f"Field '{field}' not assigned to any category")

    def test_get_canonical_field_name(self):
        """Test the get_canonical_field_name function."""
        # Test direct field name matching (case-insensitive)
        self.assertEqual(get_canonical_field_name('Plant Name'), 'Plant Name')
        self.assertEqual(get_canonical_field_name('plant name'), 'Plant Name')
        self.assertEqual(get_canonical_field_name('PLANT NAME'), 'Plant Name')
        
        # Test alias matching
        self.assertEqual(get_canonical_field_name('name'), 'Plant Name')
        self.assertEqual(get_canonical_field_name('location'), 'Location')
        self.assertEqual(get_canonical_field_name('light'), 'Light Requirements')
        self.assertEqual(get_canonical_field_name('water'), 'Watering Needs')
        
        # Test invalid fields
        self.assertIsNone(get_canonical_field_name('invalid_field'))
        self.assertIsNone(get_canonical_field_name(''))
        self.assertIsNone(get_canonical_field_name('   '))

    def test_is_valid_field(self):
        """Test the is_valid_field function."""
        # Test valid fields
        self.assertTrue(is_valid_field('Plant Name'))
        self.assertTrue(is_valid_field('plant name'))
        self.assertTrue(is_valid_field('name'))
        self.assertTrue(is_valid_field('location'))
        self.assertTrue(is_valid_field('light'))
        
        # Test invalid fields
        self.assertFalse(is_valid_field('invalid_field'))
        self.assertFalse(is_valid_field(''))
        self.assertFalse(is_valid_field('   '))

    def test_get_all_field_names(self):
        """Test the get_all_field_names function."""
        field_names = get_all_field_names()
        
        # Test that we get a copy of the field names
        self.assertEqual(len(field_names), len(FIELD_NAMES))
        self.assertIsNot(field_names, FIELD_NAMES)  # Should be a copy, not the same object
        
        # Test that all expected fields are present
        for field in FIELD_NAMES:
            self.assertIn(field, field_names)

    def test_get_aliases_for_field(self):
        """Test the get_aliases_for_field function."""
        # Test getting aliases for Plant Name
        plant_name_aliases = get_aliases_for_field('Plant Name')
        self.assertIn('name', plant_name_aliases)
        self.assertIn('plant', plant_name_aliases)
        self.assertIn('plant name', plant_name_aliases)
        
        # Test getting aliases for Location
        location_aliases = get_aliases_for_field('Location')
        self.assertIn('location', location_aliases)
        self.assertIn('where', location_aliases)
        self.assertIn('place', location_aliases)
        
        # Test getting aliases for Photo URL
        photo_aliases = get_aliases_for_field('Photo URL')
        self.assertIn('photo', photo_aliases)
        self.assertIn('photo url', photo_aliases)
        self.assertIn('image', photo_aliases)
        self.assertIn('picture', photo_aliases)
        self.assertIn('url', photo_aliases)

    def test_get_field_category(self):
        """Test the get_field_category function."""
        # Test basic category
        self.assertEqual(get_field_category('Plant Name'), 'basic')
        self.assertEqual(get_field_category('Description'), 'basic')
        self.assertEqual(get_field_category('Location'), 'basic')
        
        # Test care category
        self.assertEqual(get_field_category('Light Requirements'), 'care')
        self.assertEqual(get_field_category('Watering Needs'), 'care')
        self.assertEqual(get_field_category('Soil Preferences'), 'care')
        
        # Test media category
        self.assertEqual(get_field_category('Photo URL'), 'media')
        self.assertEqual(get_field_category('Raw Photo URL'), 'media')
        
        # Test metadata category
        self.assertEqual(get_field_category('Last Updated'), 'metadata')
        
        # Test invalid field
        self.assertIsNone(get_field_category('Invalid Field'))

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test whitespace handling
        self.assertEqual(get_canonical_field_name('  plant name  '), 'Plant Name')
        self.assertTrue(is_valid_field('  plant name  '))
        
        # Test case sensitivity in aliases
        self.assertEqual(get_canonical_field_name('NAME'), 'Plant Name')
        self.assertEqual(get_canonical_field_name('Name'), 'Plant Name')
        
        # Test empty string values
        self.assertIsNone(get_canonical_field_name(''))
        self.assertFalse(is_valid_field(''))

if __name__ == '__main__':
    unittest.main() 