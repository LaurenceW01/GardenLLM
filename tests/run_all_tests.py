#!/usr/bin/env python3
"""
GardenLLM Comprehensive Test Runner
Executes all test scripts and generates a combined report.

This script runs all baseline tests to establish current functionality
before four-mode system implementation.
"""

import subprocess
import sys
import os
import json
from datetime import datetime
import time

class TestRunner:
    def __init__(self, base_url="https://gardenllm-server.onrender.com"):
        """Initialize test runner."""
        self.base_url = base_url
        self.test_results = {}
        self.start_time = datetime.now()
        self.test_scripts = [
            "test_baseline_functionality.py",
            "test_database_operations.py", 
            "test_houston_climate.py"
        ]
        # Create tests-results directory
        self.results_dir = "tests-results"
        self.ensure_results_directory()
        
    def ensure_results_directory(self):
        """Create the tests-results directory if it doesn't exist."""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"Created results directory: {self.results_dir}")
    
    def parse_failure_details(self, stdout):
        """Parse detailed failure information from test output."""
        failure_details = []
        lines = stdout.split('\n')
        
        for i, line in enumerate(lines):
            if 'FAIL' in line and 'Details:' in line:
                # Extract test name and failure details
                parts = line.split(':')
                if len(parts) >= 3:
                    test_name = parts[0].split(']')[-1].strip()
                    details = ':'.join(parts[2:]).strip()
                    failure_details.append({
                        "test": test_name,
                        "details": details
                    })
            elif 'FAIL' in line and i + 1 < len(lines) and 'Details:' in lines[i + 1]:
                # Handle case where FAIL and Details are on separate lines
                test_part = line.split(']')[-1].strip()
                test_name = test_part.split(':')[0].strip()
                details = lines[i + 1].split('Details:')[-1].strip()
                failure_details.append({
                    "test": test_name,
                    "details": details
                })
        
        return failure_details
    
    def run_test_script(self, script_name):
        """Run a single test script and capture results."""
        print(f"\n{'='*60}")
        print(f"Running: {script_name}")
        print(f"{'='*60}")
        
        try:
            # Run the test script with the base URL
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            result = subprocess.run([
                sys.executable, script_path, self.base_url
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            # Parse the output to extract test results
            output_lines = result.stdout.split('\n')
            
            # Look for test summary in output
            summary_found = False
            passed = 0
            failed = 0
            warnings = 0
            for line in output_lines:
                if "TEST SUMMARY" in line:
                    summary_found = True
                    continue
                if summary_found:
                    # End of summary block: line is exactly 60 dashes AND we've found all summary values
                    if line.strip() == "-" * 60 and passed > 0 and failed >= 0 and warnings >= 0:
                        break
                    if "Passed:" in line:
                        try:
                            passed = int(line.split(":")[1].strip())
                        except:
                            pass
                    elif "Failed:" in line:
                        try:
                            failed = int(line.split(":")[1].strip())
                        except:
                            pass
                    elif "Warnings:" in line:
                        try:
                            warnings = int(line.split(":")[1].strip())
                        except:
                            pass
            
            # Store results
            failure_details = self.parse_failure_details(result.stdout)
            self.test_results[script_name] = {
                "return_code": result.returncode,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "failure_details": failure_details
            }
            
            # Print summary
            status = "PASS" if result.returncode == 0 else "FAIL"
            print(f"Result: {status}")
            print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")
            
            if result.stderr:
                print(f"Errors: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"ERROR: {script_name} timed out after 5 minutes")
            self.test_results[script_name] = {
                "return_code": -1,
                "passed": 0,
                "failed": 1,
                "warnings": 0,
                "stdout": "",
                "stderr": "Test timed out",
                "success": False,
                "failure_details": [{"test": script_name, "details": "Test timed out after 5 minutes"}]
            }
            return False
        except Exception as e:
            print(f"ERROR: Failed to run {script_name}: {str(e)}")
            self.test_results[script_name] = {
                "return_code": -1,
                "passed": 0,
                "failed": 1,
                "warnings": 0,
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "failure_details": [{"test": script_name, "details": f"Execution error: {str(e)}"}]
            }
            return False
    
    def check_server_status(self):
        """Check if the GardenLLM server is running."""
        print("Checking server status...")
        try:
            import requests
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                print("✓ Server is running and responding")
                return True
            else:
                print(f"✗ Server returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Cannot connect to server: {str(e)}")
            print(f"  Make sure the GardenLLM server is running at {self.base_url}")
            return False
    
    def run_all_tests(self):
        """Run all test scripts and generate comprehensive report."""
        print("=" * 80)
        print("GardenLLM Comprehensive Test Suite")
        print("=" * 80)
        print(f"Starting comprehensive test run at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        # Check server status first
        if not self.check_server_status():
            print("\nERROR: Server is not available. Please start the GardenLLM server first.")
            return False
        
        # Run all test scripts
        total_passed = 0
        total_failed = 0
        total_warnings = 0
        successful_tests = 0
        
        for script in self.test_scripts:
            script_path = os.path.join(os.path.dirname(__file__), script)
            if os.path.exists(script_path):
                success = self.run_test_script(script)
                if success:
                    successful_tests += 1
                
                # Accumulate totals
                result = self.test_results[script]
                total_passed += result["passed"]
                total_failed += result["failed"]
                total_warnings += result["warnings"]
                
                # Add delay between tests
                time.sleep(2)
            else:
                print(f"\nWARNING: Test script {script} not found, skipping...")
        
        # Generate comprehensive summary
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Test Run Duration: {duration}")
        print(f"Server URL: {self.base_url}")
        print(f"Test Scripts Executed: {successful_tests}/{len(self.test_scripts)}")
        print("-" * 80)
        print(f"Total Tests Passed: {total_passed}")
        print(f"Total Tests Failed: {total_failed}")
        print(f"Total Warnings: {total_warnings}")
        print("-" * 80)
        
        # Individual script results
        print("\nIndividual Script Results:")
        print("-" * 80)
        for script, result in self.test_results.items():
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"{script:<30} {status}")
            print(f"  Passed: {result['passed']}, Failed: {result['failed']}, Warnings: {result['warnings']}")
            
            # Show failure details if any
            if result.get("failure_details"):
                print("  Failed Tests:")
                for failure in result["failure_details"]:
                    print(f"    • {failure['test']}: {failure['details']}")
        
        # Detailed failure analysis
        if total_failed > 0:
            print("\n" + "=" * 80)
            print("DETAILED FAILURE ANALYSIS")
            print("=" * 80)
            
            failure_categories = {
                "Weather Endpoint": "Tests the /api/weather endpoint for weather forecast and plant care advice",
                "Image Analysis Endpoint": "Tests the /analyze-plant endpoint for image analysis capabilities in Image Analysis mode", 
                "Houston Climate Context": "Tests for Houston climate context in AI responses across different modes",
                "Server Connectivity": "Tests basic server connectivity and health",
                "Database Operations": "Tests database query and plant management functionality in Garden Database mode",
                "Add Plant Command": "Tests 'Add/Update plant [name]' command format in Garden Database mode",
                "Update Plant Command": "Tests 'Add/Update [name]' command format in Garden Database mode",
                "General Gardening": "Tests general gardening Q&A functionality in Garden Database mode"
            }
            
            for script, result in self.test_results.items():
                if result.get("failure_details"):
                    print(f"\n{script} Failures:")
                    print("-" * 40)
                    for failure in result["failure_details"]:
                        test_name = failure['test']
                        details = failure['details']
                        description = failure_categories.get(test_name, "Unknown test")
                        print(f"• {test_name}")
                        print(f"  Purpose: {description}")
                        print(f"  Error: {details}")
                        print()
        
        # Overall assessment
        print("\n" + "-" * 80)
        if total_failed == 0:
            print("✓ OVERALL RESULT: ALL TESTS PASSED")
            print("  The GardenLLM system is ready for four-mode implementation.")
        elif total_failed <= 2:
            print("⚠ OVERALL RESULT: MOSTLY PASSED WITH WARNINGS")
            print("  Some tests failed but the system appears mostly functional.")
        else:
            print("✗ OVERALL RESULT: MULTIPLE TEST FAILURES")
            print("  Critical issues detected. Please fix before proceeding with implementation.")
        
        print("=" * 80)
        
        # Save comprehensive results
        self.save_comprehensive_results()
        
        return total_failed == 0
    
    def save_comprehensive_results(self):
        """Save comprehensive test results to file."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.results_dir, f"comprehensive_test_results_{timestamp}.json")
        
        # Calculate totals
        total_passed = sum(result["passed"] for result in self.test_results.values())
        total_failed = sum(result["failed"] for result in self.test_results.values())
        total_warnings = sum(result["warnings"] for result in self.test_results.values())
        
        comprehensive_results = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "duration": str(datetime.now() - self.start_time)
            },
            "summary": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_warnings": total_warnings,
                "scripts_executed": len(self.test_results),
                "overall_success": total_failed == 0
            },
            "individual_results": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(comprehensive_results, f, indent=2)
        
        print(f"\nComprehensive results saved to: {filename}")
        
        # Also save a human-readable summary
        summary_filename = os.path.join(self.results_dir, f"test_summary_{timestamp}.txt")
        with open(summary_filename, 'w') as f:
            f.write("GardenLLM Comprehensive Test Summary\n")
            f.write("=" * 50 + "\n")
            f.write(f"Test Run: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Server URL: {self.base_url}\n")
            f.write(f"Duration: {datetime.now() - self.start_time}\n\n")
            f.write(f"Total Tests Passed: {total_passed}\n")
            f.write(f"Total Tests Failed: {total_failed}\n")
            f.write(f"Total Warnings: {total_warnings}\n\n")
            
            f.write("Individual Script Results:\n")
            f.write("-" * 30 + "\n")
            for script, result in self.test_results.items():
                status = "PASS" if result["success"] else "FAIL"
                f.write(f"{script}: {status}\n")
                f.write(f"  Passed: {result['passed']}, Failed: {result['failed']}, Warnings: {result['warnings']}\n")
                
                # Include failure details in summary file
                if result.get("failure_details"):
                    f.write("  Failed Tests:\n")
                    for failure in result["failure_details"]:
                        f.write(f"    • {failure['test']}: {failure['details']}\n")
                f.write("\n")
        
        print(f"Human-readable summary saved to: {summary_filename}")
        
        # Save individual test outputs
        for script, result in self.test_results.items():
            script_output_filename = os.path.join(self.results_dir, f"{script.replace('.py', '')}_output_{timestamp}.txt")
            with open(script_output_filename, 'w') as f:
                f.write(f"Output for {script}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Return Code: {result['return_code']}\n")
                f.write(f"Passed: {result['passed']}, Failed: {result['failed']}, Warnings: {result['warnings']}\n\n")
                f.write("STDOUT:\n")
                f.write("-" * 20 + "\n")
                f.write(result['stdout'])
                if result['stderr']:
                    f.write("\n\nSTDERR:\n")
                    f.write("-" * 20 + "\n")
                    f.write(result['stderr'])
            
            print(f"Individual output saved to: {script_output_filename}")

def main():
    """Main function to run the test suite."""
    # Parse command line arguments
    base_url = "https://gardenllm-server.onrender.com"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Create and run test runner
    runner = TestRunner(base_url)
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    if success:
        print("\n✓ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please review the results.")
        sys.exit(1)

if __name__ == "__main__":
    main() 