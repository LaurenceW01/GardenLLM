"""
Test Phase 4 Integration: Real AI-Enhanced Query Processing

This test verifies that Phase 4 AI-enhanced query processing
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

class TestPhase4Integration:
    """Test Phase 4 integration with real queries"""
    
    def test_care_query_integration(self):
        """Test care query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {
                'Plant Name': 'Tomato',
                'Light Requirements': 'Full sun',
                'Watering Needs': 'Regular watering',
                'Soil Preferences': 'Well-draining soil',
                'Fertilizing Schedule': 'Monthly',
                'Care Notes': 'Heat tolerant'
            }
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "For your tomato in Houston's climate, provide full sun and water regularly. The heat tolerance will help during our hot summers."
                mock_openai.return_value = mock_response
                
                # Test various care query formats
                care_queries = [
                    "How do I care for my tomato?",
                    "What does my tomato need?",
                    "How should I water my tomato?",
                    "Care tips for tomato plants"
                ]
                
                for query in care_queries:
                    result = get_chat_response(query)
                    logger.info(f"Query: '{query}'")
                    logger.info(f"Result: {result[:100]}...")
                    
                    # Should contain care advice
                    assert "tomato" in result.lower()
                    assert "houston" in result.lower() or "climate" in result.lower()
                    
                logger.info("✓ Care query integration test passed")
    
    def test_diagnosis_query_integration(self):
        """Test diagnosis query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {
                'Plant Name': 'Basil',
                'Light Requirements': 'Partial shade',
                'Watering Needs': 'Keep soil moist',
                'Care Notes': 'Prone to fungal diseases in humid conditions'
            }
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "Yellow leaves on your basil could be due to overwatering or fungal disease, which is common in Houston's humid climate."
                mock_openai.return_value = mock_response
                
                # Test various diagnosis query formats
                diagnosis_queries = [
                    "Why are my basil leaves turning yellow?",
                    "What's wrong with my basil?",
                    "My basil looks sick, what should I do?",
                    "Diagnose my basil plant problems"
                ]
                
                for query in diagnosis_queries:
                    result = get_chat_response(query)
                    logger.info(f"Query: '{query}'")
                    logger.info(f"Result: {result[:100]}...")
                    
                    # Should contain diagnosis information
                    assert "basil" in result.lower()
                    assert "yellow" in result.lower() or "disease" in result.lower()
                    
                logger.info("✓ Diagnosis query integration test passed")
    
    def test_advice_query_integration(self):
        """Test advice query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {
                'Plant Name': 'Lettuce',
                'Light Requirements': 'Partial shade',
                'Watering Needs': 'Consistent moisture',
                'Pruning Instructions': 'Harvest outer leaves',
                'Spacing Requirements': '6-8 inches apart'
            }
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "For your lettuce in Houston, provide partial shade and consistent moisture. Harvest outer leaves to encourage new growth."
                mock_openai.return_value = mock_response
                
                # Test various advice query formats
                advice_queries = [
                    "How should I prune my lettuce?",
                    "Best practices for growing lettuce",
                    "Advice for lettuce care",
                    "Tips for lettuce maintenance"
                ]
                
                for query in advice_queries:
                    result = get_chat_response(query)
                    logger.info(f"Query: '{query}'")
                    logger.info(f"Result: {result[:100]}...")
                    
                    # Should contain advice
                    assert "lettuce" in result.lower()
                    
                logger.info("✓ Advice query integration test passed")
    
    def test_general_query_integration(self):
        """Test general query through main chat system"""
        # Mock plant data
        mock_plant_data = [
            {
                'Plant Name': 'Rose',
                'Light Requirements': 'Full sun',
                'Description': 'Beautiful flowering shrub',
                'Location': 'Garden Bed 1'
            }
        ]
        
        with patch('chat_response.get_plant_data', return_value=mock_plant_data):
            with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "Roses are beautiful flowering shrubs that thrive in Houston's climate. They need full sun and regular care."
                mock_openai.return_value = mock_response
                
                # Test various general query formats
                general_queries = [
                    "Tell me about roses",
                    "What are roses like?",
                    "Information about rose plants",
                    "General facts about roses"
                ]
                
                for query in general_queries:
                    result = get_chat_response(query)
                    logger.info(f"Query: '{query}'")
                    logger.info(f"Result: {result[:100]}...")
                    
                    # Should contain general information
                    assert "rose" in result.lower()
                    
                logger.info("✓ General query integration test passed")
    
    def test_general_query_no_plants(self):
        """Test general query with no specific plants"""
        with patch('chat_response.get_plant_data', return_value=[]):
            with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "In Houston's climate, the best time to plant vegetables is in early spring (February-March) or fall (September-October)."
                mock_openai.return_value = mock_response
                
                result = get_chat_response("What's the best time to plant vegetables?")
                logger.info(f"Query: 'What's the best time to plant vegetables?'")
                logger.info(f"Result: {result[:100]}...")
                
                # Should contain general gardening advice
                assert "houston" in result.lower() or "climate" in result.lower()
                
                logger.info("✓ General query no plants test passed")
    
    def test_mixed_query_types_phase4(self):
        """Test that different query types are handled correctly in Phase 4"""
        # Mock different responses for different query types
        def mock_openai_response(*args, **kwargs):
            messages = kwargs['messages']
            user_content = messages[1]['content']
            
            if 'care' in user_content.lower() or 'water' in user_content.lower():
                return MagicMock(choices=[MagicMock(message=MagicMock(content="Care advice for your plants"))])
            elif 'diagnosis' in user_content.lower() or 'yellow' in user_content.lower():
                return MagicMock(choices=[MagicMock(message=MagicMock(content="Diagnosis: This could be a disease"))])
            elif 'advice' in user_content.lower() or 'prune' in user_content.lower():
                return MagicMock(choices=[MagicMock(message=MagicMock(content="Advice: Prune carefully"))])
            else:
                return MagicMock(choices=[MagicMock(message=MagicMock(content="General information about plants"))])
        
        with patch('chat_response.get_plant_data', return_value=[{'Plant Name': 'Test Plant'}]):
            with patch('chat_response.openai_client.chat.completions.create', side_effect=mock_openai_response):
                
                # Test care query
                care_result = get_chat_response("How do I care for my plants?")
                assert "care advice" in care_result.lower()
                
                # Test diagnosis query
                diagnosis_result = get_chat_response("Why are my leaves yellow?")
                assert "diagnosis" in diagnosis_result.lower()
                
                # Test advice query
                advice_result = get_chat_response("How should I prune?")
                assert "advice" in advice_result.lower()
                
                # Test general query
                general_result = get_chat_response("Tell me about plants")
                assert "general information" in general_result.lower()
                
                logger.info("✓ Mixed query types Phase 4 test passed")

def run_phase4_integration_tests():
    """Run all Phase 4 integration tests"""
    logger.info("Starting Phase 4 Integration Tests...")
    
    test_instance = TestPhase4Integration()
    
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
    
    logger.info(f"\nPhase 4 Integration Test Results:")
    logger.info(f"✓ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All Phase 4 integration tests passed!")
        return True
    else:
        logger.error("💥 Some Phase 4 integration tests failed!")
        return False

if __name__ == "__main__":
    success = run_phase4_integration_tests()
    sys.exit(0 if success else 1) 