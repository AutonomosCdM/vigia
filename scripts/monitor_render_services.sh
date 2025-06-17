#!/bin/bash
#
# Vigia Medical System - Render Service Monitor
# Continuous monitoring of medical services with HIPAA compliance
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MONITOR_INTERVAL=${MONITOR_INTERVAL:-300}  # 5 minutes
ALERT_THRESHOLD=${ALERT_THRESHOLD:-3}       # Alert after 3 failures

# Service IDs
VIGIA_UNIFIED_SERVICE_ID=${VIGIA_UNIFIED_SERVICE_ID}
VIGIA_WHATSAPP_SERVICE_ID=${VIGIA_WHATSAPP_SERVICE_ID}
VIGIA_WEBHOOK_SERVICE_ID=${VIGIA_WEBHOOK_SERVICE_ID}
VIGIA_POSTGRES_SERVICE_ID=${VIGIA_POSTGRES_SERVICE_ID}
VIGIA_REDIS_SERVICE_ID=${VIGIA_REDIS_SERVICE_ID}

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check service health
check_service_health() {
    local service_id=$1
    local service_name=$2
    
    if [ -z "$service_id" ]; then
        return 0  # Skip if service ID not configured
    fi
    
    log "🔍 Checking $service_name ($service_id)..."
    
    # Get service status from Render API
    local status=$(render services get "$service_id" --output json 2>/dev/null | jq -r '.status // "unknown"')
    
    case "$status" in
        "available")
            success "$service_name is healthy"
            
            # Additional health check via HTTP endpoint
            if [[ "$service_name" == *"Web"* ]]; then
                check_http_health "$service_id" "$service_name"
            fi
            return 0
            ;;
        "build_in_progress"|"deploy_in_progress")
            warning "$service_name is deploying (status: $status)"
            return 1
            ;;
        "build_failed"|"deploy_failed")
            error "$service_name deployment failed (status: $status)"
            show_recent_logs "$service_id" "$service_name"
            return 2
            ;;
        "suspended")
            warning "$service_name is suspended"
            return 1
            ;;
        *)
            error "$service_name status unknown: $status"
            return 2
            ;;
    esac
}

# Function to check HTTP health endpoint
check_http_health() {
    local service_id=$1
    local service_name=$2
    
    # Get service URL
    local service_url=$(render services get "$service_id" --output json 2>/dev/null | jq -r '.serviceDetails.url // null')
    
    if [ "$service_url" != "null" ] && [ -n "$service_url" ]; then
        log "🌐 Testing health endpoint: $service_url/health"
        
        # Test health endpoint with timeout
        if curl -f -s --max-time 10 "$service_url/health" > /dev/null 2>&1; then
            success "$service_name health endpoint responding"
        else
            warning "$service_name health endpoint not responding"
            
            # Try to get more info from the health endpoint
            local health_response=$(curl -s --max-time 5 "$service_url/health" 2>/dev/null || echo "No response")
            log "Health response: $health_response"
        fi
    else
        warning "$service_name URL not available yet"
    fi
}

# Function to check database connectivity
check_database_health() {
    if [ -z "$VIGIA_POSTGRES_SERVICE_ID" ]; then
        return 0
    fi
    
    log "🗄️ Checking PostgreSQL database..."
    
    # Check database service status
    if check_service_health "$VIGIA_POSTGRES_SERVICE_ID" "PostgreSQL Database"; then
        # Try to connect to database
        if render psql "$VIGIA_POSTGRES_SERVICE_ID" -c "SELECT 1;" > /dev/null 2>&1; then
            success "Database connectivity verified"
        else
            warning "Database connection test failed"
        fi
    fi
}

# Function to check Redis cache
check_redis_health() {
    if [ -z "$VIGIA_REDIS_SERVICE_ID" ]; then
        return 0
    fi
    
    log "🔴 Checking Redis cache..."
    
    if check_service_health "$VIGIA_REDIS_SERVICE_ID" "Redis Cache"; then
        success "Redis cache is healthy"
    fi
}

# Function to show recent logs
show_recent_logs() {
    local service_id=$1
    local service_name=$2
    
    log "📋 Recent logs for $service_name:"
    render logs "$service_id" --num 10 | sed 's/^/  /'
}

# Function to send medical team alert
send_medical_alert() {
    local service_name=$1
    local status=$2
    local details=$3
    
    warning "🚨 Sending medical team alert for $service_name"
    
    # Try to send Slack alert if configured
    if command -v python3 &> /dev/null && [ -f "$PROJECT_DIR/vigia_detect/interfaces/slack_orchestrator.py" ]; then
        python3 "$PROJECT_DIR/vigia_detect/interfaces/slack_orchestrator.py" \
            --alert "🏥 MEDICAL ALERT: $service_name is $status. $details" \
            --priority high \
            --compliance-incident true \
            2>/dev/null || warning "Failed to send Slack alert"
    fi
    
    # Log to medical audit trail
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) MEDICAL_ALERT service=$service_name status=$status details=\"$details\"" >> /tmp/vigia_medical_alerts.log
}

# Function to perform comprehensive health check
comprehensive_health_check() {
    log "🏥 Performing comprehensive health check for Vigia Medical System..."
    
    local overall_health=0
    local service_failures=()
    
    # Check all web services
    if ! check_service_health "$VIGIA_UNIFIED_SERVICE_ID" "Unified Medical Service"; then
        service_failures+=("Unified Medical Service")
        overall_health=1
    fi
    
    if ! check_service_health "$VIGIA_WHATSAPP_SERVICE_ID" "WhatsApp Web Service"; then
        service_failures+=("WhatsApp Web Service")
        overall_health=1
    fi
    
    if ! check_service_health "$VIGIA_WEBHOOK_SERVICE_ID" "Webhook Web Service"; then
        service_failures+=("Webhook Web Service")
        overall_health=1
    fi
    
    # Check databases
    if ! check_database_health; then
        service_failures+=("PostgreSQL Database")
        overall_health=1
    fi
    
    if ! check_redis_health; then
        service_failures+=("Redis Cache")
        overall_health=1
    fi
    
    # Generate health report
    if [ $overall_health -eq 0 ]; then
        success "🎉 All Vigia medical services are healthy"
    else
        error "⚠️ Some services have issues: ${service_failures[*]}"
        
        # Send alerts for critical failures
        for service in "${service_failures[@]}"; do
            send_medical_alert "$service" "unhealthy" "Service health check failed during routine monitoring"
        done
    fi
    
    return $overall_health
}

# Function to show service dashboard
show_dashboard() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Vigia Medical System Monitor                 ║"
    echo "║                     $(date +'%Y-%m-%d %H:%M:%S')                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Service status table
    printf "%-25s %-15s %-30s\n" "Service" "Status" "URL"
    printf "%-25s %-15s %-30s\n" "-------" "------" "---"
    
    # Function to get service info
    get_service_info() {
        local service_id=$1
        local service_name=$2
        
        if [ -z "$service_id" ]; then
            printf "%-25s %-15s %-30s\n" "$service_name" "Not configured" "N/A"
            return
        fi
        
        local status=$(render services get "$service_id" --output json 2>/dev/null | jq -r '.status // "unknown"')
        local url=$(render services get "$service_id" --output json 2>/dev/null | jq -r '.serviceDetails.url // "N/A"')
        
        # Color coding
        case "$status" in
            "available") status="${GREEN}$status${NC}" ;;
            "build_in_progress"|"deploy_in_progress") status="${YELLOW}$status${NC}" ;;
            *) status="${RED}$status${NC}" ;;
        esac
        
        printf "%-25s %-15s %-30s\n" "$service_name" "$status" "$url"
    }
    
    get_service_info "$VIGIA_UNIFIED_SERVICE_ID" "Unified Medical"
    get_service_info "$VIGIA_WHATSAPP_SERVICE_ID" "WhatsApp Service"
    get_service_info "$VIGIA_WEBHOOK_SERVICE_ID" "Webhook Service"
    get_service_info "$VIGIA_POSTGRES_SERVICE_ID" "PostgreSQL DB"
    get_service_info "$VIGIA_REDIS_SERVICE_ID" "Redis Cache"
    
    echo ""
}

# Function for continuous monitoring
continuous_monitor() {
    log "🔄 Starting continuous monitoring (interval: ${MONITOR_INTERVAL}s)"
    
    local failure_count=0
    
    while true; do
        show_dashboard
        
        if comprehensive_health_check; then
            failure_count=0
        else
            failure_count=$((failure_count + 1))
            
            if [ $failure_count -ge $ALERT_THRESHOLD ]; then
                send_medical_alert "Vigia Medical System" "critical" "Multiple consecutive health check failures ($failure_count)"
                failure_count=0  # Reset after alerting
            fi
        fi
        
        log "⏳ Next check in ${MONITOR_INTERVAL} seconds..."
        sleep "$MONITOR_INTERVAL"
    done
}

# Main function
main() {
    local command=${1:-monitor}
    
    case "$command" in
        "check"|"health")
            show_dashboard
            comprehensive_health_check
            ;;
        "monitor"|"watch")
            continuous_monitor
            ;;
        "dashboard")
            show_dashboard
            ;;
        "logs")
            local service_id=${2:-$VIGIA_UNIFIED_SERVICE_ID}
            if [ -n "$service_id" ]; then
                render logs "$service_id" --follow
            else
                error "No service ID provided"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 {check|monitor|dashboard|logs [SERVICE_ID]}"
            echo ""
            echo "Commands:"
            echo "  check      - Run single health check"
            echo "  monitor    - Continuous monitoring"
            echo "  dashboard  - Show service dashboard"
            echo "  logs       - Stream service logs"
            echo ""
            exit 1
            ;;
    esac
}

# Validate prerequisites
if ! command -v render &> /dev/null; then
    error "Render CLI not found. Install with: brew install render"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    error "jq not found. Install with: brew install jq"
    exit 1
fi

if [ -z "$RENDER_API_KEY" ]; then
    error "RENDER_API_KEY not set. Run 'render login' or set API key"
    exit 1
fi

# Run main function
main "$@"