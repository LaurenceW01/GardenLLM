# PowerShell script to commit and push changes to git
# This script adds all changes, commits with a descriptive message, and pushes to remote
# All output is logged to a file with timestamp

# Create logs directory if it doesn't exist
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Create log file with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$logsDir\git_commit_push_$timestamp.log"

# Function to write to both console and log file
function Write-Log {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    
    # Write to console with color
    Write-Host $Message -ForegroundColor $ForegroundColor
    
    # Write to log file with timestamp
    $logMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
    Add-Content -Path $logFile -Value $logMessage
}

# Start logging
Write-Log "Starting git commit and push process..." "Green"
Write-Log "Log file: $logFile" "Cyan"

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Log "Error: Not in a git repository!" "Red"
    exit 1
}

# Check git status
Write-Log "Checking git status..." "Yellow"
$gitStatus = git status 2>&1
Write-Log $gitStatus "White"

$ErrorActionPreference = 'Stop'

# Add all changes
Write-Log "Adding all changes to git..." "Yellow"
git add -A

# Use detailed commit message explaining changes
$commitMessage = @"
Implement Weather Context Integration for AI Gardening Assistant

- Added weather_context_integration.py: Provides concise, real-time weather and forecast context for all AI conversations
- Enhanced conversation_manager.py: Injects weather context into conversation history for every user query
- Updated chat_response.py: Ensures all AI responses include up-to-date weather context
- Updated and created comprehensive tests:
  - tests/test_weather_context_integration.py: Verifies all weather context features and integration points
  - tests/test_weather_aware_chat.py: Confirms weather context is present in chat responses
  - tests/test_web_weather_integration.py: Ensures web API endpoints and UI use weather context
  - tests/show_weather_context.py: Prints generated weather context messages for manual verification
- All tests passed (9/9): Weather context is now available in chat, web, and all AI responses
- Caching and fallback logic implemented for performance and reliability
- Documentation and summary added: tests-results/weather_context_integration_summary.md

File changes:
- weather_context_integration.py: New module for weather context logic
- conversation_manager.py: Weather-aware message retrieval
- chat_response.py: Weather context injection in all AI calls
- enhanced_weather_service.py: Used for real-time weather data
- tests/: New and updated tests for all integration points
- tests-results/weather_context_integration_summary.md: Summary of implementation and test results
- commit_and_push.ps1: Updated commit message for weather context integration

This commit completes the implementation of the WEATHER_CONTEXT_INTEGRATION_PLAN.md, enabling the AI assistant to provide weather-aware gardening advice for all user queries.
"@

Write-Log "Committing with detailed message..." "Yellow"
git commit -m "$commitMessage"

# Push to current branch (which should be main now)
Write-Log "Pushing to origin/main..." "Yellow"
git push origin main

Write-Host "Commit and push complete!" 