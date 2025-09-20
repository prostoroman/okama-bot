#!/bin/bash
# Auto-switch to DEV branch script for shans-ai project

echo "🔄 Switching to DEV branch..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check if DEV branch exists
if ! git show-ref --verify --quiet refs/heads/DEV; then
    echo "❌ DEV branch does not exist locally"
    echo "Creating DEV branch from origin/DEV..."
    git checkout -b DEV origin/DEV
else
    # Switch to DEV branch
    git checkout DEV
fi

# Pull latest changes from origin/DEV
echo "📥 Pulling latest changes from origin/DEV..."
git pull origin DEV

echo "✅ Successfully switched to DEV branch"
echo "Current branch: $(git branch --show-current)"
