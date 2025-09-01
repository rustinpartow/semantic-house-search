#!/bin/bash
# railway-health-check.sh

set -e

echo "🔍 Railway Health Check Starting..."

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found"
    exit 1
fi

# Check authentication
if ! CI=1 NO_COLOR=1 railway whoami &> /dev/null; then
    echo "❌ Not authenticated with Railway"
    exit 1
fi

echo "✅ Authenticated with Railway"

# Check project link
if ! CI=1 NO_COLOR=1 railway status &> /dev/null; then
    echo "❌ Project not linked"
    exit 1
fi

echo "✅ Project linked"

# Check service status
STATUS=$(CI=1 NO_COLOR=1 railway status 2>/dev/null | grep -i "active\|running" || echo "inactive")
if [[ "$STATUS" == *"active"* ]] || [[ "$STATUS" == *"running"* ]]; then
    echo "✅ Service is active"
else
    echo "❌ Service is not active: $STATUS"
    exit 1
fi

# Check for domain
DOMAIN=$(CI=1 NO_COLOR=1 railway domain 2>/dev/null || echo "")
if [[ -n "$DOMAIN" ]]; then
    echo "✅ Domain available: $DOMAIN"
else
    echo "❌ No domain configured"
    exit 1
fi

echo "✅ All health checks passed"
