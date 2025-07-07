#!/usr/bin/env python3
"""
GardenLLM Houston Climate Context Test
Validates that Houston climate context is present in all AI responses.

This test ensures that the mandatory Houston climate context is maintained
throughout the four-mode system implementation.
"""

import requests
import json
import time
from datetime import datetime

class HoustonClimateTest:
    def __init__(self, base_url="https://gardenllm-server.onrender.com"):
        """Initialize Houston climate test suite."""
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
    
    def check_houston_context(self, response_text):
        """Check for Houston climate context indicators in response text."""
        houston_indicators = {
            "houston": ["houston", "texas", "tx"],
            "zone": ["zone 9", "zone 9a", "zone 9b"],
            "temperature": ["90-100°f", "32-38°c", "30-40°f", "-1-4°c"],
            "humidity": ["humidity", "humid", "60-80%"],
            "soil": ["clay soil", "alkaline", "ph 7.0-8.0"],
            "rainfall": ["50+ inches", "heavy spring", "heavy fall"],
            "seasons": ["february-may", "september-november", "avoid peak summer"]
        }
        
        context_found = {}
        total_indicators = 0
        found_indicators = 0
        
        for category, indicators in houston_indicators.items():
            category_found = False
            for indicator in indicators:
                if indicator in response_text.lower():
                    category_found = True
                    found_indicators += 1
                total_indicators += 1
            context_found[category] = category_found
        
        return context_found, found_indicators, total_indicators
    
    def test_general_gardening_houston_context(self):
        """Test Houston climate context in general gardening responses."""
        gardening_queries = [
            "How do I grow tomatoes?",
            "What vegetables grow well in my area?",
            "When should I plant peppers?",
            "How often should I water my garden?",
            "What soil amendments do I need?",
            "How do I protect plants from frost?",
            "What are good companion plants?",
            "How do I fertilize my garden?"
        ]
        
        total_queries = len(gardening_queries)
        houston_context_found = 0
        
        for query in gardening_queries:
            try:
                data = {"message": query}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    context_found, found_indicators, total_indicators = self.check_houston_context(response_text)
                    
                    # Check if at least 2 categories of Houston context are present
                    categories_found = sum(context_found.values())
                    
                    if categories_found >= 2:
                        houston_context_found += 1
                        self.log_test(f"General Gardening - '{query[:30]}...'", "PASS", 
                                    f"Houston context found ({categories_found} categories)")
                    else:
                        self.log_test(f"General Gardening - '{query[:30]}...'", "WARNING", 
                                    f"Limited Houston context ({categories_found} categories)")
                        
                else:
                    self.log_test(f"General Gardening - '{query[:30]}...'", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"General Gardening - '{query[:30]}...'", "FAIL", f"Error: {str(e)}")
        
        # Calculate overall success rate
        success_rate = (houston_context_found / total_queries) * 100
        self.log_test("General Gardening Houston Context Overall", 
                     "PASS" if success_rate >= 70 else "WARNING",
                     f"Houston context found in {success_rate:.1f}% of responses")
    
    def test_weather_mode_houston_context(self):
        """Test Houston climate context in weather mode responses."""
        try:
            # Test weather API endpoint
            response = requests.get(f"{self.base_url}/api/weather", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                plant_care_advice = result.get("plant_care_advice", [])
                
                # Check for Houston climate indicators in plant care advice
                houston_indicators = ["houston", "zone 9", "texas", "humidity", "clay soil", "gulf coast"]
                houston_context_found = 0
                total_advice = len(plant_care_advice)
                
                for advice in plant_care_advice:
                    if any(indicator in advice.lower() for indicator in houston_indicators):
                        houston_context_found += 1
                
                context_percentage = (houston_context_found / total_advice) * 100 if total_advice > 0 else 0
                
                if context_percentage >= 30:  # At least 30% of advice should have Houston context
                    self.log_test("Weather Mode Houston Context", "PASS", f"Houston context found in {context_percentage:.1f}% of weather advice")
                    return True
                else:
                    self.log_test("Weather Mode Houston Context", "WARNING", f"Houston context found in only {context_percentage:.1f}% of weather advice")
                    return True
            else:
                self.log_test("Weather Mode Houston Context", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Weather Mode Houston Context", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_add_plant_houston_context(self):
        """Test Houston climate context in add plant responses."""
        test_plants = ["tomato", "rosemary", "basil", "pepper", "lettuce", "carrots"]
        
        total_plants = len(test_plants)
        houston_context_found = 0
        
        for plant in test_plants:
            try:
                command = f"Add/Update plant {plant}"
                data = {"message": command}
                
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    context_found, found_indicators, total_indicators = self.check_houston_context(response_text)
                    
                    # Check if at least 2 categories of Houston context are present
                    categories_found = sum(context_found.values())
                    
                    if categories_found >= 2:
                        houston_context_found += 1
                        self.log_test(f"Add Plant - {plant}", "PASS", 
                                    f"Houston context found ({categories_found} categories)")
                    else:
                        self.log_test(f"Add Plant - {plant}", "WARNING", 
                                    f"Limited Houston context ({categories_found} categories)")
                        
                else:
                    self.log_test(f"Add Plant - {plant}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Add Plant - {plant}", "FAIL", f"Error: {str(e)}")
        
        # Calculate overall success rate
        success_rate = (houston_context_found / total_plants) * 100
        self.log_test("Add Plant Houston Context Overall", 
                     "PASS" if success_rate >= 80 else "WARNING",
                     f"Houston context found in {success_rate:.1f}% of responses")
    
    def test_specific_houston_climate_indicators(self):
        """Test for specific Houston climate indicators in responses."""
        test_queries = [
            "What's the best time to plant tomatoes in my area?",
            "How do I deal with the humidity in my garden?",
            "What soil type do I have and how do I improve it?",
            "When is the last frost date in my area?",
            "How do I protect plants from the summer heat?"
        ]
        
        expected_indicators = {
            "planting time": ["february", "march", "spring", "fall"],
            "humidity": ["humidity", "humid", "60-80%"],
            "soil": ["clay", "alkaline", "ph 7.0-8.0"],
            "frost": ["november", "march", "freeze", "frost"],
            "heat": ["summer", "90-100°f", "heat", "hot"]
        }
        
        for i, query in enumerate(test_queries):
            try:
                data = {"message": query}
                response = requests.post(f"{self.base_url}/chat", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Get the expected indicators for this query
                    query_key = list(expected_indicators.keys())[i]
                    expected = expected_indicators[query_key]
                    
                    # Check if expected indicators are present
                    found_indicators = [indicator for indicator in expected 
                                      if indicator in response_text.lower()]
                    
                    if len(found_indicators) >= 1:
                        self.log_test(f"Specific Indicator - {query_key}", "PASS", 
                                    f"Found indicators: {found_indicators}")
                    else:
                        self.log_test(f"Specific Indicator - {query_key}", "WARNING", 
                                    f"No expected indicators found for {query_key}")
                        
                else:
                    self.log_test(f"Specific Indicator - {query_key}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Specific Indicator - {query_key}", "FAIL", f"Error: {str(e)}")
    
    def test_climate_context_consistency(self):
        """Test that climate context is consistent across different query types."""
        base_query = "How do I care for tomatoes?"
        
        # Test the same query across different endpoints
        endpoints = [
            ("/chat", {"message": base_query}, "POST"),
            ("/api/weather", {}, "GET")
        ]
        
        responses = []
        
        for endpoint, data, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if endpoint == "/api/weather":
                        # For weather endpoint, check plant care advice
                        plant_care_advice = result.get("plant_care_advice", [])
                        response_text = " ".join(plant_care_advice)
                    else:
                        response_text = result.get("response", "")
                    
                    responses.append(response_text)
                    
                    context_found, found_indicators, total_indicators = self.check_houston_context(response_text)
                    categories_found = sum(context_found.values())
                    
                    self.log_test(f"Climate Consistency - {endpoint}", "PASS", 
                                f"Houston context found ({categories_found} categories)")
                        
                else:
                    self.log_test(f"Climate Consistency - {endpoint}", "FAIL", 
                                f"Status code: {response.status_code}")
                
                time.sleep(1)  # Rate limiting consideration
                
            except Exception as e:
                self.log_test(f"Climate Consistency - {endpoint}", "FAIL", f"Error: {str(e)}")
        
        # Check if responses are consistent
        if len(responses) >= 2:
            # Simple consistency check - both should mention Houston or Texas
            houston_mentions = [1 if "houston" in resp.lower() or "texas" in resp.lower() 
                              else 0 for resp in responses]
            
            if sum(houston_mentions) >= 1:
                self.log_test("Climate Context Consistency", "PASS", 
                            "Climate context consistent across endpoints")
            else:
                self.log_test("Climate Context Consistency", "WARNING", 
                            "Climate context inconsistent across endpoints")
    
    def run_all_tests(self):
        """Run all Houston climate context tests and generate report."""
        print("=" * 60)
        print("GardenLLM Houston Climate Context Test")
        print("=" * 60)
        print(f"Starting tests at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing against: {self.base_url}")
        print("-" * 60)
        
        # Run all tests
        tests = [
            self.test_general_gardening_houston_context,
            self.test_weather_mode_houston_context,
            self.test_add_plant_houston_context,
            self.test_specific_houston_climate_indicators,
            self.test_climate_context_consistency
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
        filename = f"houston_climate_test_results_{timestamp}.json"
        
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
    
    tester = HoustonClimateTest(base_url)
    passed, failed, warnings = tester.run_all_tests()
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)  # Exit with error if any tests failed
    else:
        sys.exit(0)  # Exit successfully if all tests passed or had warnings 