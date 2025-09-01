#!/bin/bash
# railway-safe.sh - Completely non-interactive Railway commands

set -e

# Function to run Railway commands with maximum safety
railway_safe() {
    local cmd="$1"
    local timeout_seconds="${2:-30}"
    
    echo "🔧 Running: $cmd"
    
    # Use expect to handle any prompts
    expect -c "
        set timeout $timeout_seconds
        spawn bash -c \"CI=1 NO_COLOR=1 $cmd\"
        expect {
            \"Select a\" { 
                send \"\r\"
                exp_continue 
            }
            \"? \" { 
                send \"\r\"
                exp_continue 
            }
            \"Press any key\" { 
                send \"\r\"
                exp_continue 
            }
            eof
        }
    " 2>/dev/null || {
        echo "❌ Command failed or timed out: $cmd"
        return 1
    }
}

# Function to get Railway status safely
railway_status_safe() {
    echo "📊 Getting Railway status..."
    railway_safe "railway status" 10
}

# Function to get Railway logs safely (with timeout)
railway_logs_safe() {
    echo "📋 Getting Railway logs (last 30 seconds)..."
    timeout 10s CI=1 NO_COLOR=1 railway logs 2>/dev/null || {
        echo "⚠️ Logs command timed out (this is normal for long-running logs)"
    }
}

# Function to check if service is active
railway_health_safe() {
    echo "🏥 Checking Railway health..."
    
    # Get status and check for active
    local status_output
    status_output=$(timeout 10s CI=1 NO_COLOR=1 railway status 2>/dev/null || echo "error")
    
    if [[ "$status_output" == *"error"* ]]; then
        echo "❌ Could not get Railway status"
        return 1
    fi
    
    if [[ "$status_output" == *"ACTIVE"* ]] || [[ "$status_output" == *"active"* ]]; then
        echo "✅ Service is ACTIVE"
        return 0
    else
        echo "❌ Service is not active"
        echo "Status: $status_output"
        return 1
    fi
}

# Function to check domain
railway_domain_safe() {
    echo "🌐 Checking Railway domain..."
    local domain_output
    domain_output=$(timeout 10s CI=1 NO_COLOR=1 railway domain 2>/dev/null || echo "no-domain")
    
    if [[ "$domain_output" == *"no-domain"* ]] || [[ -z "$domain_output" ]]; then
        echo "❌ No domain configured"
        return 1
    else
        echo "✅ Domain: $domain_output"
        return 0
    fi
}

# Main monitoring function
railway_monitor_safe() {
    echo "🚀 Railway Safe Monitoring Starting..."
    echo "=================================="
    
    railway_status_safe
    echo ""
    
    railway_health_safe
    echo ""
    
    railway_domain_safe
    echo ""
    
    railway_logs_safe
    echo ""
    
    echo "✅ Railway monitoring complete"
}

# Run the monitoring
railway_monitor_safe
