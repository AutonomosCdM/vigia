#!/bin/bash
#
# Vigia Medical System - Render CLI Deployment Script
# Production-ready deployment with medical compliance validation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Configuration
ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Service IDs (set these in your environment or .env file)
VIGIA_UNIFIED_SERVICE_ID=${VIGIA_UNIFIED_SERVICE_ID}
VIGIA_WHATSAPP_SERVICE_ID=${VIGIA_WHATSAPP_SERVICE_ID}
VIGIA_WEBHOOK_SERVICE_ID=${VIGIA_WEBHOOK_SERVICE_ID}

# Function to validate prerequisites
validate_prerequisites() {
    log "🔍 Validating deployment prerequisites..."
    
    # Check Render CLI
    if ! command -v render &> /dev/null; then
        error "Render CLI not found. Install with: brew install render"
        exit 1
    fi
    
    # Check authentication
    if [ -z "$RENDER_API_KEY" ]; then
        error "RENDER_API_KEY not set. Run 'render login' or set API key"
        exit 1
    fi
    
    # Check service IDs
    if [ -z "$VIGIA_UNIFIED_SERVICE_ID" ] && [ -z "$VIGIA_WHATSAPP_SERVICE_ID" ]; then
        error "No service IDs configured. Set VIGIA_UNIFIED_SERVICE_ID or VIGIA_WHATSAPP_SERVICE_ID"
        exit 1
    fi
    
    success "Prerequisites validated"
}

# Function to run medical compliance tests
run_medical_tests() {
    log "🧪 Running medical compliance tests..."
    
    cd "$PROJECT_DIR"
    
    # Run critical medical tests
    if ! python -m pytest tests/medical/test_lpp_medical_simple.py -v; then
        error "Medical tests failed"
        exit 1
    fi
    
    # Run infrastructure tests
    if ! python -m pytest tests/infrastructure/test_hospital_deployment.py -v; then
        error "Infrastructure tests failed"
        exit 1
    fi
    
    # Validate render deployment configuration
    if ! python test_render_deployment.py; then
        error "Render deployment validation failed"
        exit 1
    fi
    
    success "All medical compliance tests passed"
}

# Function to setup environment variables
setup_environment() {
    log "⚙️ Setting up environment variables for $ENVIRONMENT..."
    
    local service_id=$1
    
    # Core medical compliance settings
    render env set "$service_id" ENVIRONMENT="$ENVIRONMENT"
    render env set "$service_id" MEDICAL_COMPLIANCE_LEVEL=hipaa
    render env set "$service_id" PHI_PROTECTION_ENABLED=true
    render env set "$service_id" AUDIT_RETENTION_YEARS=7
    render env set "$service_id" SESSION_TIMEOUT_MINUTES=15
    
    # Medical AI settings
    render env set "$service_id" VIGIA_USE_MOCK_YOLO=false
    render env set "$service_id" PYTHONPATH=/app
    
    # Import environment-specific variables if file exists
    local env_file=".env.$ENVIRONMENT"
    if [ -f "$env_file" ]; then
        log "📄 Importing variables from $env_file"
        render env import "$service_id" "$env_file"
    fi
    
    success "Environment variables configured"
}

# Function to deploy unified service (recommended)
deploy_unified_service() {
    log "🚀 Deploying unified Vigia medical service..."
    
    if [ -z "$VIGIA_UNIFIED_SERVICE_ID" ]; then
        warning "VIGIA_UNIFIED_SERVICE_ID not set, skipping unified deployment"
        return
    fi
    
    # Setup environment
    setup_environment "$VIGIA_UNIFIED_SERVICE_ID"
    
    # Create deployment
    log "🏥 Starting deployment of unified medical service..."
    if render deploys create "$VIGIA_UNIFIED_SERVICE_ID" --wait --confirm; then
        success "Unified service deployed successfully"
        
        # Validate deployment
        validate_deployment "$VIGIA_UNIFIED_SERVICE_ID"
    else
        error "Unified service deployment failed"
        exit 1
    fi
}

# Function to deploy legacy services (WhatsApp + Webhook)
deploy_legacy_services() {
    log "🚀 Deploying legacy Vigia services..."
    
    # Deploy WhatsApp service
    if [ -n "$VIGIA_WHATSAPP_SERVICE_ID" ]; then
        log "📱 Deploying WhatsApp service..."
        setup_environment "$VIGIA_WHATSAPP_SERVICE_ID"
        
        if render deploys create "$VIGIA_WHATSAPP_SERVICE_ID" --wait --confirm; then
            success "WhatsApp service deployed"
        else
            error "WhatsApp service deployment failed"
            exit 1
        fi
    fi
    
    # Deploy Webhook service
    if [ -n "$VIGIA_WEBHOOK_SERVICE_ID" ]; then
        log "🔗 Deploying webhook service..."
        setup_environment "$VIGIA_WEBHOOK_SERVICE_ID"
        
        if render deploys create "$VIGIA_WEBHOOK_SERVICE_ID" --wait --confirm; then
            success "Webhook service deployed"
        else
            error "Webhook service deployment failed"
            exit 1
        fi
    fi
}

# Function to validate deployment
validate_deployment() {
    log "🔍 Validating deployment health..."
    
    local service_id=$1
    
    # Wait for service to be available
    log "⏳ Waiting for service to be ready..."
    sleep 30
    
    # Get service URL
    local service_url=$(render services get "$service_id" --output json | jq -r '.serviceDetails.url')
    
    if [ "$service_url" != "null" ] && [ -n "$service_url" ]; then
        log "🌐 Service URL: $service_url"
        
        # Health check
        if curl -f "$service_url/health" > /dev/null 2>&1; then
            success "Health check passed: $service_url/health"
        else
            warning "Health check failed, service may still be starting"
        fi
    else
        warning "Could not determine service URL"
    fi
    
    # Show recent logs
    log "📋 Recent service logs:"
    render logs "$service_id" --num 20
}

# Function to show deployment summary
show_summary() {
    log "📊 Deployment Summary"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
    
    # List deployed services
    if [ -n "$VIGIA_UNIFIED_SERVICE_ID" ]; then
        echo "🏥 Unified Service: $VIGIA_UNIFIED_SERVICE_ID"
        render services get "$VIGIA_UNIFIED_SERVICE_ID" --output json | jq -r '.serviceDetails.url // "URL not available"'
    fi
    
    if [ -n "$VIGIA_WHATSAPP_SERVICE_ID" ]; then
        echo "📱 WhatsApp Service: $VIGIA_WHATSAPP_SERVICE_ID"
        render services get "$VIGIA_WHATSAPP_SERVICE_ID" --output json | jq -r '.serviceDetails.url // "URL not available"'
    fi
    
    if [ -n "$VIGIA_WEBHOOK_SERVICE_ID" ]; then
        echo "🔗 Webhook Service: $VIGIA_WEBHOOK_SERVICE_ID"
        render services get "$VIGIA_WEBHOOK_SERVICE_ID" --output json | jq -r '.serviceDetails.url // "URL not available"'
    fi
    
    echo ""
    success "🎉 Vigia Medical System deployed successfully to Render!"
    echo ""
    echo "Next steps:"
    echo "1. Monitor service health via Render dashboard"
    echo "2. Test medical endpoints with synthetic data"
    echo "3. Configure external integrations (Twilio, Slack)"
    echo "4. Set up monitoring and alerting"
}

# Main deployment flow
main() {
    log "🏥 Starting Vigia Medical System deployment to Render..."
    log "Environment: $ENVIRONMENT"
    
    # Validate prerequisites
    validate_prerequisites
    
    # Run medical compliance tests
    run_medical_tests
    
    # Deploy services
    if [ -n "$VIGIA_UNIFIED_SERVICE_ID" ]; then
        deploy_unified_service
    else
        deploy_legacy_services
    fi
    
    # Show summary
    show_summary
}

# Help function
show_help() {
    echo "Usage: $0 [ENVIRONMENT]"
    echo ""
    echo "Deploy Vigia Medical System to Render"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT    Deployment environment (default: production)"
    echo ""
    echo "Environment Variables:"
    echo "  RENDER_API_KEY              Render API key (required)"
    echo "  VIGIA_UNIFIED_SERVICE_ID    Unified service ID (recommended)"
    echo "  VIGIA_WHATSAPP_SERVICE_ID   WhatsApp service ID (legacy)"
    echo "  VIGIA_WEBHOOK_SERVICE_ID    Webhook service ID (legacy)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Deploy to production"
    echo "  $0 staging                  # Deploy to staging"
    echo ""
}

# Parse arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main
        ;;
esac