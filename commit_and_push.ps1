# PowerShell script to commit and push changes to git
# This script adds all changes, commits with a descriptive message, and pushes to remote

Write-Host "Starting git commit and push process..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "Error: Not in a git repository!" -ForegroundColor Red
    exit 1
}

# Check git status
Write-Host "Checking git status..." -ForegroundColor Yellow
git status

# Add all changes
Write-Host "Adding all changes..." -ForegroundColor Yellow
git add .

# Check if there are changes to commit
$status = git status --porcelain
if (-not $status) {
    Write-Host "No changes to commit!" -ForegroundColor Yellow
    exit 0
}

# Create commit message
$commitMessage = "Fix timezone issues and improve hourly forecast: use Houston timezone (CST), scrape actual hourly data from Click2Houston, get all 24 hours instead of 12, fix time display to show correct current time"

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m $commitMessage

# Check if commit was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Commit successful!" -ForegroundColor Green
    
    # Push to remote
    Write-Host "Pushing to remote repository..." -ForegroundColor Yellow
    git push
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Push successful! Changes have been deployed." -ForegroundColor Green
    } else {
        Write-Host "Error: Push failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Error: Commit failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Git commit and push process completed successfully!" -ForegroundColor Green 