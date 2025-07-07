#!/usr/bin/env python3
"""
Version creation script for GardenLLM
Creates a version number and Git tag for the current state
"""

import subprocess
import sys
from datetime import datetime
import os

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def create_version():
    """Create a version number and Git tag"""
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version = f"v1.0.0-{timestamp}"
    
    print(f"Creating version: {version}")
    
    # Get current Git commit hash
    stdout, stderr, code = run_command("git rev-parse HEAD")
    if code == 0:
        commit_hash = stdout[:8]  # First 8 characters
        print(f"Current commit: {commit_hash}")
    else:
        print(f"Warning: Could not get commit hash: {stderr}")
        commit_hash = "unknown"
    
    # Create version file
    version_content = f"""# GardenLLM Version Information
VERSION={version}
COMMIT_HASH={commit_hash}
CREATED_AT={datetime.now().isoformat()}

# Current Features:
# - Plant care guide parsing functionality
# - Google Sheets integration  
# - Web interface for plant management
# - Multiple field update support
# - Photo URL handling
# - OpenAI integration for plant care recommendations
"""
    
    with open("VERSION.txt", "w") as f:
        f.write(version_content)
    
    print(f"Created VERSION.txt with version {version}")
    
    # Try to add to Git and create tag
    print("Adding version file to Git...")
    stdout, stderr, code = run_command("git add VERSION.txt")
    if code != 0:
        print(f"Warning: Could not add to Git: {stderr}")
    
    print("Creating Git tag...")
    stdout, stderr, code = run_command(f'git tag -a "{version}" -m "Version {version} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
    if code == 0:
        print(f"Successfully created Git tag: {version}")
    else:
        print(f"Warning: Could not create Git tag: {stderr}")
    
    print(f"\nVersion {version} has been created!")
    print("To return to this version later, use:")
    print(f"  git checkout {version}")
    print("Or to see all versions:")
    print("  git tag --list")

if __name__ == "__main__":
    create_version() 