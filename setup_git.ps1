# Setup and push to GitHub repository
# Run this script manually: .\setup_git.ps1

# Set environment variables to prevent git from hanging
$env:GIT_TERMINAL_PROMPT = "0"
$env:GIT_ASKPASS = ""
$env:GIT_CREDENTIAL_HELPER = ""

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..."
    git init
}

# Set remote if not already set
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding remote origin..."
    git remote add origin https://github.com/jonDomino/grades-dashboard.git
}

# Add dashboard files
Write-Host "Adding dashboard files..."
git add dashboard.py
git add requirements.txt
git add README.md
git add .gitignore

# Commit
Write-Host "Committing files..."
git commit -m "Initial commit: Streamlit dashboard for bet analysis"

# Set branch to main
git branch -M main

# Push to GitHub
Write-Host "Pushing to GitHub..."
Write-Host "You may need to authenticate..."
git push -u origin main

Write-Host "Done!"

