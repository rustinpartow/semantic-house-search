#!/bin/bash
# railway-simple.sh - Ultra-simple Railway monitoring using curl

set -e

echo "🚀 Simple Railway Monitoring"
echo "============================"

# Get the Railway domain first
echo "🌐 Getting Railway domain..."
DOMAIN_OUTPUT=$(CI=1 NO_COLOR=1 railway domain 2>/dev/null || echo "")

if [[ -z "$DOMAIN_OUTPUT" ]]; then
    echo "❌ No Railway domain found"
    echo "💡 This means the service is not exposed yet"
    exit 1
fi

# Extract domain from output (look for .up.railway.app)
DOMAIN=$(echo "$DOMAIN_OUTPUT" | grep -o '[a-zA-Z0-9-]*\.up\.railway\.app' | head -1)

if [[ -z "$DOMAIN" ]]; then
    echo "❌ Could not extract domain from output:"
    echo "$DOMAIN_OUTPUT"
    exit 1
fi

echo "✅ Domain found: $DOMAIN"

# Test the health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_URL="https://$DOMAIN/health"

if curl -s --max-time 10 "$HEALTH_URL" > /dev/null; then
    echo "✅ Health endpoint responding"
    
    # Get the actual response
    echo "📋 Health response:"
    curl -s --max-time 10 "$HEALTH_URL" | jq '.' 2>/dev/null || curl -s --max-time 10 "$HEALTH_URL"
else
    echo "❌ Health endpoint not responding"
    exit 1
fi

echo ""
echo "🎉 Railway service is working!"
echo "🔗 URL: https://$DOMAIN"
