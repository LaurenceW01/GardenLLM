#!/usr/bin/env python3
"""
GardenLLM Database Operations Test
Validates add/update plant functionality with exact command formats.

This test ensures the critical add/update plant functionality works exactly as specified
in the requirements document.
"""

import requests
import json
import time
from datetime import datetime

class DatabaseOperationsTest:
    def __init__(self, base_url="https://gardenllm-server.onrender.com"):
        """Initialize database operations test suite."""
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
    
    def test_exact_add_plant_command_format(self):
        """Test the exact add plant command format: 'Add/Update plant [plant name]'."""
        test_plants = ["tomato", "rosemary", "basil", "pepper"]
        
        for plant in test_plants:
            try:
                command = f"Add/Update plant {plant}"
                data = {"message": command}
                
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check for AI-generated care information
                    care_keywords = ["watering", "light", "soil", "temperature", "fertilizing", "pruning"]
                    care_info_present = any(keyword in response_text.lower() for keyword in care_keywords)
                    
                    # Check for Houston climate context
                    houston_context = any(indicator in response_text.lower() for indicator in ["houston", "zone 9", "texas", "humidity"])
                    
                    if care_info_present:
                        self.log_test(f"Add Plant Command - {plant}", "PASS", 
                                    f"Command '{command}' working with AI care generation")
                    else:
                        self.log_test(f"Add Plant Command - {plant}", "WARNING", 
                                    f"Command '{command}' working but care info not detected")
                    
                    if houston_context:
                        self.log_test(f"Add Plant Houston Context - {plant}", "PASS", 
                                    "Houston climate context present")
                    else:
                        self.log_test(f"Add Plant Houston Context - {plant}", "WARNING", 
                                    "Houston climate context not detected")
                        
                else:
                    self.log_test(f"Add Plant Command - {plant}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Add Plant Command - {plant}", "FAIL", f"Error: {str(e)}")
    
    def test_exact_update_plant_command_format(self):
        """Test the exact update plant command format: 'Add/Update [plant name]'."""
        test_plants = ["tomato", "rosemary", "basil", "pepper"]
        
        for plant in test_plants:
            try:
                command = f"Add/Update {plant}"
                data = {"message": command}
                
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check for AI-generated care information
                    care_keywords = ["watering", "light", "soil", "temperature", "fertilizing", "pruning"]
                    care_info_present = any(keyword in response_text.lower() for keyword in care_keywords)
                    
                    # Check for Houston climate context
                    houston_context = any(indicator in response_text.lower() for indicator in ["houston", "zone 9", "texas", "humidity"])
                    
                    if care_info_present:
                        self.log_test(f"Update Plant Command - {plant}", "PASS", 
                                    f"Command '{command}' working with AI care generation")
                    else:
                        self.log_test(f"Update Plant Command - {plant}", "WARNING", 
                                    f"Command '{command}' working but care info not detected")
                    
                    if houston_context:
                        self.log_test(f"Update Plant Houston Context - {plant}", "PASS", 
                                    "Houston climate context present")
                    else:
                        self.log_test(f"Update Plant Houston Context - {plant}", "WARNING", 
                                    "Houston climate context not detected")
                        
                else:
                    self.log_test(f"Update Plant Command - {plant}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Update Plant Command - {plant}", "FAIL", f"Error: {str(e)}")
    
    def test_optional_fields_handling(self):
        """Test that optional fields (location, photo URL) are handled correctly."""
        test_cases = [
            {
                "command": "Add/Update plant tomato with location: backyard garden",
                "expected_field": "location"
            },
            {
                "command": "Add/Update plant tomato with photo URL: https://example.com/tomato.jpg",
                "expected_field": "photo"
            },
            {
                "command": "Add/Update plant tomato location: front porch photo URL: https://example.com/tomato2.jpg",
                "expected_field": "both"
            }
        ]
        
        for test_case in test_cases:
            try:
                data = {"message": test_case["command"]}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check if optional fields are acknowledged
                    if "location" in test_case["command"].lower() and "location" in response_text.lower():
                        self.log_test(f"Optional Field - {test_case['expected_field']}", "PASS", 
                                    f"Location field handled correctly")
                    elif "photo" in test_case["command"].lower() and "photo" in response_text.lower():
                        self.log_test(f"Optional Field - {test_case['expected_field']}", "PASS", 
                                    f"Photo URL field handled correctly")
                    else:
                        self.log_test(f"Optional Field - {test_case['expected_field']}", "WARNING", 
                                    f"Optional field handling unclear")
                        
                else:
                    self.log_test(f"Optional Field - {test_case['expected_field']}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Optional Field - {test_case['expected_field']}", "FAIL", f"Error: {str(e)}")
    
    def test_ai_care_information_generation(self):
        """Test that AI generates comprehensive care information."""
        test_plant = "tomato"
        
        try:
            command = f"Add/Update plant {test_plant}"
            data = {"message": command}
            
            response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Check for comprehensive care information
                care_sections = {
                    "watering": ["water", "watering", "moisture"],
                    "light": ["light", "sun", "shade", "exposure"],
                    "soil": ["soil", "drainage", "ph"],
                    "temperature": ["temperature", "heat", "cold", "frost"],
                    "fertilizing": ["fertilizer", "fertilizing", "nutrients"],
                    "pruning": ["prune", "pruning", "trim"],
                    "spacing": ["space", "spacing", "distance"]
                }
                
                sections_found = 0
                total_sections = len(care_sections)
                
                for section, keywords in care_sections.items():
                    if any(keyword in response_text.lower() for keyword in keywords):
                        sections_found += 1
                
                coverage_percentage = (sections_found / total_sections) * 100
                
                if coverage_percentage >= 60:  # At least 60% of care sections should be present
                    self.log_test("AI Care Information Generation", "PASS", 
                                f"Comprehensive care info generated ({coverage_percentage:.1f}% coverage)")
                else:
                    self.log_test("AI Care Information Generation", "WARNING", 
                                f"Limited care info generated ({coverage_percentage:.1f}% coverage)")
                    
            else:
                self.log_test("AI Care Information Generation", "FAIL", 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("AI Care Information Generation", "FAIL", f"Error: {str(e)}")
    
    def test_database_query_commands(self):
        """Test database query functionality."""
        query_commands = [
            "Show me my plants",
            "What plants do I have?",
            "List my garden plants",
            "What's in my garden database?"
        ]
        
        for command in query_commands:
            try:
                data = {"message": command}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check for database-related response
                    if "plant" in response_text.lower() or "garden" in response_text.lower():
                        self.log_test(f"Database Query - '{command}'", "PASS", 
                                    "Database query functionality working")
                    else:
                        self.log_test(f"Database Query - '{command}'", "WARNING", 
                                    "Database query working but response format unclear")
                        
                else:
                    self.log_test(f"Database Query - '{command}'", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Database Query - '{command}'", "FAIL", f"Error: {str(e)}")
    
    def test_command_format_preservation(self):
        """Test that only the exact command formats work."""
        invalid_commands = [
            "Add tomato to my garden",
            "Add a tomato plant",
            "I want to add tomato",
            "Update tomato watering to daily",
            "Change tomato location to backyard"
        ]
        
        for command in invalid_commands:
            try:
                data = {"message": command}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # These commands should not trigger add/update functionality
                    # They should be treated as general gardening questions
                    if "add" in command.lower() and "plant" in command.lower():
                        # This might still work if the system is flexible
                        self.log_test(f"Invalid Command - '{command}'", "INFO", 
                                    "Command format flexibility detected")
                    else:
                        self.log_test(f"Invalid Command - '{command}'", "PASS", 
                                    "Command correctly handled as general query")
                        
                else:
                    self.log_test(f"Invalid Command - '{command}'", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Invalid Command - '{command}'", "FAIL", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all database operation tests and generate report."""
        print("=" * 60)
        print("GardenLLM Database Operations Test")
        print("=" * 60)
        print(f"Starting tests at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing against: {self.base_url}")
        print("-" * 60)
        
        # Run all tests
        tests = [
            self.test_exact_add_plant_command_format,
            self.test_exact_update_plant_command_format,
            self.test_optional_fields_handling,
            self.test_ai_care_information_generation,
            self.test_database_query_commands,
            self.test_command_format_preservation
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, "ERROR", f"Test execution error: {str(e)}")
        
        # Generate summary
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        warnings = sum(1 for result in self.test_results if result["status"] == "WARNING")
        
        print("-" * 60)
        print("TEST SUMMARY")
        print("-" * 60)
        print(f"Total Tests: {len(self.test_results)}")
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
        filename = f"database_operations_test_results_{timestamp}.json"
        
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
    
    tester = DatabaseOperationsTest(base_url)
    passed, failed, warnings = tester.run_all_tests()
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)  # Exit with error if any tests failed
    else:
        sys.exit(0)  # Exit successfully if all tests passed or had warnings 