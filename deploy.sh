#!/bin/bash
# deploy.sh - Automated Railway deployment with verification

set -e  # Exit on any error

echo "🚀 Starting Railway deployment process..."

# 1. Run build verification
echo "📋 Running build verification tests..."
make test-build

# 2. Check git status
echo "📋 Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Staging changes..."
    git add .
    git commit -m "Deploy: $(date)"
else
    echo "✅ No changes to commit"
fi

# 3. Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ Deployment initiated! Check Railway dashboard for build status."
echo "🔗 Railway will automatically redeploy from GitHub."
