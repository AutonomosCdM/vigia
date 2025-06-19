#!/bin/bash

# Render Deployment Monitor Script
# Usage: ./render_monitor.sh [service-name-or-id]

set -e

SERVICE_NAME="${1:-vigia-medical}"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check service status
check_service_status() {
    log "🔍 Checking service status..."
    render services --output json | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | {name: .name, status: .status, url: .url}"
}

# Function to get service logs
get_logs() {
    log "📄 Getting recent logs..."
    SERVICE_ID=$(render services --output json | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | .id")
    
    if [ "$SERVICE_ID" != "null" ] && [ ! -z "$SERVICE_ID" ]; then
        render logs "$SERVICE_ID" --output text --tail 50
    else
        log "❌ Service not found: $SERVICE_NAME"
        render services --output text
    fi
}

# Function to test health endpoint
test_health() {
    log "🏥 Testing health endpoint..."
    SERVICE_URL=$(render services --output json | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | .url")
    
    if [ "$SERVICE_URL" != "null" ] && [ ! -z "$SERVICE_URL" ]; then
        curl -s "$SERVICE_URL/health" | jq '.' || echo "Health endpoint not responding"
    else
        log "❌ Service URL not available yet"
    fi
}

# Function to test MCP endpoints
test_mcp_endpoints() {
    log "🚀 Testing MCP endpoints..."
    SERVICE_URL=$(render services --output json | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | .url")
    
    if [ "$SERVICE_URL" != "null" ] && [ ! -z "$SERVICE_URL" ]; then
        echo "Testing MCP capabilities:"
        curl -s "$SERVICE_URL/api/mcp/capabilities" | jq '.' || echo "MCP capabilities not responding"
        
        echo "Testing MCP Gateway health:"
        curl -s "$SERVICE_URL/api/mcp-gateway/health" | jq '.' || echo "MCP Gateway not responding"
    else
        log "❌ Service URL not available yet"
    fi
}

# Function to monitor in real-time
monitor_realtime() {
    log "📊 Starting real-time monitoring (Ctrl+C to stop)..."
    SERVICE_ID=$(render services --output json | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | .id")
    
    if [ "$SERVICE_ID" != "null" ] && [ ! -z "$SERVICE_ID" ]; then
        render logs "$SERVICE_ID" --output text --follow
    else
        log "❌ Service not found for real-time monitoring"
    fi
}

# Main execution
case "${2:-status}" in
    "status")
        check_service_status
        ;;
    "logs")
        get_logs
        ;;
    "health")
        test_health
        ;;
    "mcp")
        test_mcp_endpoints
        ;;
    "monitor")
        monitor_realtime
        ;;
    "full")
        check_service_status
        echo "=================="
        test_health
        echo "=================="
        test_mcp_endpoints
        echo "=================="
        get_logs
        ;;
    *)
        echo "Usage: $0 [service-name] [status|logs|health|mcp|monitor|full]"
        echo "  status  - Check service status"
        echo "  logs    - Get recent logs"
        echo "  health  - Test health endpoint"
        echo "  mcp     - Test MCP endpoints"
        echo "  monitor - Real-time log monitoring"
        echo "  full    - Run all checks"
        ;;
esac