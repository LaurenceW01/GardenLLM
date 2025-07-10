#!/usr/bin/env python3
"""
Test script for the centralized ConversationManager

This script tests all functionality of the ConversationManager to ensure
it works correctly after being moved to its own module.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import time

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation_manager import ConversationManager

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_conversation_creation():
    """Test basic conversation creation and message addition"""
    logger.info("Testing conversation creation...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Test adding a message to a new conversation
    test_message = {"role": "user", "content": "Hello, this is a test message"}
    manager.add_message(test_id, test_message)
    
    # Verify conversation was created
    messages = manager.get_messages(test_id)
    assert len(messages) == 1, f"Expected 1 message, got {len(messages)}"
    assert messages[0]["content"] == "Hello, this is a test message", "Message content doesn't match"
    
    logger.info("✅ Conversation creation test passed")
    return True

def test_multiple_messages():
    """Test adding multiple messages to a conversation"""
    logger.info("Testing multiple messages...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add multiple messages
    messages_to_add = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second message"},
        {"role": "assistant", "content": "Second response"}
    ]
    
    for message in messages_to_add:
        manager.add_message(test_id, message)
    
    # Verify all messages are present
    retrieved_messages = manager.get_messages(test_id)
    assert len(retrieved_messages) == 4, f"Expected 4 messages, got {len(retrieved_messages)}"
    
    # Verify message order and content
    for i, expected in enumerate(messages_to_add):
        assert retrieved_messages[i]["content"] == expected["content"], f"Message {i} content doesn't match"
        assert retrieved_messages[i]["role"] == expected["role"], f"Message {i} role doesn't match"
    
    logger.info("✅ Multiple messages test passed")
    return True

def test_conversation_timeout():
    """Test conversation timeout functionality"""
    logger.info("Testing conversation timeout...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add a message
    manager.add_message(test_id, {"role": "user", "content": "Test message"})
    
    # Verify conversation exists
    messages = manager.get_messages(test_id)
    assert len(messages) == 1, "Conversation should exist"
    
    # Manually set last_activity to simulate timeout
    manager.conversations[test_id]['last_activity'] = datetime.now() - timedelta(minutes=31)
    
    # Verify conversation is now inactive
    messages = manager.get_messages(test_id)
    assert len(messages) == 0, "Conversation should be cleared after timeout"
    
    logger.info("✅ Conversation timeout test passed")
    return True

def test_token_counting():
    """Test token counting functionality"""
    logger.info("Testing token counting...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add a message with known content
    test_message = {"role": "user", "content": "This is a test message for token counting"}
    manager.add_message(test_id, test_message)
    
    # Get total tokens
    total_tokens = manager._get_total_tokens(test_id)
    assert total_tokens > 0, "Token count should be greater than 0"
    
    # Add another message and verify token count increases
    second_message = {"role": "assistant", "content": "This is a response message"}
    manager.add_message(test_id, second_message)
    
    new_total_tokens = manager._get_total_tokens(test_id)
    assert new_total_tokens > total_tokens, "Token count should increase with new message"
    
    logger.info(f"✅ Token counting test passed. Tokens: {total_tokens} -> {new_total_tokens}")
    return True

def test_message_trimming():
    """Test message trimming when token limit is exceeded"""
    logger.info("Testing message trimming...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add system message first
    system_message = {"role": "system", "content": "You are a helpful assistant."}
    manager.add_message(test_id, system_message)
    
    # Add many long messages to trigger trimming
    long_content = "This is a very long message that contains many words and should contribute significantly to the token count. " * 50
    
    for i in range(10):
        message = {"role": "user", "content": f"Long message {i}: {long_content}"}
        manager.add_message(test_id, message)
    
    # Verify that messages were trimmed (should have fewer than 10 user messages)
    messages = manager.get_messages(test_id)
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    
    # Should have system message + some user messages (trimmed)
    assert len(messages) < 12, f"Messages should be trimmed, got {len(messages)}"
    assert len(user_messages) < 10, f"User messages should be trimmed, got {len(user_messages)}"
    
    logger.info(f"✅ Message trimming test passed. Final message count: {len(messages)}")
    return True

def test_clear_conversation():
    """Test clearing a conversation"""
    logger.info("Testing conversation clearing...")
    
    manager = ConversationManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add some messages
    manager.add_message(test_id, {"role": "user", "content": "Test message"})
    manager.add_message(test_id, {"role": "assistant", "content": "Test response"})
    
    # Verify messages exist
    messages = manager.get_messages(test_id)
    assert len(messages) == 2, "Should have 2 messages"
    
    # Clear the conversation
    manager.clear_conversation(test_id)
    
    # Verify conversation is cleared
    messages = manager.get_messages(test_id)
    assert len(messages) == 0, "Conversation should be empty after clearing"
    
    logger.info("✅ Conversation clearing test passed")
    return True

def test_multiple_conversations():
    """Test managing multiple conversations simultaneously"""
    logger.info("Testing multiple conversations...")
    
    manager = ConversationManager()
    
    # Create multiple conversations
    conversations = []
    for i in range(3):
        conv_id = f"test_conv_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        manager.add_message(conv_id, {"role": "user", "content": f"Message from conversation {i}"})
        conversations.append(conv_id)
    
    # Verify all conversations exist
    for conv_id in conversations:
        messages = manager.get_messages(conv_id)
        assert len(messages) == 1, f"Conversation {conv_id} should have 1 message"
    
    # Add more messages to one conversation
    manager.add_message(conversations[0], {"role": "assistant", "content": "Response in conversation 0"})
    
    # Verify only that conversation was affected
    messages_0 = manager.get_messages(conversations[0])
    messages_1 = manager.get_messages(conversations[1])
    
    assert len(messages_0) == 2, "First conversation should have 2 messages"
    assert len(messages_1) == 1, "Second conversation should still have 1 message"
    
    logger.info("✅ Multiple conversations test passed")
    return True

def test_plant_vision_integration():
    """Test that plant_vision.py can still use the conversation manager"""
    logger.info("Testing plant_vision integration...")
    
    try:
        # Import plant_vision to test the integration
        from plant_vision import conversation_manager
        
        # Test that it's the same type
        assert isinstance(conversation_manager, ConversationManager), "conversation_manager should be ConversationManager instance"
        
        # Test basic functionality
        test_id = f"plant_vision_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conversation_manager.add_message(test_id, {"role": "user", "content": "Plant vision test message"})
        
        messages = conversation_manager.get_messages(test_id)
        assert len(messages) == 1, "Plant vision integration should work"
        
        logger.info("✅ Plant vision integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Plant vision integration test failed: {e}")
        return False

def main():
    """Run all conversation manager tests"""
    logger.info("🧪 Starting ConversationManager Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Conversation Creation", test_conversation_creation),
        ("Multiple Messages", test_multiple_messages),
        ("Conversation Timeout", test_conversation_timeout),
        ("Token Counting", test_token_counting),
        ("Message Trimming", test_message_trimming),
        ("Clear Conversation", test_clear_conversation),
        ("Multiple Conversations", test_multiple_conversations),
        ("Plant Vision Integration", test_plant_vision_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All ConversationManager tests passed! Phase 1 is ready.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 