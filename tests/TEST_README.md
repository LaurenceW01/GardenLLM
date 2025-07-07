# GardenLLM Test Suite

This test suite validates all existing functionality before implementing the four-mode system. It ensures that no functionality is broken during the implementation process.

## Test Files

### Core Test Scripts
- **`test_baseline_functionality.py`** - Tests all core functionality (weather, gardening, database, image analysis)
- **`test_database_operations.py`** - Specifically tests add/update plant functionality with exact command formats
- **`test_houston_climate.py`** - Validates Houston climate context in all AI responses

### Test Runner
- **`run_all_tests.py`** - Comprehensive test runner that executes all tests and generates reports

### Documentation
- **`test_plan.md`** - Detailed test plan and strategy
- **`TEST_README.md`** - This file

## Prerequisites

1. **GardenLLM Server Running**: The GardenLLM server is running on `https://gardenllm-server.onrender.com` (or specify a different URL)
2. **Python Dependencies**: Ensure you have the required Python packages:
   ```bash
   pip install requests
   ```

## Running Tests

### Quick Start
Run all tests with the default server URL:
```bash
python run_all_tests.py
```

### Custom Server URL
Run tests against a different server:
```bash
python run_all_tests.py https://your-server.com
```

### Individual Tests
Run specific test scripts:
```bash
python test_baseline_functionality.py
python test_database_operations.py
python test_houston_climate.py
```

## Test Categories

### 1. Baseline Functionality Tests
- **Server Connectivity**: Verifies the server is running and responding
- **Weather Endpoint**: Tests weather analysis with Houston context
- **General Gardening**: Tests general gardening Q&A functionality
- **Add Plant Command**: Tests "Add/Update plant [name]" format
- **Update Plant Command**: Tests "Add/Update [name]" format
- **Image Analysis**: Tests image analysis endpoint accessibility
- **Database Operations**: Tests database query functionality
- **Houston Climate Context**: Validates Houston climate context in responses

### 2. Database Operations Tests
- **Exact Command Formats**: Validates the exact "Add/Update plant [name]" and "Add/Update [name]" formats
- **Optional Fields**: Tests handling of location and photo URL optional fields
- **AI Care Information**: Validates AI-generated comprehensive care information
- **Database Queries**: Tests plant database query functionality
- **Command Format Preservation**: Ensures only exact command formats work

### 3. Houston Climate Tests
- **General Gardening Context**: Tests Houston climate context in general gardening responses
- **Weather Mode Context**: Tests Houston climate context in weather mode responses
- **Add Plant Context**: Tests Houston climate context in add plant responses
- **Specific Indicators**: Tests for specific Houston climate indicators
- **Context Consistency**: Validates climate context consistency across endpoints

## Expected Results

### Before Implementation
All tests should pass with the following expectations:

1. **Server Connectivity**: ✓ PASS
2. **Weather Analysis**: ✓ PASS (with Houston context)
3. **General Gardening**: ✓ PASS (with Houston context)
4. **Add/Update Plant Commands**: ✓ PASS (exact format, AI care generation)
5. **Database Operations**: ✓ PASS
6. **Houston Climate Context**: ✓ PASS (in 70%+ of responses)

### Test Output
Each test generates:
- **Console Output**: Real-time test results with timestamps
- **JSON Results**: Detailed test results in JSON format
- **Summary Report**: Human-readable summary of all tests

## Test Results Files

After running tests, you'll find these files:
- `comprehensive_test_results_YYYYMMDD_HHMMSS.json` - Detailed JSON results
- `test_summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary
- `baseline_test_results_YYYYMMDD_HHMMSS.json` - Individual test results
- `database_operations_test_results_YYYYMMDD_HHMMSS.json` - Database test results
- `houston_climate_test_results_YYYYMMDD_HHMMSS.json` - Climate test results

## Success Criteria

### All Tests Must Pass
- **Server Connectivity**: Server responds with 200 status
- **Weather Mode**: Weather analysis works with Houston context
- **General Gardening**: Q&A works with Houston climate context
- **Add Plant Commands**: Exact format "Add/Update plant [name]" works
- **Update Plant Commands**: Exact format "Add/Update [name]" works
- **AI Care Generation**: Comprehensive care information is generated
- **Houston Context**: Houston climate context in 70%+ of responses

### Critical Functionality
- **Add/Update Plant**: Must work with exact command formats
- **AI Care Information**: Must be generated and parsed correctly
- **Optional Fields**: Only location and photo URL are optional
- **Houston Climate**: Must be present in all responses
- **Database Operations**: Must work without errors

## Troubleshooting

### Common Issues

1. **Server Not Running**
   ```
   ERROR: Cannot connect to server
   ```
   **Solution**: Start the GardenLLM server first

2. **Timeout Errors**
   ```
   ERROR: Test timed out after 5 minutes
   ```
   **Solution**: Check server performance or increase timeout in test script

3. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'requests'
   ```
   **Solution**: Install required packages: `pip install requests`

4. **Houston Context Missing**
   ```
   WARNING: Houston climate context not detected
   ```
   **Solution**: Check that system prompts include Houston climate instructions

### Debug Mode
To see detailed test output, run individual test scripts:
```bash
python test_baseline_functionality.py https://gardenllm-server.onrender.com
```

## Test Execution Strategy

### Before Implementation
1. Run `python run_all_tests.py`
2. Verify all tests pass
3. Save baseline results for comparison
4. Document any warnings or issues

### During Implementation
1. After each phase, run relevant tests
2. Compare results with baseline
3. Ensure no functionality regression
4. Fix any issues before proceeding

### After Implementation
1. Run comprehensive test suite
2. Verify all four modes work correctly
3. Ensure conversation memory functions
4. Validate climate context is maintained

## Test Data

The tests use standard plant names and queries:
- **Test Plants**: tomato, rosemary, basil, pepper, lettuce, carrots
- **Test Queries**: Standard gardening questions with Houston context
- **Weather Queries**: Weather-related gardening questions

## Rate Limiting

Tests include 1-second delays between requests to respect API rate limits. Adjust if needed for your server configuration.

## Support

If you encounter issues with the test suite:
1. Check the test output for specific error messages
2. Verify the server is running and accessible
3. Review the test plan in `test_plan.md`
4. Check that all dependencies are installed

## Next Steps

After successful test execution:
1. Review the test results
2. Address any warnings or failures
3. Proceed with four-mode system implementation
4. Run tests after each implementation phase
5. Maintain functionality throughout development 