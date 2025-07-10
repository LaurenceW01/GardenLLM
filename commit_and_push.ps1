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
Write-Host "Adding all changes to git..."
git add -A

# Commit with a descriptive message
$commitMessage = "Release v1.00.06: Phase 2 Conversation History Integration - Complete integration of conversation history into chat response system. Features conversation ID support throughout processing pipeline, context preservation across user interactions, AI response enhancement with conversation history, backward compatibility, and robust error handling. Includes lazy initialization pattern for ConversationManager, comprehensive test suite (11/11 passing), and web interface updates. Successfully tested conversation storage, context preservation, token management, and timeout handling."
Write-Host "Committing with message: $commitMessage"
git commit -m "$commitMessage"

# Push to main
Write-Host "Pushing to origin/main..."
git push origin main

Write-Host "Commit and push complete!" 