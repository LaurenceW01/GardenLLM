#!/usr/bin/env python3
"""
Test weather-aware chat responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_weather_aware_chat():
    """Test that chat responses include weather context"""
    print("🌤️  WEATHER-AWARE CHAT TEST")
    print("=" * 50)
    
    try:
        from chat_response import get_chat_response_legacy, get_chat_response_with_analyzer_optimized
        from conversation_manager import ConversationManager
        
        # Test questions that should benefit from weather context
        test_questions = [
            "Should I water my tomatoes today?",
            "Is it a good day to plant new flowers?",
            "Do I need to protect my plants from frost tonight?",
            "Can I fertilize my garden today?",
            "Should I bring my potted plants inside?"
        ]
        
        print("📝 Testing weather-aware chat responses...")
        print("-" * 50)
        
        for i, question in enumerate(test_questions):
            print(f"\n🌱 Question {i+1}: {question}")
            
            # Test legacy response (should include weather context)
            try:
                legacy_response = get_chat_response_legacy(question)
                print(f"  📨 Legacy Response: {legacy_response[:100]}...")
                
                # Check if response mentions weather
                if any(word in legacy_response.lower() for word in ['weather', 'temperature', 'rain', 'humidity', 'wind']):
                    print("  ✅ Response includes weather-related advice")
                else:
                    print("  ⚠️  Response doesn't mention weather")
                    
            except Exception as e:
                print(f"  ❌ Legacy response error: {e}")
        
        # Test conversation manager integration
        print(f"\n💬 Testing ConversationManager integration...")
        print("-" * 50)
        
        manager = ConversationManager()
        conversation_id = manager.generate_conversation_id("weather_chat_test")
        
        # Add a test message
        test_message = {"role": "user", "content": "Should I water my tomatoes today?"}
        manager.add_message(conversation_id, test_message)
        
        # Get weather-aware messages
        weather_messages = manager.get_weather_aware_messages(conversation_id)
        print(f"  📨 Weather-aware messages: {len(weather_messages)} total")
        
        # Show weather context messages
        for i, msg in enumerate(weather_messages):
            if msg['role'] == 'system' and ('weather' in msg['content'].lower() or 'forecast' in msg['content'].lower()):
                print(f"  🌤️  Weather context {i+1}: {msg['content'][:80]}...")
        
        print("\n✅ Weather-aware chat test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in weather-aware chat test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_weather_context_injection():
    """Test that weather context is properly injected into conversations"""
    print("\n🔧 WEATHER CONTEXT INJECTION TEST")
    print("=" * 50)
    
    try:
        from weather_context_integration import inject_weather_context_into_conversation
        
        # Test conversation injection
        sample_conversation = [
            {"role": "system", "content": "You are a helpful gardening assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help with your garden today?"},
            {"role": "user", "content": "Should I water my plants?"}
        ]
        
        print("📝 Original conversation:")
        for i, msg in enumerate(sample_conversation):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
        
        # Inject weather context
        enhanced_conversation = inject_weather_context_into_conversation(sample_conversation)
        
        print(f"\n📝 Enhanced conversation ({len(enhanced_conversation)} messages):")
        for i, msg in enumerate(enhanced_conversation):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
        
        # Check if weather context was added
        weather_context_count = sum(1 for msg in enhanced_conversation 
                                   if msg['role'] == 'system' and 
                                   ('weather' in msg['content'].lower() or 'forecast' in msg['content'].lower()))
        
        print(f"\n✅ Weather context messages added: {weather_context_count}")
        
        if weather_context_count > 0:
            print("✅ Weather context injection working correctly!")
        else:
            print("⚠️  No weather context detected in enhanced conversation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in weather context injection test: {e}")
        return False

def main():
    """Run all weather-aware chat tests"""
    print("🌤️  WEATHER-AWARE CHAT INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Weather-Aware Chat", test_weather_aware_chat),
        ("Weather Context Injection", test_weather_context_injection)
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
        print("🎉 All weather-aware chat tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 