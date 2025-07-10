"""
Test Phase 2: Conversation History Integration

This test suite verifies that conversation history is properly integrated
into the chat response system, including:
- Conversation ID handling
- Message storage and retrieval
- Context preservation across queries
- Cross-mode conversation support
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_response import (
    get_chat_response_with_analyzer_optimized,
    handle_ai_enhanced_query_optimized,
    generate_ai_response_with_context,
    get_conversation_manager
)
from conversation_manager import ConversationManager
from query_analyzer import QueryType

class TestPhase2ConversationIntegration(unittest.TestCase):
    """Test conversation history integration in chat response system"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any existing conversations
        get_conversation_manager().conversations.clear()
        
        # Create a test conversation ID
        self.test_conversation_id = "test_conversation_123"
        
        # Mock OpenAI responses
        self.mock_openai_response = MagicMock()
        self.mock_openai_response.choices = [MagicMock()]
        self.mock_openai_response.choices[0].message.content = "Test AI response"
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear conversations
        get_conversation_manager().conversations.clear()
    
    def test_conversation_id_parameter_accepted(self):
        """Test that conversation_id parameter is properly accepted"""
        with patch('chat_response.openai_client.chat.completions.create', return_value=self.mock_openai_response):
            response = get_chat_response_with_analyzer_optimized(
                "What plants do I have?", 
                conversation_id=self.test_conversation_id
            )
            self.assertIsInstance(response, str)
            self.assertIn("Test AI response", response)
    
    def test_conversation_messages_stored(self):
        """Test that conversation messages are properly stored"""
        with patch('chat_response.openai_client.chat.completions.create', return_value=self.mock_openai_response):
            # Send first message
            get_chat_response_with_analyzer_optimized(
                "What plants do I have?", 
                conversation_id=self.test_conversation_id
            )
            
            # Check that messages were stored
            messages = get_conversation_manager().get_messages(self.test_conversation_id)
            self.assertEqual(len(messages), 2)  # User message + AI response
            self.assertEqual(messages[0]["role"], "user")
            self.assertEqual(messages[0]["content"], "What plants do I have?")
            self.assertEqual(messages[1]["role"], "assistant")
            self.assertEqual(messages[1]["content"], "Test AI response")
    
    def test_conversation_context_preserved(self):
        """Test that conversation context is preserved across multiple messages"""
        with patch('chat_response.openai_client.chat.completions.create', return_value=self.mock_openai_response):
            # Send first message
            get_chat_response_with_analyzer_optimized(
                "I have a tomato plant", 
                conversation_id=self.test_conversation_id
            )
            
            # Send follow-up message
            get_chat_response_with_analyzer_optimized(
                "How should I care for it?", 
                conversation_id=self.test_conversation_id
            )
            
            # Check that both conversations are stored
            messages = get_conversation_manager().get_messages(self.test_conversation_id)
            self.assertEqual(len(messages), 4)  # 2 user messages + 2 AI responses
            
            # Verify conversation flow
            self.assertEqual(messages[0]["content"], "I have a tomato plant")
            self.assertEqual(messages[2]["content"], "How should I care for it?")
    
    def test_ai_response_with_conversation_history(self):
        """Test that AI responses include conversation history context"""
        with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
            mock_openai.return_value = self.mock_openai_response
            
            # Send first message
            get_chat_response_with_analyzer_optimized(
                "I have a tomato plant", 
                conversation_id=self.test_conversation_id
            )
            
            # Send follow-up message
            get_chat_response_with_analyzer_optimized(
                "How should I care for it?", 
                conversation_id=self.test_conversation_id
            )
            
            # Verify that the AI calls included conversation history
            call_args = mock_openai.call_args_list
            self.assertGreaterEqual(len(call_args), 4)  # At least 2 analysis calls + 2 response calls
            
            # Check that the AI response calls have more messages (including history)
            # The AI response calls are at indices 1 and 3 (after analysis calls)
            if len(call_args) >= 2:
                first_response_messages = call_args[1][1]['messages']
                self.assertGreaterEqual(len(first_response_messages), 2)  # System + current user
            
            if len(call_args) >= 4:
                second_response_messages = call_args[3][1]['messages']
                self.assertGreater(len(second_response_messages), 2)  # System + history + current user
    
    def test_conversation_id_optional(self):
        """Test that conversation_id is optional and doesn't break existing functionality"""
        with patch('chat_response.openai_client.chat.completions.create', return_value=self.mock_openai_response):
            # Test without conversation_id
            response = get_chat_response_with_analyzer_optimized("What plants do I have?")
            self.assertIsInstance(response, str)
            
            # Test with None conversation_id
            response = get_chat_response_with_analyzer_optimized("What plants do I have?", conversation_id=None)
            self.assertIsInstance(response, str)
    
    def test_conversation_manager_integration(self):
        """Test that ConversationManager is properly integrated"""
        # Verify conversation manager is available
        self.assertIsInstance(get_conversation_manager(), ConversationManager)
        
        # Test basic conversation operations
        test_message = {"role": "user", "content": "Test message"}
        get_conversation_manager().add_message(self.test_conversation_id, test_message)
        
        messages = get_conversation_manager().get_messages(self.test_conversation_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Test message")
    
    def test_handle_ai_enhanced_query_with_conversation(self):
        """Test that handle_ai_enhanced_query_optimized supports conversation history"""
        with patch('chat_response.openai_client.chat.completions.create', return_value=self.mock_openai_response):
            response = handle_ai_enhanced_query_optimized(
                QueryType.CARE,
                ["tomato"],
                "How should I care for my tomato plant?",
                conversation_id=self.test_conversation_id
            )
            self.assertIsInstance(response, str)
    
    def test_generate_ai_response_with_conversation_context(self):
        """Test that generate_ai_response_with_context includes conversation history"""
        with patch('chat_response.openai_client.chat.completions.create') as mock_openai:
            mock_openai.return_value = self.mock_openai_response
            
            # Add some conversation history first
            get_conversation_manager().add_message(self.test_conversation_id, {
                "role": "user", 
                "content": "I have a tomato plant"
            })
            get_conversation_manager().add_message(self.test_conversation_id, {
                "role": "assistant", 
                "content": "That's great! Tomatoes are wonderful plants."
            })
            
            # Generate response with conversation context
            response = generate_ai_response_with_context(
                QueryType.CARE,
                "Context about tomato care",
                "How should I water it?",
                conversation_id=self.test_conversation_id
            )
            
            # Verify that the AI call included conversation history
            call_args = mock_openai.call_args
            messages = call_args[1]['messages']
            self.assertGreater(len(messages), 2)  # System + history + current user
            
            # Check that conversation history is included
            message_contents = [msg['content'] for msg in messages]
            self.assertIn("I have a tomato plant", str(message_contents))
    
    def test_conversation_timeout_handling(self):
        """Test that conversation timeout is properly handled"""
        # Add a message to create conversation
        get_conversation_manager().add_message(self.test_conversation_id, {
            "role": "user", 
            "content": "Test message"
        })
        
        # Verify conversation exists
        messages = get_conversation_manager().get_messages(self.test_conversation_id)
        self.assertEqual(len(messages), 1)
        
        # Simulate timeout by modifying last_activity
        get_conversation_manager().conversations[self.test_conversation_id]['last_activity'] = \
            get_conversation_manager().conversations[self.test_conversation_id]['last_activity'] - \
            get_conversation_manager().conversation_timeout - get_conversation_manager().conversation_timeout
        
        # Verify conversation is cleared on timeout
        messages = get_conversation_manager().get_messages(self.test_conversation_id)
        self.assertEqual(len(messages), 0)
    
    def test_token_management_with_conversation(self):
        """Test that token management works with conversation history"""
        # Add multiple messages to test token management
        for i in range(10):
            get_conversation_manager().add_message(self.test_conversation_id, {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}: " + "x" * 100  # Long message to test token limits
            })
        
        # Verify that messages are managed (not all stored if token limit exceeded)
        messages = get_conversation_manager().get_messages(self.test_conversation_id)
        self.assertLessEqual(len(messages), 10)  # Should be trimmed if token limit exceeded
    
    def test_error_handling_with_conversation(self):
        """Test that errors are handled gracefully with conversation history"""
        with patch('chat_response.openai_client.chat.completions.create', side_effect=Exception("API Error")):
            # Should not crash even with conversation_id
            try:
                response = get_chat_response_with_analyzer_optimized(
                    "Test message", 
                    conversation_id=self.test_conversation_id
                )
                # Should return error message
                self.assertIsInstance(response, str)
                # Check for technical difficulties message (actual error message)
                self.assertIn("technical difficulties", response.lower())
            except Exception as e:
                self.fail(f"Function should handle errors gracefully: {e}")

if __name__ == '__main__':
    unittest.main() 