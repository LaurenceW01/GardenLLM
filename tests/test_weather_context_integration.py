#!/usr/bin/env python3
"""
Test script for weather context integration functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_context_integration import (
    WeatherContextProvider, 
    get_weather_context_messages,
    inject_weather_context_into_conversation,
    create_weather_aware_conversation
)
from conversation_manager import ConversationManager
import json

def test_weather_context_provider():
    """Test the WeatherContextProvider class"""
    print("Testing WeatherContextProvider...")
    print("=" * 50)
    
    try:
        # Create provider instance
        provider = WeatherContextProvider()
        print(f"✅ Created WeatherContextProvider for {provider.location}")
        
        # Test getting weather context
        context_messages = provider.get_weather_context()
        print(f"✅ Got {len(context_messages)} weather context messages")
        
        # Display context messages
        for i, message in enumerate(context_messages):
            print(f"  Message {i+1}: {message['role']} - {message['content'][:100]}...")
        
        # Test cache functionality
        print("\nTesting cache functionality...")
        cached_messages = provider.get_weather_context()
        print(f"✅ Retrieved cached context: {len(cached_messages)} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing WeatherContextProvider: {e}")
        return False

def test_weather_context_functions():
    """Test the utility functions"""
    print("\nTesting weather context utility functions...")
    print("=" * 50)
    
    try:
        # Test get_weather_context_messages
        context_messages = get_weather_context_messages()
        print(f"✅ get_weather_context_messages: {len(context_messages)} messages")
        
        # Test inject_weather_context_into_conversation
        sample_conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        enhanced_conversation = inject_weather_context_into_conversation(sample_conversation)
        print(f"✅ inject_weather_context_into_conversation: {len(enhanced_conversation)} messages")
        
        # Test create_weather_aware_conversation
        weather_conversation = create_weather_aware_conversation("Should I water my plants today?")
        print(f"✅ create_weather_aware_conversation: {len(weather_conversation)} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing utility functions: {e}")
        return False

def test_conversation_manager_integration():
    """Test integration with ConversationManager"""
    print("\nTesting ConversationManager integration...")
    print("=" * 50)
    
    try:
        # Create conversation manager
        manager = ConversationManager()
        conversation_id = manager.generate_conversation_id("weather_test")
        print(f"✅ Created conversation: {conversation_id}")
        
        # Add a test message
        test_message = {"role": "user", "content": "Should I water my tomatoes today?"}
        manager.add_message(conversation_id, test_message)
        print(f"✅ Added test message to conversation")
        
        # Test regular messages
        regular_messages = manager.get_messages(conversation_id)
        print(f"✅ Regular messages: {len(regular_messages)} messages")
        
        # Test weather-aware messages
        weather_messages = manager.get_weather_aware_messages(conversation_id)
        print(f"✅ Weather-aware messages: {len(weather_messages)} messages")
        
        # Display weather context difference
        if len(weather_messages) > len(regular_messages):
            print(f"✅ Weather context added {len(weather_messages) - len(regular_messages)} context messages")
            for i, msg in enumerate(weather_messages[:len(weather_messages) - len(regular_messages)]):
                print(f"  Weather context {i+1}: {msg['content'][:80]}...")
        else:
            print("⚠️  No weather context added (may be unavailable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ConversationManager integration: {e}")
        return False

def test_weather_context_content():
    """Test the content of weather context messages"""
    print("\nTesting weather context content...")
    print("=" * 50)
    
    try:
        context_messages = get_weather_context_messages()
        
        if not context_messages:
            print("⚠️  No weather context messages available")
            return True
        
        print(f"✅ Analyzing {len(context_messages)} weather context messages:")
        
        for i, message in enumerate(context_messages):
            print(f"\nMessage {i+1}:")
            print(f"  Role: {message['role']}")
            print(f"  Content: {message['content']}")
            
            # Check content quality
            content = message['content']
            if 'weather' in content.lower():
                print("  ✅ Contains weather information")
            if 'houston' in content.lower():
                print("  ✅ Contains location information")
            if '°f' in content.lower() or 'fahrenheit' in content.lower():
                print("  ✅ Contains temperature information")
            if 'rain' in content.lower() or 'forecast' in content.lower():
                print("  ✅ Contains forecast information")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing weather context content: {e}")
        return False

def main():
    """Run all weather context integration tests"""
    print("Weather Context Integration Tests")
    print("=" * 60)
    
    tests = [
        ("WeatherContextProvider", test_weather_context_provider),
        ("Utility Functions", test_weather_context_functions),
        ("ConversationManager Integration", test_conversation_manager_integration),
        ("Weather Context Content", test_weather_context_content)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All weather context integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 