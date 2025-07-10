#!/usr/bin/env python3
"""
Test script for Phase 1 of the Plant Image Analysis Enhancement Plan

This script tests the enhanced plant identification and health assessment capabilities
implemented in Phase 1 of the enhancement plan.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_plant_vision_imports():
    """Test that all required functions can be imported"""
    try:
        from plant_vision import (
            analyze_plant_image,
            check_plant_in_database,
            extract_plant_names_from_analysis,
            enhance_analysis_with_database_check,
            ConversationManager,
            conversation_manager
        )
        logger.info("✅ All plant_vision functions imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_conversation_manager():
    """Test the conversation manager functionality"""
    try:
        from plant_vision import conversation_manager
        
        # Test conversation creation
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_message = {"role": "user", "content": "Test message"}
        
        conversation_manager.add_message(test_id, test_message)
        messages = conversation_manager.get_messages(test_id)
        
        if len(messages) == 1 and messages[0]["content"] == "Test message":
            logger.info("✅ Conversation manager working correctly")
            return True
        else:
            logger.error("❌ Conversation manager not working correctly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Conversation manager test failed: {e}")
        return False

def test_plant_name_extraction():
    """Test plant name extraction from analysis text"""
    try:
        from plant_vision import extract_plant_names_from_analysis
        
        # Test analysis text with plant names
        test_analysis = """
        This appears to be a Rose plant (Rosa sp.) in good condition.
        The common name is Rose and it shows signs of healthy growth.
        This specimen is a beautiful flowering plant.
        """
        
        plant_names = extract_plant_names_from_analysis(test_analysis)
        
        if "Rose" in plant_names:
            logger.info(f"✅ Plant name extraction working: {plant_names}")
            return True
        else:
            logger.error(f"❌ Plant name extraction failed: {plant_names}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Plant name extraction test failed: {e}")
        return False

def test_database_integration():
    """Test database integration functions"""
    try:
        from plant_vision import check_plant_in_database
        
        # Test with a sample plant name
        result = check_plant_in_database("Test Plant")
        
        if isinstance(result, dict) and "exists" in result and "message" in result:
            logger.info("✅ Database integration functions working")
            logger.info(f"   Sample result: {result}")
            return True
        else:
            logger.error(f"❌ Database integration test failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database integration test failed: {e}")
        return False

def test_analysis_enhancement():
    """Test analysis enhancement with database integration"""
    try:
        from plant_vision import enhance_analysis_with_database_check
        
        # Test with sample analysis
        test_analysis = """
        ## Plant Identification
        This is a Rose plant (Rosa sp.)
        
        ## Health Assessment
        The plant appears healthy with good growth.
        """
        
        enhanced = enhance_analysis_with_database_check(test_analysis)
        
        if "Garden Database Integration" in enhanced:
            logger.info("✅ Analysis enhancement working")
            return True
        else:
            logger.error("❌ Analysis enhancement failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Analysis enhancement test failed: {e}")
        return False

def test_web_integration():
    """Test that web.py can import the enhanced functions"""
    try:
        # Test that web.py can import the required functions
        import importlib.util
        
        # Check if web.py exists and can import plant_vision
        spec = importlib.util.spec_from_file_location("web", "web.py")
        if spec and spec.loader:
            web_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(web_module)
            logger.info("✅ Web integration test passed")
            return True
        else:
            logger.error("❌ Web.py not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Web integration test failed: {e}")
        return False

def main():
    """Run all Phase 1 tests"""
    logger.info("🧪 Starting Phase 1 Plant Image Analysis Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Plant Vision Imports", test_plant_vision_imports),
        ("Conversation Manager", test_conversation_manager),
        ("Plant Name Extraction", test_plant_name_extraction),
        ("Database Integration", test_database_integration),
        ("Analysis Enhancement", test_analysis_enhancement),
        ("Web Integration", test_web_integration),
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
        logger.info("🎉 All Phase 1 tests passed! Plant Image Analysis Enhancement is ready.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 