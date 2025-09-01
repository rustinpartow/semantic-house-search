#!/bin/bash
# railway-logs.sh

echo "📋 Recent Railway logs:"
CI=1 NO_COLOR=1 railway logs

echo ""
echo "📊 Service status:"
CI=1 NO_COLOR=1 railway status

echo ""
echo "🌐 Domain info:"
CI=1 NO_COLOR=1 railway domain
