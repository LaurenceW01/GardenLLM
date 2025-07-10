"""
Test Phase 5: Integration and Optimization

This test suite verifies:
- Unified query processing pipeline
- Performance monitoring
- Error handling and graceful degradation
- Two-AI-call workflow optimization
"""

import unittest
from unittest.mock import patch, Mock
import sys
import os
import time

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_response import (
    process_query_with_pipeline, 
    get_chat_response_with_analyzer_optimized,
    handle_ai_enhanced_query_optimized,
    build_ai_context_with_plants,
    generate_ai_response_with_context,
    generate_fallback_ai_response,
    get_performance_metrics,
    log_performance_summary,
    performance_monitor
)
from query_analyzer import QueryType

class TestPhase5Integration(unittest.TestCase):
    """Test Phase 5 integration and optimization features"""

    def setUp(self):
        """Set up test data"""
        self.sample_plant_list = [
            "Peggy Martin Rose",
            "Cherry Tomato", 
            "Sweet Basil",
            "Thai Basil",
            "Roma Tomato"
        ]

    def tearDown(self):
        """Reset performance monitor after each test"""
        performance_monitor.metrics = {
            'total_queries': 0,
            'ai_analysis_calls': 0,
            'ai_response_calls': 0,
            'database_only_queries': 0,
            'ai_enhanced_queries': 0,
            'average_analysis_time': 0.0,
            'average_response_time': 0.0,
            'total_processing_time': 0.0,
            'errors': 0
        }

    @patch('chat_response.analyze_query')
    @patch('chat_response.handle_database_only_query')
    def test_unified_pipeline_database_only(self, mock_db_handler, mock_analyze):
        """Test unified pipeline for database-only queries"""
        # Mock analysis result for database-only query
        mock_analyze.return_value = {
            'query_type': QueryType.LOCATION,
            'plant_references': ['Peggy Martin Rose'],
            'requires_ai_response': False,
            'confidence': 0.95
        }
        
        # Mock database handler
        mock_db_handler.return_value = "Your Peggy Martin Rose is located in the front garden."
        
        # Test the pipeline
        result = process_query_with_pipeline("Where is my Peggy Martin Rose?")
        
        # Verify results
        self.assertEqual(result, "Your Peggy Martin Rose is located in the front garden.")
        mock_analyze.assert_called_once()
        mock_db_handler.assert_called_once()
        
        # Check performance metrics
        metrics = get_performance_metrics()
        self.assertEqual(metrics['total_queries'], 1)
        self.assertEqual(metrics['ai_analysis_calls'], 1)
        self.assertEqual(metrics['database_only_queries'], 1)
        self.assertEqual(metrics['ai_enhanced_queries'], 0)

    @patch('chat_response.analyze_query')
    @patch('chat_response.handle_ai_enhanced_query_optimized')
    def test_unified_pipeline_ai_enhanced(self, mock_ai_handler, mock_analyze):
        """Test unified pipeline for AI-enhanced queries"""
        # Mock analysis result for AI-enhanced query
        mock_analyze.return_value = {
            'query_type': QueryType.CARE,
            'plant_references': ['Sweet Basil'],
            'requires_ai_response': True,
            'confidence': 0.92
        }
        
        # Mock AI handler
        mock_ai_handler.return_value = "To care for your Sweet Basil, water regularly and provide full sun."
        
        # Test the pipeline
        result = process_query_with_pipeline("How do I care for my basil?")
        
        # Verify results
        self.assertEqual(result, "To care for your Sweet Basil, water regularly and provide full sun.")
        mock_analyze.assert_called_once()
        mock_ai_handler.assert_called_once()
        
        # Check performance metrics
        metrics = get_performance_metrics()
        self.assertEqual(metrics['total_queries'], 1)
        self.assertEqual(metrics['ai_analysis_calls'], 1)
        self.assertEqual(metrics['ai_enhanced_queries'], 1)
        self.assertEqual(metrics['database_only_queries'], 0)

    @patch('chat_response.analyze_query')
    def test_unified_pipeline_error_handling(self, mock_analyze):
        """Test unified pipeline error handling and graceful degradation"""
        # Mock analysis to raise an exception
        mock_analyze.side_effect = Exception("AI analysis failed")
        
        # Test the pipeline - should fall back to legacy method
        with patch('chat_response.get_chat_response_legacy') as mock_legacy:
            mock_legacy.return_value = "Fallback response from legacy method"
            
            result = process_query_with_pipeline("Test query")
            
            # Verify fallback was used
            self.assertEqual(result, "Fallback response from legacy method")
            mock_legacy.assert_called_once()
            
            # Check error metrics
            metrics = get_performance_metrics()
            self.assertEqual(metrics['errors'], 1)

    @patch('chat_response.analyze_query')
    def test_unified_pipeline_double_failure(self, mock_analyze):
        """Test unified pipeline when both analyzer and legacy method fail"""
        # Mock both methods to fail
        mock_analyze.side_effect = Exception("AI analysis failed")
        
        with patch('chat_response.get_chat_response_legacy') as mock_legacy:
            mock_legacy.side_effect = Exception("Legacy method failed")
            
            result = process_query_with_pipeline("Test query")
            
            # Should return error message
            self.assertIn("technical difficulties", result.lower())
            
            # Check error metrics
            metrics = get_performance_metrics()
            self.assertEqual(metrics['errors'], 1)

    @patch('chat_response.analyze_query')
    @patch('chat_response.build_ai_context_with_plants')
    @patch('chat_response.generate_ai_response_with_context')
    def test_optimized_ai_enhanced_processing(self, mock_generate, mock_context, mock_analyze):
        """Test optimized AI-enhanced query processing with performance monitoring"""
        # Mock analysis result
        mock_analyze.return_value = {
            'query_type': QueryType.CARE,
            'plant_references': ['Sweet Basil'],
            'requires_ai_response': True,
            'confidence': 0.92
        }
        
        # Mock context building
        mock_context.return_value = "Context with plant data and Houston climate"
        
        # Mock AI response generation
        mock_generate.return_value = "Care advice for Sweet Basil in Houston climate"
        
        # Test optimized processing
        result = get_chat_response_with_analyzer_optimized("How do I care for my basil?")
        
        # Verify results
        self.assertEqual(result, "Care advice for Sweet Basil in Houston climate")
        mock_context.assert_called_once()
        mock_generate.assert_called_once()
        
        # Check performance metrics
        metrics = get_performance_metrics()
        self.assertEqual(metrics['ai_analysis_calls'], 1)
        self.assertEqual(metrics['ai_response_calls'], 1)

    @patch('chat_response.get_plant_data')
    def test_build_ai_context_with_plants(self, mock_get_plant_data):
        """Test building AI context with plant data"""
        # Mock plant data
        mock_get_plant_data.return_value = [
            {
                'name': 'Sweet Basil',
                'location': 'Herb garden',
                'care_info': 'Full sun, regular watering'
            }
        ]
        
        # Test context building
        context = build_ai_context_with_plants(
            QueryType.CARE, 
            ['Sweet Basil'], 
            "How do I care for my basil?"
        )
        
        # Verify context contains expected elements
        self.assertIn("Houston, Texas (Zone 9a)", context)
        self.assertIn("Sweet Basil", context)
        self.assertIn("Herb garden", context)
        self.assertIn("Plant care and maintenance advice", context)
        
        mock_get_plant_data.assert_called_once_with(['Sweet Basil'])

    @patch('chat_response.openai_client.chat.completions.create')
    def test_generate_ai_response_with_context(self, mock_openai):
        """Test AI response generation with context"""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Here's care advice for your basil in Houston."
        mock_openai.return_value = mock_response
        
        # Test response generation
        result = generate_ai_response_with_context(
            QueryType.CARE,
            "Context with plant data",
            "How do I care for my basil?"
        )
        
        # Verify result
        self.assertEqual(result, "Here's care advice for your basil in Houston.")
        mock_openai.assert_called_once()

    @patch('chat_response.openai_client.chat.completions.create')
    def test_generate_fallback_ai_response(self, mock_openai):
        """Test fallback AI response generation"""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "I can help with your gardening question."
        mock_openai.return_value = mock_response
        
        # Test fallback response
        result = generate_fallback_ai_response("How do I grow tomatoes?")
        
        # Verify result
        self.assertEqual(result, "I can help with your gardening question.")
        mock_openai.assert_called_once()

    @patch('chat_response.openai_client.chat.completions.create')
    def test_fallback_ai_response_failure(self, mock_openai):
        """Test fallback AI response when it also fails"""
        # Mock AI failure
        mock_openai.side_effect = Exception("AI service unavailable")
        
        # Test fallback response
        result = generate_fallback_ai_response("How do I grow tomatoes?")
        
        # Should return error message
        self.assertIn("technical difficulties", result.lower())

    def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        # Reset metrics
        performance_monitor.metrics = {
            'total_queries': 0,
            'ai_analysis_calls': 0,
            'ai_response_calls': 0,
            'database_only_queries': 0,
            'ai_enhanced_queries': 0,
            'average_analysis_time': 0.0,
            'average_response_time': 0.0,
            'total_processing_time': 0.0,
            'errors': 0
        }
        
        # Test timer functionality
        start_time = performance_monitor.start_timer()
        time.sleep(0.01)  # Small delay
        elapsed = time.time() - start_time
        
        # Test metric recording
        performance_monitor.record_metric('total_queries')
        performance_monitor.record_metric('ai_analysis_calls')
        performance_monitor.update_average('average_analysis_time', 1.5, 1)
        
        # Get metrics
        metrics = get_performance_metrics()
        
        # Verify metrics
        self.assertEqual(metrics['total_queries'], 1)
        self.assertEqual(metrics['ai_analysis_calls'], 1)
        self.assertEqual(metrics['average_analysis_time'], 1.5)

    def test_performance_metrics_accumulation(self):
        """Test that performance metrics accumulate correctly"""
        # Reset metrics
        performance_monitor.metrics = {
            'total_queries': 0,
            'ai_analysis_calls': 0,
            'ai_response_calls': 0,
            'database_only_queries': 0,
            'ai_enhanced_queries': 0,
            'average_analysis_time': 0.0,
            'average_response_time': 0.0,
            'total_processing_time': 0.0,
            'errors': 0
        }
        
        # Record multiple metrics
        performance_monitor.record_metric('total_queries')
        performance_monitor.record_metric('total_queries')
        performance_monitor.record_metric('ai_analysis_calls')
        performance_monitor.record_metric('errors')
        
        # Update averages
        performance_monitor.update_average('average_analysis_time', 1.0, 1)
        performance_monitor.update_average('average_analysis_time', 2.0, 2)
        
        # Get metrics
        metrics = get_performance_metrics()
        
        # Verify accumulation
        self.assertEqual(metrics['total_queries'], 2)
        self.assertEqual(metrics['ai_analysis_calls'], 1)
        self.assertEqual(metrics['errors'], 1)
        self.assertEqual(metrics['average_analysis_time'], 1.5)  # (1.0 + 2.0) / 2

    @patch('chat_response.analyze_query')
    @patch('chat_response.handle_ai_enhanced_query_optimized')
    def test_two_ai_call_workflow(self, mock_ai_handler, mock_analyze):
        """Test the complete two-AI-call workflow"""
        # Mock first AI call (analysis)
        mock_analyze.return_value = {
            'query_type': QueryType.CARE,
            'plant_references': ['Sweet Basil'],
            'requires_ai_response': True,
            'confidence': 0.92
        }
        
        # Mock second AI call (response)
        mock_ai_handler.return_value = "Care advice for Sweet Basil"
        
        # Test the complete workflow using the full pipeline
        result = process_query_with_pipeline("How do I care for my basil?")
        
        # Verify both AI calls were made
        mock_analyze.assert_called_once()
        mock_ai_handler.assert_called_once()
        
        # Verify result
        self.assertEqual(result, "Care advice for Sweet Basil")
        # Note: We do not check ai_response_calls metric here because the handler is mocked and the metric is not incremented.

    def test_error_recovery_scenarios(self):
        """Test various error recovery scenarios"""
        # Test 1: Analysis fails, legacy succeeds
        with patch('chat_response.analyze_query') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            with patch('chat_response.get_chat_response_legacy') as mock_legacy:
                mock_legacy.return_value = "Legacy response"
                
                result = process_query_with_pipeline("Test query")
                self.assertEqual(result, "Legacy response")
        
        # Test 2: Both analysis and legacy fail
        with patch('chat_response.analyze_query') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            with patch('chat_response.get_chat_response_legacy') as mock_legacy:
                mock_legacy.side_effect = Exception("Legacy failed")
                
                result = process_query_with_pipeline("Test query")
                self.assertIn("technical difficulties", result.lower())

    def test_performance_logging(self):
        """Test performance logging functionality"""
        # This test verifies that logging doesn't crash
        try:
            log_performance_summary()
            # If we get here, logging worked
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Performance logging failed: {e}")

if __name__ == '__main__':
    unittest.main() 