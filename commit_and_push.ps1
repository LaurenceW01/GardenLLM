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

# Add all changes
Write-Log "Adding all changes..." "Yellow"
$gitAdd = git add . 2>&1
if ($gitAdd) {
    Write-Log $gitAdd "White"
}

# Check if there are changes to commit
$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Log "No changes to commit!" "Yellow"
    exit 0
}

# Create commit message
$commitMessage = "Fix timezone issues and improve hourly forecast: use Houston timezone (CST), scrape actual hourly data from Click2Houston, get all 24 hours instead of 12, fix time display to show correct current time"

# Commit changes
Write-Log "Committing changes..." "Yellow"
Write-Log "Commit message: $commitMessage" "Cyan"
$gitCommit = git commit -m $commitMessage 2>&1
Write-Log $gitCommit "White"

# Check if commit was successful
if ($LASTEXITCODE -eq 0) {
    Write-Log "Commit successful!" "Green"
    
    # Push to remote
    Write-Log "Pushing to remote repository..." "Yellow"
    $gitPush = git push 2>&1
    Write-Log $gitPush "White"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Push successful! Changes have been deployed." "Green"
    } else {
        Write-Log "Error: Push failed!" "Red"
        exit 1
    }
} else {
    Write-Log "Error: Commit failed!" "Red"
    exit 1
}

Write-Log "Git commit and push process completed successfully!" "Green"
Write-Log "Log saved to: $logFile" "Cyan" 