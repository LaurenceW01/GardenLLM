"""
Test Phase 4: AI-Enhanced Query Processing

This test suite verifies that the new AI-enhanced query processing
correctly handles CARE, DIAGNOSIS, ADVICE, and GENERAL queries with database context.
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_response import (
    handle_ai_enhanced_query, 
    _build_ai_context, 
    _generate_ai_response, 
    _add_photo_urls_to_response
)
from query_analyzer import QueryType

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPhase4AIEnhancedQueries:
    """Test Phase 4 AI-enhanced query processing"""
    
    def test_build_ai_context_care_query(self):
        """Test context building for care queries"""
        plant_data = [
            {
                'Plant Name': 'Tomato',
                'Light Requirements': 'Full sun',
                'Watering Needs': 'Regular watering',
                'Soil Preferences': 'Well-draining soil',
                'Fertilizing Schedule': 'Monthly',
                'Pruning Instructions': 'Remove suckers',
                'Care Notes': 'Heat tolerant'
            }
        ]
        
        context = _build_ai_context(QueryType.CARE, plant_data, "How do I care for my tomato?")
        
        # Should include Houston climate info
        assert "Houston, Texas (Zone 9a)" in context
        assert "Hot and humid subtropical climate" in context
        
        # Should include care-specific plant info
        assert "Tomato:" in context
        assert "Light Requirements: Full sun" in context
        assert "Watering Needs: Regular watering" in context
        assert "Fertilizing Schedule: Monthly" in context
        assert "Pruning Instructions: Remove suckers" in context
        
        logger.info("✓ Care query context test passed")
    
    def test_build_ai_context_diagnosis_query(self):
        """Test context building for diagnosis queries"""
        plant_data = [
            {
                'Plant Name': 'Basil',
                'Light Requirements': 'Partial shade',
                'Watering Needs': 'Keep soil moist',
                'Soil Preferences': 'Rich soil',
                'Care Notes': 'Prone to fungal diseases'
            }
        ]
        
        context = _build_ai_context(QueryType.DIAGNOSIS, plant_data, "Why are my basil leaves turning yellow?")
        
        # Should include diagnosis-relevant plant info
        assert "Basil:" in context
        assert "Light Requirements: Partial shade" in context
        assert "Watering Needs: Keep soil moist" in context
        assert "Care Notes: Prone to fungal diseases" in context
        
        # Should not include non-diagnosis fields
        assert "Fertilizing Schedule" not in context
        
        logger.info("✓ Diagnosis query context test passed")
    
    def test_build_ai_context_advice_query(self):
        """Test context building for advice queries"""
        plant_data = [
            {
                'Plant Name': 'Lettuce',
                'Light Requirements': 'Partial shade',
                'Watering Needs': 'Consistent moisture',
                'Soil Preferences': 'Rich, well-draining',
                'Pruning Instructions': 'Harvest outer leaves',
                'Mulching Needs': 'Light mulch',
                'Spacing Requirements': '6-8 inches apart'
            }
        ]
        
        context = _build_ai_context(QueryType.ADVICE, plant_data, "How should I prune my lettuce?")
        
        # Should include advice-relevant plant info
        assert "Lettuce:" in context
        assert "Pruning Instructions: Harvest outer leaves" in context
        assert "Spacing Requirements: 6-8 inches apart" in context
        assert "Mulching Needs: Light mulch" in context
        
        logger.info("✓ Advice query context test passed")
    
    def test_build_ai_context_general_query(self):
        """Test context building for general queries"""
        plant_data = [
            {
                'Plant Name': 'Rose',
                'Light Requirements': 'Full sun',
                'Watering Needs': 'Deep watering',
                'Description': 'Beautiful flowering shrub',
                'Location': 'Garden Bed 1'
            }
        ]
        
        context = _build_ai_context(QueryType.GENERAL, plant_data, "Tell me about roses")
        
        # Should include all relevant plant info
        assert "Rose:" in context
        assert "Light Requirements: Full sun" in context
        assert "Description: Beautiful flowering shrub" in context
        assert "Location: Garden Bed 1" in context
        
        logger.info("✓ General query context test passed")
    
    def test_build_ai_context_no_plants(self):
        """Test context building when no plants are referenced"""
        context = _build_ai_context(QueryType.GENERAL, [], "What's the best time to plant vegetables?")
        
        # Should still include Houston climate info
        assert "Houston, Texas (Zone 9a)" in context
        assert "Hot and humid subtropical climate" in context
        
        # Should not include plant-specific info
        assert "Relevant plants in your garden:" not in context
        
        logger.info("✓ No plants context test passed")
    
    def test_generate_ai_response_care(self):
        """Test AI response generation for care queries"""
        context = "Location: Houston, Texas\nTomato: Light Requirements: Full sun"
        
        with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Water your tomato regularly and provide full sun exposure."
            mock_openai.return_value = mock_response
            
            result = _generate_ai_response(QueryType.CARE, context, "How do I care for my tomato?")
            
            assert "Water your tomato regularly" in result
            mock_openai.assert_called_once()
            
            # Check that the system prompt includes care-specific instructions
            call_args = mock_openai.call_args
            system_message = call_args[1]['messages'][0]['content']
            assert "plant care" in system_message.lower()
            assert "houston climate" in system_message.lower()
            
        logger.info("✓ Care AI response test passed")
    
    def test_generate_ai_response_diagnosis(self):
        """Test AI response generation for diagnosis queries"""
        context = "Location: Houston, Texas\nBasil: Care Notes: Prone to fungal diseases"
        
        with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Yellow leaves could indicate overwatering or fungal disease."
            mock_openai.return_value = mock_response
            
            result = _generate_ai_response(QueryType.DIAGNOSIS, context, "Why are my basil leaves yellow?")
            
            assert "Yellow leaves could indicate" in result
            mock_openai.assert_called_once()
            
            # Check that the system prompt includes diagnosis-specific instructions
            call_args = mock_openai.call_args
            system_message = call_args[1]['messages'][0]['content']
            assert "plant health expert" in system_message.lower()
            assert "diagnose plant problems" in system_message.lower()
            
        logger.info("✓ Diagnosis AI response test passed")
    
    def test_generate_ai_response_error_handling(self):
        """Test AI response generation error handling"""
        context = "Location: Houston, Texas"
        
        with patch('chat_response.openai_client.chat.completions.create', side_effect=Exception("API Error")):
            result = _generate_ai_response(QueryType.GENERAL, context, "Test question")
            
            assert "I'm sorry, I encountered an error" in result
            
        logger.info("✓ AI response error handling test passed")
    
    def test_add_photo_urls_to_response(self):
        """Test adding photo URLs to AI response"""
        response = "Here's some helpful information about your plants."
        plant_data = [
            {
                'Plant Name': 'Tomato',
                'Raw Photo URL': 'http://example.com/tomato.jpg'
            },
            {
                'Plant Name': 'Basil',
                'Raw Photo URL': 'https://photos.google.com/photo/ABC123?authuser=1'
            }
        ]
        
        result = _add_photo_urls_to_response(response, plant_data)
        
        assert "Here's some helpful information about your plants." in result
        assert "You can see a photo of Tomato here: http://example.com/tomato.jpg" in result
        assert "You can see a photo of Basil here: https://photos.google.com/photo/ABC123?authuser=0" in result
        
        logger.info("✓ Add photo URLs test passed")
    
    def test_add_photo_urls_no_photos(self):
        """Test adding photo URLs when no photos are available"""
        response = "Here's some helpful information."
        plant_data = [
            {
                'Plant Name': 'Tomato',
                'Raw Photo URL': ''
            }
        ]
        
        result = _add_photo_urls_to_response(response, plant_data)
        
        assert result == response  # Should be unchanged
        
        logger.info("✓ No photos test passed")
    
    def test_handle_ai_enhanced_query_care(self):
        """Test complete AI-enhanced query handling for care"""
        mock_plant_data = [
            {
                'Plant Name': 'Tomato',
                'Light Requirements': 'Full sun',
                'Watering Needs': 'Regular watering'
            }
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            with patch('chat_response._build_ai_context', return_value="Context"):
                with patch('chat_response._generate_ai_response', return_value="Care advice"):
                    with patch('chat_response._add_photo_urls_to_response', return_value="Care advice with photos"):
                        
                        result = handle_ai_enhanced_query(QueryType.CARE, ['tomato'], "How do I care for my tomato?")
                        
                        assert result == "Care advice with photos"
                        
        logger.info("✓ Complete care query test passed")
    
    def test_handle_ai_enhanced_query_no_plants(self):
        """Test AI-enhanced query handling when no plants are referenced"""
        with patch('chat_response._build_ai_context', return_value="Context"):
            with patch('chat_response._generate_ai_response', return_value="General advice"):
                with patch('chat_response._add_photo_urls_to_response', return_value="General advice"):
                    
                    result = handle_ai_enhanced_query(QueryType.GENERAL, [], "What's the best time to plant?")
                    
                    assert result == "General advice"
                    
        logger.info("✓ No plants AI query test passed")
    
    def test_handle_ai_enhanced_query_error_handling(self):
        """Test AI-enhanced query error handling"""
        with patch('chat_response.get_plant_data', side_effect=Exception("Database error")):
            with patch('chat_response.get_chat_response_legacy', return_value="Legacy response"):
                
                result = handle_ai_enhanced_query(QueryType.CARE, ['tomato'], "How do I care for my tomato?")
                
                assert result == "Legacy response"
                
        logger.info("✓ AI-enhanced query error handling test passed")

def run_phase4_tests():
    """Run all Phase 4 tests"""
    logger.info("Starting Phase 4 AI-Enhanced Query Tests...")
    
    test_instance = TestPhase4AIEnhancedQueries()
    
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
    
    logger.info(f"\nPhase 4 Test Results:")
    logger.info(f"✓ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All Phase 4 tests passed!")
        return True
    else:
        logger.error("💥 Some Phase 4 tests failed!")
        return False

if __name__ == "__main__":
    success = run_phase4_tests()
    sys.exit(0 if success else 1) 