"""
Test file for Query Analyzer Module (Phase 1)

This file contains unit tests for the query_analyzer module to ensure
the AI-powered query analysis functionality works correctly.

Author: GardenLLM Team
Date: December 2024
"""

import unittest
import json
from unittest.mock import Mock, patch
from query_analyzer import (
    analyze_query, 
    QueryType, 
    is_database_only_query, 
    is_ai_response_required,
    _build_analysis_prompt,
    _parse_analysis_response,
    _get_fallback_analysis
)

class TestQueryAnalyzer(unittest.TestCase):
    """Test cases for the Query Analyzer module"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_plant_list = ["tomato", "basil", "rose", "hibiscus", "lavender"]

    def test_query_type_constants(self):
        """Test that query type constants are properly defined"""
        self.assertEqual(QueryType.LOCATION, "LOCATION")
        self.assertEqual(QueryType.PHOTO, "PHOTO")
        self.assertEqual(QueryType.LIST, "LIST")
        self.assertEqual(QueryType.CARE, "CARE")
        self.assertEqual(QueryType.DIAGNOSIS, "DIAGNOSIS")
        self.assertEqual(QueryType.ADVICE, "ADVICE")
        self.assertEqual(QueryType.GENERAL, "GENERAL")

    def test_is_database_only_query(self):
        """Test database-only query classification"""
        self.assertTrue(is_database_only_query(QueryType.LOCATION))
        self.assertTrue(is_database_only_query(QueryType.PHOTO))
        self.assertTrue(is_database_only_query(QueryType.LIST))
        self.assertFalse(is_database_only_query(QueryType.CARE))
        self.assertFalse(is_database_only_query(QueryType.DIAGNOSIS))
        self.assertFalse(is_database_only_query(QueryType.ADVICE))
        self.assertFalse(is_database_only_query(QueryType.GENERAL))

    def test_is_ai_response_required(self):
        """Test AI response requirement classification"""
        self.assertFalse(is_ai_response_required(QueryType.LOCATION))
        self.assertFalse(is_ai_response_required(QueryType.PHOTO))
        self.assertFalse(is_ai_response_required(QueryType.LIST))
        self.assertTrue(is_ai_response_required(QueryType.CARE))
        self.assertTrue(is_ai_response_required(QueryType.DIAGNOSIS))
        self.assertTrue(is_ai_response_required(QueryType.ADVICE))
        self.assertTrue(is_ai_response_required(QueryType.GENERAL))

    def test_build_analysis_prompt(self):
        """Test prompt building functionality"""
        query = "Where are my tomatoes?"
        prompt = _build_analysis_prompt(query, self.sample_plant_list)
        
        # Check that prompt contains expected elements
        self.assertIn(query, prompt)
        self.assertIn("tomato, basil, rose, hibiscus, lavender", prompt)
        self.assertIn("LOCATION", prompt)
        self.assertIn("PHOTO", prompt)
        self.assertIn("LIST", prompt)
        self.assertIn("CARE", prompt)
        self.assertIn("DIAGNOSIS", prompt)
        self.assertIn("ADVICE", prompt)
        self.assertIn("GENERAL", prompt)

    def test_parse_analysis_response_valid(self):
        """Test parsing of valid AI response"""
        valid_response = '''
        {
            "plant_references": ["tomato"],
            "query_type": "LOCATION",
            "confidence": 0.95,
            "reasoning": "User is asking about location of tomatoes"
        }
        '''
        
        result = _parse_analysis_response(valid_response)
        
        self.assertEqual(result['plant_references'], ["tomato"])
        self.assertEqual(result['query_type'], "LOCATION")
        self.assertEqual(result['confidence'], 0.95)
        self.assertEqual(result['reasoning'], "User is asking about location of tomatoes")

    def test_parse_analysis_response_with_code_blocks(self):
        """Test parsing of AI response with code blocks"""
        response_with_blocks = '''
        ```json
        {
            "plant_references": ["basil"],
            "query_type": "CARE",
            "confidence": 0.88,
            "reasoning": "User is asking about care for basil"
        }
        ```
        '''
        
        result = _parse_analysis_response(response_with_blocks)
        
        self.assertEqual(result['plant_references'], ["basil"])
        self.assertEqual(result['query_type'], "CARE")
        self.assertEqual(result['confidence'], 0.88)

    def test_parse_analysis_response_invalid_json(self):
        """Test parsing of invalid JSON response"""
        invalid_response = "This is not valid JSON"
        
        result = _parse_analysis_response(invalid_response)
        
        # Should return fallback analysis
        self.assertIn('query_type', result)
        self.assertIn('confidence', result)
        self.assertIn('plant_references', result)

    def test_parse_analysis_response_missing_fields(self):
        """Test parsing of response with missing fields"""
        incomplete_response = '''
        {
            "plant_references": ["rose"]
        }
        '''
        
        result = _parse_analysis_response(incomplete_response)
        
        # Should have default values for missing fields
        self.assertEqual(result['plant_references'], ["rose"])
        self.assertEqual(result['query_type'], "GENERAL")  # Default
        self.assertEqual(result['confidence'], 0.5)  # Default

    def test_parse_analysis_response_invalid_query_type(self):
        """Test parsing of response with invalid query type"""
        invalid_type_response = '''
        {
            "plant_references": ["hibiscus"],
            "query_type": "INVALID_TYPE",
            "confidence": 0.75
        }
        '''
        
        result = _parse_analysis_response(invalid_type_response)
        
        # Should default to GENERAL
        self.assertEqual(result['query_type'], "GENERAL")

    def test_get_fallback_analysis(self):
        """Test fallback analysis functionality"""
        # Test list query
        list_query = "What plants do I have?"
        result = _get_fallback_analysis(list_query)
        self.assertEqual(result['query_type'], "LIST")
        self.assertFalse(result['requires_ai_response'])
        
        # Test location query
        location_query = "Where are my tomatoes?"
        result = _get_fallback_analysis(location_query)
        self.assertEqual(result['query_type'], "LOCATION")
        self.assertFalse(result['requires_ai_response'])
        
        # Test photo query
        photo_query = "Show me my roses"
        result = _get_fallback_analysis(photo_query)
        self.assertEqual(result['query_type'], "PHOTO")
        self.assertFalse(result['requires_ai_response'])
        
        # Test general query
        general_query = "How do I start a garden?"
        result = _get_fallback_analysis(general_query)
        self.assertEqual(result['query_type'], "GENERAL")
        self.assertTrue(result['requires_ai_response'])

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_analyze_query_success(self, mock_openai):
        """Test successful query analysis with AI"""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plant_references": ["tomato", "basil"],
            "query_type": "CARE",
            "confidence": 0.92,
            "reasoning": "User is asking about care for multiple plants"
        }
        '''
        mock_openai.return_value = mock_response
        
        # Test the analysis
        result = analyze_query("How do I care for my tomatoes and basil?", self.sample_plant_list)
        
        # Verify the result
        self.assertEqual(result['plant_references'], ["tomato", "basil"])
        self.assertEqual(result['query_type'], "CARE")
        self.assertEqual(result['confidence'], 0.92)
        self.assertTrue(result['requires_ai_response'])
        self.assertEqual(result['original_query'], "How do I care for my tomatoes and basil?")
        self.assertEqual(result['plant_list_provided'], 5)
        
        # Verify AI was called
        mock_openai.assert_called_once()

    @patch('query_analyzer.openai_client.chat.completions.create')
    def test_analyze_query_ai_failure(self, mock_openai):
        """Test query analysis when AI call fails"""
        # Mock AI failure
        mock_openai.side_effect = Exception("AI API error")
        
        # Test the analysis
        result = analyze_query("Where are my roses?")
        
        # Should return fallback analysis
        self.assertIn('query_type', result)
        self.assertIn('confidence', result)
        self.assertIn('plant_references', result)
        self.assertEqual(result['original_query'], "Where are my roses?")

    def test_analyze_query_database_only_types(self):
        """Test that database-only query types are correctly identified"""
        database_only_types = [QueryType.LOCATION, QueryType.PHOTO, QueryType.LIST]
        
        for query_type in database_only_types:
            result = {
                'plant_references': [],
                'query_type': query_type,
                'confidence': 0.8
            }
            
            # Determine if AI response is required
            requires_ai = result['query_type'] in [
                QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL
            ]
            
            self.assertFalse(requires_ai, f"Query type {query_type} should not require AI response")

    def test_analyze_query_ai_required_types(self):
        """Test that AI-required query types are correctly identified"""
        ai_required_types = [QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL]
        
        for query_type in ai_required_types:
            result = {
                'plant_references': [],
                'query_type': query_type,
                'confidence': 0.8
            }
            
            # Determine if AI response is required
            requires_ai = result['query_type'] in [
                QueryType.CARE, QueryType.DIAGNOSIS, QueryType.ADVICE, QueryType.GENERAL
            ]
            
            self.assertTrue(requires_ai, f"Query type {query_type} should require AI response")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 