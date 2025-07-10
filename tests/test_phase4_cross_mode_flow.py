#!/usr/bin/env python3
"""
Phase 4 Cross-Mode Conversation Flow Test Suite

This test suite verifies the Phase 4 enhancements including:
- Mode-specific system prompts
- Cross-mode context preservation
- Conversation context summarization
- Enhanced conversation metadata
- Seamless mode transitions
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation_manager import ConversationManager
from chat_response import generate_ai_response_with_context


class Phase4CrossModeFlowTests(unittest.TestCase):
    """Test suite for Phase 4 cross-mode conversation flow enhancements"""
    
    def setUp(self):
        """Set up test environment"""
        print(f"\n{'='*60}")
        print(f"Phase 4 Cross-Mode Flow Test: {self._testMethodName}")
        print(f"{'='*60}")
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager()
    
    def test_mode_specific_system_prompts(self):
        """Test mode-specific system prompt generation"""
        print("Testing mode-specific system prompts...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add some conversation context
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I have tomatoes in my garden',
            'mode': 'database'
        })
        
        # Get conversation context
        context = self.conversation_manager.get_conversation_context(conversation_id)
        
        # Test different mode prompts
        database_prompt = self.conversation_manager.get_mode_specific_system_prompt('database', context)
        image_prompt = self.conversation_manager.get_mode_specific_system_prompt('image_analysis', context)
        general_prompt = self.conversation_manager.get_mode_specific_system_prompt('general', context)
        
        # Verify prompts are different and contain appropriate content
        self.assertIn('garden database', database_prompt.lower())
        self.assertIn('plant identification', image_prompt.lower())
        self.assertIn('gardening assistant', general_prompt.lower())
        
        # Verify context is included
        self.assertIn('tomatoes', database_prompt.lower())
        
        print("PASS: Mode-specific system prompts test passed")
    
    def test_conversation_context_summary(self):
        """Test conversation context summarization"""
        print("Testing conversation context summarization...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add messages with various topics
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'How do I care for my tomato plants?',
            'mode': 'database'
        })
        
        self.conversation_manager.add_message(conversation_id, {
            'role': 'assistant',
            'content': 'Tomatoes need full sun and regular watering.',
            'mode': 'database'
        })
        
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'What about watering frequency?',
            'mode': 'database'
        })
        
        # Get context summary
        summary = self.conversation_manager.get_conversation_context_summary(conversation_id)
        
        # Verify summary contains key information
        self.assertIn('database', summary.lower())
        self.assertIn('tomato', summary.lower())
        self.assertIn('plant', summary.lower())
        self.assertIn('water', summary.lower())
        self.assertIn('Messages: 3', summary)
        
        print("PASS: Conversation context summarization test passed")
    
    def test_cross_mode_context_extraction(self):
        """Test cross-mode context extraction"""
        print("Testing cross-mode context extraction...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add messages with preferences and topics
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I prefer plants that need full sun',
            'mode': 'database'
        })
        
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I have tomatoes and peppers in my garden',
            'mode': 'database'
        })
        
        # Get cross-mode context
        cross_context = self.conversation_manager.get_cross_mode_context(conversation_id)
        
        # Verify context extraction
        self.assertTrue(cross_context['available'])
        self.assertEqual(cross_context['mode'], 'database')
        self.assertIn('tomato', cross_context['recent_topics'])
        self.assertIn('pepper', cross_context['recent_topics'])
        self.assertEqual(cross_context['user_preferences']['light'], 'full sun')
        
        print("PASS: Cross-mode context extraction test passed")
    
    def test_mode_transition_context_creation(self):
        """Test mode transition context creation"""
        print("Testing mode transition context creation...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add initial context
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I have tomatoes in my garden',
            'mode': 'database'
        })
        
        # Create mode transition context
        transition_context = self.conversation_manager.create_mode_transition_context(conversation_id, 'image_analysis')
        
        # Verify transition context
        self.assertEqual(transition_context['conversation_id'], conversation_id)
        self.assertEqual(transition_context['previous_mode'], 'database')
        self.assertEqual(transition_context['new_mode'], 'image_analysis')
        self.assertIn('system_prompt', transition_context)
        self.assertIn('context_summary', transition_context)
        self.assertIn('recent_topics', transition_context)
        self.assertIn('user_preferences', transition_context)
        self.assertIn('transition_timestamp', transition_context)
        
        # Verify system prompt is mode-specific
        self.assertIn('plant identification', transition_context['system_prompt'].lower())
        
        print("PASS: Mode transition context creation test passed")
    
    def test_conversation_metadata_tracking(self):
        """Test enhanced conversation metadata tracking"""
        print("Testing enhanced conversation metadata tracking...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Create conversation with initial metadata
        initial_metadata = {
            'user_preferences': {'light': 'full sun', 'water': 'frequent'},
            'garden_location': 'Houston, TX',
            'experience_level': 'intermediate'
        }
        
        success = self.conversation_manager.create_conversation_with_metadata(conversation_id, initial_metadata)
        self.assertTrue(success)
        
        # Get conversation context
        context = self.conversation_manager.get_conversation_context(conversation_id)
        
        # Verify metadata is preserved
        self.assertIn('user_preferences', context['metadata'])
        self.assertIn('garden_location', context['metadata'])
        self.assertIn('experience_level', context['metadata'])
        
        print("PASS: Enhanced conversation metadata tracking test passed")
    
    def test_seamless_mode_transitions(self):
        """Test seamless mode transitions with context preservation"""
        print("Testing seamless mode transitions...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Start in database mode
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I have tomatoes in my garden',
            'mode': 'database'
        })
        
        # Switch to image analysis mode
        transition_context = self.conversation_manager.create_mode_transition_context(conversation_id, 'image_analysis')
        
        # Add message in image analysis mode
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'Is this the same type of tomato?',
            'mode': 'image_analysis'
        })
        
        # Switch back to database mode
        transition_context2 = self.conversation_manager.create_mode_transition_context(conversation_id, 'database')
        
        # Verify context is preserved across transitions
        self.assertIn('tomato', transition_context['recent_topics'])
        self.assertIn('tomato', transition_context2['recent_topics'])
        
        # Verify mode transitions are tracked
        context = self.conversation_manager.get_conversation_context(conversation_id)
        self.assertEqual(context['metadata']['mode'], 'database')
        
        print("PASS: Seamless mode transitions test passed")
    
    def test_enhanced_ai_response_with_mode_context(self):
        """Test enhanced AI response generation with mode-specific context"""
        print("Testing enhanced AI response with mode context...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add conversation context
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I have tomatoes in my garden',
            'mode': 'database'
        })
        
        # Mock the OpenAI client
        with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Based on your garden context, here's advice for your tomatoes..."
            mock_openai.return_value = mock_response
            
            # Generate AI response with context
            response = generate_ai_response_with_context(
                query_type='CARE',
                context='You have tomatoes in your garden',
                message='How should I care for them?',
                conversation_id=conversation_id
            )
            
            # Verify the function was called
            mock_openai.assert_called_once()
            
            # Verify response contains context
            self.assertIn('tomatoes', response.lower())
        
        print("PASS: Enhanced AI response with mode context test passed")
    
    def test_context_summary_length_limits(self):
        """Test context summary respects length limits"""
        print("Testing context summary length limits...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add a long message
        long_message = "This is a very long message about gardening that contains many words and should be truncated when summarized " * 10
        
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': long_message,
            'mode': 'database'
        })
        
        # Get summary with short limit
        summary = self.conversation_manager.get_conversation_context_summary(conversation_id, max_length=50)
        
        # Verify summary is within limit
        self.assertLessEqual(len(summary), 53)  # 50 + 3 for "..."
        
        print("PASS: Context summary length limits test passed")
    
    def test_user_preferences_extraction(self):
        """Test user preferences extraction from conversation"""
        print("Testing user preferences extraction...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add messages with preferences
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I prefer plants that need full sun and frequent watering',
            'mode': 'database'
        })
        
        self.conversation_manager.add_message(conversation_id, {
            'role': 'user',
            'content': 'I like drought tolerant plants too',
            'mode': 'database'
        })
        
        # Get cross-mode context
        cross_context = self.conversation_manager.get_cross_mode_context(conversation_id)
        
        # Verify preferences are extracted
        self.assertEqual(cross_context['user_preferences']['light'], 'full sun')
        self.assertEqual(cross_context['user_preferences']['water'], 'frequent')
        
        print("PASS: User preferences extraction test passed")
    
    def test_conversation_continuity_across_modes(self):
        """Test conversation continuity across multiple mode switches"""
        print("Testing conversation continuity across modes...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Simulate a conversation flow across modes
        modes_and_messages = [
            ('database', 'I have tomatoes in my garden'),
            ('image_analysis', 'Is this the same type of tomato?'),
            ('database', 'How should I care for my tomatoes?'),
            ('image_analysis', 'What about this plant?'),
            ('database', 'Can you compare the care needs?')
        ]
        
        for mode, message in modes_and_messages:
            # Create transition context
            transition_context = self.conversation_manager.create_mode_transition_context(conversation_id, mode)
            
            # Add message
            self.conversation_manager.add_message(conversation_id, {
                'role': 'user',
                'content': message,
                'mode': mode
            })
            
            # Verify context is maintained
            cross_context = self.conversation_manager.get_cross_mode_context(conversation_id)
            self.assertIn('tomato', cross_context['recent_topics'])
        
        # Verify final state
        context = self.conversation_manager.get_conversation_context(conversation_id)
        self.assertEqual(len(context['messages']), len(modes_and_messages))
        self.assertEqual(context['metadata']['mode'], 'database')
        
        print("PASS: Conversation continuity across modes test passed")
    
    def test_error_handling_in_cross_mode_flow(self):
        """Test error handling in cross-mode conversation flow"""
        print("Testing error handling in cross-mode flow...")
        
        # Test with invalid conversation ID
        cross_context = self.conversation_manager.get_cross_mode_context('invalid_id')
        self.assertFalse(cross_context['available'])
        
        # Test with empty string conversation ID
        try:
            summary = self.conversation_manager.get_conversation_context_summary("")
            self.assertEqual(summary, "No conversation context available")
        except Exception as e:
            self.fail(f"Exception should be handled gracefully: {e}")
        
        # Test mode transition with invalid conversation
        transition_context = self.conversation_manager.create_mode_transition_context('invalid_id', 'database')
        # For invalid conversations, the context should still be created but with empty data
        self.assertIn('conversation_id', transition_context)
        self.assertEqual(transition_context['conversation_id'], 'invalid_id')
        
        print("PASS: Error handling in cross-mode flow test passed")
    
    def test_performance_of_cross_mode_features(self):
        """Test performance of cross-mode conversation features"""
        print("Testing performance of cross-mode features...")
        
        conversation_id = self.conversation_manager.generate_conversation_id()
        
        # Add multiple messages
        for i in range(20):
            self.conversation_manager.add_message(conversation_id, {
                'role': 'user',
                'content': f'Message {i} about gardening and plants',
                'mode': 'database'
            })
        
        # Test performance of cross-mode features
        start_time = time.time()
        
        # Test context summary generation
        summary = self.conversation_manager.get_conversation_context_summary(conversation_id)
        
        # Test cross-mode context extraction
        cross_context = self.conversation_manager.get_cross_mode_context(conversation_id)
        
        # Test mode transition context creation
        transition_context = self.conversation_manager.create_mode_transition_context(conversation_id, 'image_analysis')
        
        end_time = time.time()
        performance_time = end_time - start_time
        
        # Verify performance is reasonable (should complete in under 1 second)
        self.assertLess(performance_time, 1.0)
        
        # Verify features work correctly
        self.assertIn('plant', summary.lower())
        self.assertTrue(cross_context['available'])
        self.assertEqual(transition_context['new_mode'], 'image_analysis')
        
        print("PASS: Performance of cross-mode features test passed")


def run_phase4_cross_mode_tests():
    """Run all Phase 4 cross-mode conversation flow tests"""
    print("\n" + "="*80)
    print("PHASE 4 CROSS-MODE CONVERSATION FLOW TEST SUITE")
    print("="*80)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(Phase4CrossModeFlowTests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_phase4_cross_mode_tests()
    sys.exit(0 if success else 1) 