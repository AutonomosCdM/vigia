#!/bin/bash
# Consolidated Render Deployment Script
# Combines functionality from deploy_with_render.sh and deploy_with_render_cli.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
SERVICE_TYPE="webhook"
DEPLOY_METHOD="cli"
ENVIRONMENT="production"

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --service TYPE     Service type (webhook|whatsapp|unified) [default: webhook]"
    echo "  -m, --method METHOD    Deploy method (cli|blueprint) [default: cli]"
    echo "  -e, --env ENV         Environment (production|staging|development) [default: production]"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --service webhook --method cli"
    echo "  $0 --service whatsapp --method blueprint"
    echo "  $0 --env staging"
}

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."
    
    # Check if render CLI is installed (for CLI method)
    if [[ "$DEPLOY_METHOD" == "cli" ]]; then
        if ! command -v render &> /dev/null; then
            error "Render CLI not found. Install with: npm install -g @render/cli"
        fi
        success "Render CLI found"
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        error "Git not found. Please install git"
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Not in a git repository"
    fi
    
    success "Dependencies check passed"
}

validate_environment() {
    log "Validating environment configuration..."
    
    # Check for required environment files
    local env_file="$PROJECT_ROOT/config/.env.example"
    if [[ ! -f "$env_file" ]]; then
        error "Environment template not found: $env_file"
    fi
    
    # Validate service configuration
    local service_config="$PROJECT_ROOT/dev/render/render_server.py"
    if [[ ! -f "$service_config" ]]; then
        error "Service configuration not found: $service_config"
    fi
    
    success "Environment validation passed"
}

deploy_with_cli() {
    log "Deploying with Render CLI..."
    
    # Login to Render (if not already logged in)
    if ! render auth status &> /dev/null; then
        log "Please login to Render..."
        render auth login
    fi
    
    # Create service configuration
    local service_name="vigia-${SERVICE_TYPE}-${ENVIRONMENT}"
    local start_command="python dev/render/render_server.py"
    
    log "Creating Render service: $service_name"
    
    # Set environment variable for service type
    export VIGIA_SERVICE_TYPE="$SERVICE_TYPE"
    
    # Deploy service
    render services create web \
        --name "$service_name" \
        --repo "$(git config --get remote.origin.url)" \
        --branch "$(git branch --show-current)" \
        --runtime python3 \
        --build-command "pip install -r config/requirements.txt" \
        --start-command "$start_command" \
        --env-var "VIGIA_SERVICE_TYPE=$SERVICE_TYPE" \
        --env-var "ENVIRONMENT=$ENVIRONMENT"
    
    success "Service created with Render CLI"
}

deploy_with_blueprint() {
    log "Deploying with Render Blueprint..."
    
    # Check if render.yaml exists
    local blueprint_file="$PROJECT_ROOT/render.yaml"
    if [[ ! -f "$blueprint_file" ]]; then
        log "Creating render.yaml blueprint..."
        create_blueprint
    fi
    
    # Display blueprint deployment instructions
    echo ""
    echo "🔗 Deploy with Render Blueprint:"
    echo "1. Go to: https://render.com/deploy"
    echo "2. Connect your GitHub repository"
    echo "3. Use the render.yaml configuration"
    echo "4. Set environment variables:"
    echo "   - VIGIA_SERVICE_TYPE: $SERVICE_TYPE"
    echo "   - ENVIRONMENT: $ENVIRONMENT"
    echo ""
    echo "Or click this direct link:"
    echo "https://render.com/deploy?repo=$(git config --get remote.origin.url)"
    
    success "Blueprint deployment instructions provided"
}

create_blueprint() {
    log "Creating Render blueprint configuration..."
    
    cat > "$PROJECT_ROOT/render.yaml" << EOF
services:
  - type: web
    name: vigia-${SERVICE_TYPE}
    runtime: python3
    buildCommand: pip install -r config/requirements.txt
    startCommand: python dev/render/render_server.py
    envVars:
      - key: VIGIA_SERVICE_TYPE
        value: ${SERVICE_TYPE}
      - key: ENVIRONMENT
        value: ${ENVIRONMENT}
      - key: PORT
        generateValue: true
    autoDeploy: true
    healthCheckPath: /health
EOF
    
    success "Created render.yaml blueprint"
}

setup_environment_variables() {
    log "Setting up environment variables..."
    
    # Check if credentials are configured
    if ! python "$PROJECT_ROOT/scripts/setup/setup_credentials.py" --check &> /dev/null; then
        warning "Credentials not configured. Run: python scripts/setup/setup_credentials.py"
    fi
    
    # Generate Render environment file
    if [[ -f "$PROJECT_ROOT/scripts/setup/setup_credentials.py" ]]; then
        log "Generating Render environment configuration..."
        python "$PROJECT_ROOT/scripts/setup/setup_credentials.py" --render-export
        success "Environment variables prepared"
    fi
}

validate_deployment() {
    log "Validating deployment..."
    
    # For CLI deployments, check service status
    if [[ "$DEPLOY_METHOD" == "cli" ]]; then
        local service_name="vigia-${SERVICE_TYPE}-${ENVIRONMENT}"
        
        # Wait for deployment to complete
        log "Waiting for deployment to complete..."
        sleep 30
        
        # Check service status
        if render services list | grep -q "$service_name"; then
            success "Service deployed successfully"
            
            # Get service URL
            local service_url=$(render services list --format json | jq -r ".[] | select(.name == \"$service_name\") | .serviceDetails.url")
            if [[ "$service_url" != "null" && -n "$service_url" ]]; then
                success "Service URL: $service_url"
                
                # Test health endpoint
                log "Testing health endpoint..."
                if curl -f "$service_url/health" &> /dev/null; then
                    success "Health check passed"
                else
                    warning "Health check failed - service may still be starting"
                fi
            fi
        else
            error "Service deployment failed"
        fi
    else
        success "Blueprint deployment prepared - manual verification required"
    fi
}

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--service)
                SERVICE_TYPE="$2"
                shift 2
                ;;
            -m|--method)
                DEPLOY_METHOD="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Validate arguments
    if [[ ! "$SERVICE_TYPE" =~ ^(webhook|whatsapp|unified)$ ]]; then
        error "Invalid service type: $SERVICE_TYPE"
    fi
    
    if [[ ! "$DEPLOY_METHOD" =~ ^(cli|blueprint)$ ]]; then
        error "Invalid deploy method: $DEPLOY_METHOD"
    fi
    
    if [[ ! "$ENVIRONMENT" =~ ^(production|staging|development)$ ]]; then
        error "Invalid environment: $ENVIRONMENT"
    fi
    
    # Main deployment flow
    echo "🚀 Vigia Render Deployment"
    echo "=========================="
    echo "Service Type: $SERVICE_TYPE"
    echo "Deploy Method: $DEPLOY_METHOD"
    echo "Environment: $ENVIRONMENT"
    echo ""
    
    check_dependencies
    validate_environment
    setup_environment_variables
    
    if [[ "$DEPLOY_METHOD" == "cli" ]]; then
        deploy_with_cli
    else
        deploy_with_blueprint
    fi
    
    validate_deployment
    
    success "Render deployment completed!"
}

# Run main function
main "$@"