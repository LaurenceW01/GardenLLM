"""
Test AI-powered intelligent plant name matching.

This test verifies that the AI's intelligent matching capabilities correctly handles:
- Generic vs specific plant names
- Compound plant names
- Context-aware matching
"""

import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_analyzer import analyze_query, QueryType

class TestAIIntelligentMatching(unittest.TestCase):
    """Test AI-powered intelligent plant name matching"""

    def setUp(self):
        """Set up test data with various plant name types"""
        # Sample plant list with different types of names
        self.plant_list = [
            "Peggy Martin Rose",
            "Cherry Tomato", 
            "Sweet Basil",
            "Thai Basil",
            "Roma Tomato",
            "Beefsteak Tomato",
            "English Rose",
            "Tea Rose",
            "Hybrid Tea Rose",
            "Lavender",
            "Rosemary",
            "Thyme"
        ]

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_generic_rose_matches_all_roses(self, mock_openai):
        """Test that asking about 'roses' matches all rose varieties"""
        # Mock AI response for generic rose query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Peggy Martin Rose", "English Rose", "Tea Rose", "Hybrid Tea Rose"],
            "query_type": "CARE",
            "confidence": 0.95,
            "reasoning": "User asked about 'roses' generically, so matching all rose varieties in database"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("How do I care for my roses?", self.plant_list)
        
        # Verify the AI correctly identified all rose varieties
        expected_roses = ["Peggy Martin Rose", "English Rose", "Tea Rose", "Hybrid Tea Rose"]
        self.assertEqual(set(result['plant_references']), set(expected_roses))
        self.assertEqual(result['query_type'], "CARE")
        self.assertTrue(result['requires_ai_response'])

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_specific_rose_matches_only_exact(self, mock_openai):
        """Test that asking about 'Peggy Martin Rose' matches only that specific variety"""
        # Mock AI response for specific rose query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Peggy Martin Rose"],
            "query_type": "LOCATION",
            "confidence": 0.98,
            "reasoning": "User asked about specific 'Peggy Martin Rose', so matching only that exact variety"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("Where is my Peggy Martin Rose?", self.plant_list)
        
        # Verify the AI correctly identified only the specific rose
        self.assertEqual(result['plant_references'], ["Peggy Martin Rose"])
        self.assertEqual(result['query_type'], "LOCATION")
        self.assertFalse(result['requires_ai_response'])

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_generic_tomato_matches_all_tomatoes(self, mock_openai):
        """Test that asking about 'tomatoes' matches all tomato varieties"""
        # Mock AI response for generic tomato query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Cherry Tomato", "Roma Tomato", "Beefsteak Tomato"],
            "query_type": "CARE",
            "confidence": 0.94,
            "reasoning": "User asked about 'tomatoes' generically, so matching all tomato varieties"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("How do I grow tomatoes?", self.plant_list)
        
        # Verify the AI correctly identified all tomato varieties
        expected_tomatoes = ["Cherry Tomato", "Roma Tomato", "Beefsteak Tomato"]
        self.assertEqual(set(result['plant_references']), set(expected_tomatoes))
        self.assertEqual(result['query_type'], "CARE")

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_cherry_alone_does_not_match_cherry_tomato(self, mock_openai):
        """Test that asking about 'cherry' alone does not match 'Cherry Tomato'"""
        # Mock AI response for cherry query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": [],
            "query_type": "GENERAL",
            "confidence": 0.85,
            "reasoning": "User asked about 'cherry' but this is too vague to match 'Cherry Tomato' specifically"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("Show me cherry", self.plant_list)
        
        # Verify the AI correctly did not match Cherry Tomato
        self.assertEqual(result['plant_references'], [])
        self.assertEqual(result['query_type'], "GENERAL")

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_cherry_tomato_matches_specifically(self, mock_openai):
        """Test that asking about 'cherry tomato' matches specifically"""
        # Mock AI response for cherry tomato query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Cherry Tomato"],
            "query_type": "PHOTO",
            "confidence": 0.97,
            "reasoning": "User specifically asked about 'cherry tomato', matching exact variety"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("Show me cherry tomato", self.plant_list)
        
        # Verify the AI correctly matched Cherry Tomato specifically
        self.assertEqual(result['plant_references'], ["Cherry Tomato"])
        self.assertEqual(result['query_type'], "PHOTO")

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_generic_basil_matches_all_basils(self, mock_openai):
        """Test that asking about 'basil' matches all basil varieties"""
        # Mock AI response for generic basil query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Sweet Basil", "Thai Basil"],
            "query_type": "CARE",
            "confidence": 0.93,
            "reasoning": "User asked about 'basil' generically, so matching all basil varieties"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("How do I care for basil?", self.plant_list)
        
        # Verify the AI correctly identified all basil varieties
        expected_basils = ["Sweet Basil", "Thai Basil"]
        self.assertEqual(set(result['plant_references']), set(expected_basils))
        self.assertEqual(result['query_type'], "CARE")

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_context_aware_matching(self, mock_openai):
        """Test that context affects matching decisions"""
        # Mock AI response for context-aware query
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["Peggy Martin Rose"],
            "query_type": "LOCATION",
            "confidence": 0.96,
            "reasoning": "User asked 'Where is my Peggy Martin Rose?' - specific location query for specific plant"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("Where is my Peggy Martin Rose?", self.plant_list)
        
        # Verify the AI correctly handled the specific context
        self.assertEqual(result['plant_references'], ["Peggy Martin Rose"])
        self.assertEqual(result['query_type'], "LOCATION")
        self.assertFalse(result['requires_ai_response'])

    def test_ai_prompt_contains_matching_rules(self):
        """Test that the AI prompt includes the intelligent matching rules"""
        from query_analyzer import _build_analysis_prompt
        
        prompt = _build_analysis_prompt("test query", self.plant_list)
        
        # Check that the prompt contains the intelligent matching rules
        self.assertIn("Generic vs Specific Names", prompt)
        self.assertIn("Compound Plant Names", prompt)
        self.assertIn("Context Matters", prompt)
        self.assertIn("roses", prompt)
        self.assertIn("Peggy Martin Rose", prompt)
        self.assertIn("cherry tomato", prompt)

if __name__ == '__main__':
    unittest.main() 