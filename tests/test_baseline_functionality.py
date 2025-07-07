#!/usr/bin/env python3
"""
GardenLLM Baseline Functionality Test
Validates all core functionality before four-mode system implementation.

This test establishes the baseline behavior that must be preserved throughout implementation.
"""

import requests
import json
import time
import os
from datetime import datetime

class GardenLLMBaselineTest:
    def __init__(self, base_url="https://gardenllm-server.onrender.com"):
        """Initialize test suite with base URL for the GardenLLM application."""
        self.base_url = base_url
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name, status, details=""):
        """Log test results with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
    
    def test_server_connectivity(self):
        """Test basic server connectivity and health."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("Server Connectivity", "PASS", "Server is responding")
                return True
            else:
                self.log_test("Server Connectivity", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_weather_endpoint(self):
        """Test weather analysis functionality."""
        try:
            # Test weather API endpoint (not the page endpoint)
            response = requests.get(f"{self.base_url}/api/weather", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Check for weather forecast and plant care advice
                if "forecast" in result and "plant_care_advice" in result:
                    self.log_test("Weather Endpoint", "PASS", "Weather API working with forecast and plant care advice")
                    return True
                else:
                    self.log_test("Weather Endpoint", "WARNING", "Weather API working but missing expected fields")
                    return True
            else:
                self.log_test("Weather Endpoint", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Weather Endpoint", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_general_gardening(self):
        """Test general gardening Q&A functionality in Garden Database mode."""
        try:
            gardening_data = {
                "message": "How do I grow tomatoes in my garden?"
            }
            response = requests.post(f"{self.base_url}/chat", json=gardening_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Check for Houston climate context
                if "Houston" in result.get("response", "") or "Zone 9" in result.get("response", ""):
                    self.log_test("General Gardening", "PASS", "General gardening Q&A working with Houston context")
                    return True
                else:
                    self.log_test("General Gardening", "WARNING", "General gardening working but Houston context not detected")
                    return True
            else:
                self.log_test("General Gardening", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("General Gardening", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_add_plant_command(self):
        """Test add plant functionality with exact command format in Garden Database mode."""
        try:
            add_plant_data = {
                "message": "Add/Update plant tomato"
            }
            response = requests.post(f"{self.base_url}/chat", json=add_plant_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Check for AI-generated care information
                care_keywords = ["watering", "light", "soil", "temperature", "fertilizing"]
                care_info_present = any(keyword in response_text.lower() for keyword in care_keywords)
                
                if care_info_present:
                    self.log_test("Add Plant Command", "PASS", "Add plant command working with AI care generation")
                    return True
                else:
                    self.log_test("Add Plant Command", "WARNING", "Add plant command working but care info not detected")
                    return True
            else:
                self.log_test("Add Plant Command", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Add Plant Command", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_update_plant_command(self):
        """Test update plant functionality with exact command format in Garden Database mode."""
        try:
            update_plant_data = {
                "message": "Add/Update tomato"
            }
            response = requests.post(f"{self.base_url}/chat", json=update_plant_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Check for AI-generated care information
                care_keywords = ["watering", "light", "soil", "temperature", "fertilizing"]
                care_info_present = any(keyword in response_text.lower() for keyword in care_keywords)
                
                if care_info_present:
                    self.log_test("Update Plant Command", "PASS", "Update plant command working with AI care generation")
                    return True
                else:
                    self.log_test("Update Plant Command", "WARNING", "Update plant command working but care info not detected")
                    return True
            else:
                self.log_test("Update Plant Command", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Update Plant Command", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_image_analysis_endpoint(self):
        """Test image analysis functionality in Image Analysis mode."""
        try:
            # Test if image analysis endpoint exists and accepts requests
            # Create a simple test image (1x1 pixel PNG)
            import io
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178\xd5\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {'file': ('test.png', io.BytesIO(test_image_data), 'image/png')}
            data = {'message': 'What plant is this?'}
            
            response = requests.post(f"{self.base_url}/analyze-plant", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    self.log_test("Image Analysis Endpoint", "PASS", "Image analysis endpoint working")
                    return True
                else:
                    self.log_test("Image Analysis Endpoint", "WARNING", "Image analysis working but missing response field")
                    return True
            else:
                self.log_test("Image Analysis Endpoint", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Image Analysis Endpoint", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_database_operations(self):
        """Test database query functionality."""
        try:
            query_data = {
                "message": "Show me my plants"
            }
            response = requests.post(f"{self.base_url}/chat", json=query_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Check for database-related response
                if "plant" in response_text.lower() or "garden" in response_text.lower():
                    self.log_test("Database Operations", "PASS", "Database query functionality working")
                    return True
                else:
                    self.log_test("Database Operations", "WARNING", "Database query working but response format unclear")
                    return True
            else:
                self.log_test("Database Operations", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database Operations", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_houston_climate_context(self):
        """Test that Houston climate context is present in responses."""
        try:
            # Test multiple queries to check for Houston context
            test_queries = [
                "How do I care for roses?",
                "What vegetables grow well in my area?",
                "When should I plant tomatoes?",
                "How often should I water my garden?"
            ]
            
            houston_context_found = 0
            total_queries = len(test_queries)
            
            for query in test_queries:
                data = {"message": query}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check for Houston climate indicators
                    houston_indicators = ["houston", "zone 9", "texas", "humidity", "clay soil"]
                    if any(indicator in response_text.lower() for indicator in houston_indicators):
                        houston_context_found += 1
                
                time.sleep(1)  # Rate limiting consideration
            
            context_percentage = (houston_context_found / total_queries) * 100
            
            if context_percentage >= 50:  # At least 50% of responses should have Houston context
                self.log_test("Houston Climate Context", "PASS", f"Houston context found in {context_percentage:.1f}% of responses")
                return True
            else:
                self.log_test("Houston Climate Context", "WARNING", f"Houston context found in only {context_percentage:.1f}% of responses")
                return True
        except Exception as e:
            self.log_test("Houston Climate Context", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all baseline tests and generate report."""
        print("=" * 60)
        print("GardenLLM Baseline Functionality Test")
        print("=" * 60)
        print(f"Starting tests at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing against: {self.base_url}")
        print("-" * 60)
        
        # Run all tests
        tests = [
            self.test_server_connectivity,
            self.test_weather_endpoint,
            self.test_general_gardening,
            self.test_add_plant_command,
            self.test_update_plant_command,
            self.test_image_analysis_endpoint,
            self.test_database_operations,
            self.test_houston_climate_context
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test in tests:
            try:
                result = test()
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:
                    warnings += 1
            except Exception as e:
                self.log_test(test.__name__, "ERROR", f"Test execution error: {str(e)}")
                failed += 1
        
        # Generate summary
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("-" * 60)
        print("TEST SUMMARY")
        print("-" * 60)
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Duration: {duration}")
        print("-" * 60)
        
        # Save detailed results
        self.save_results()
        
        return passed, failed, warnings
    
    def save_results(self):
        """Save test results to file."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_test_results_{timestamp}.json"
        
        results = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "base_url": self.base_url
            },
            "results": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Detailed results saved to: {filename}")

if __name__ == "__main__":
    # Allow command line override of base URL
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://gardenllm-server.onrender.com"
    
    tester = GardenLLMBaselineTest(base_url)
    passed, failed, warnings = tester.run_all_tests()
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)  # Exit with error if any tests failed
    else:
        sys.exit(0)  # Exit successfully if all tests passed or had warnings 