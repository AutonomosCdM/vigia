#!/bin/bash

# Render Deployment Script
# Deploys Vigia Medical System to Render using render.yaml

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if render CLI is installed
    if ! command -v render &> /dev/null; then
        log "❌ Render CLI not found. Install with: npm install -g @render/cli"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log "❌ jq not found. Install with: brew install jq"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "render.yaml" ]; then
        log "❌ render.yaml not found. Make sure you're in the project root."
        exit 1
    fi
    
    log "✅ Prerequisites check passed"
}

# Function to validate render.yaml
validate_config() {
    log "📋 Validating render.yaml..."
    
    if ! python -c "import yaml; yaml.safe_load(open('render.yaml'))" 2>/dev/null; then
        log "❌ render.yaml is not valid YAML"
        exit 1
    fi
    
    log "✅ render.yaml is valid"
}

# Function to check authentication
check_auth() {
    log "🔐 Checking authentication..."
    
    if render whoami --output json >/dev/null 2>&1; then
        USER_INFO=$(render whoami --output json)
        USER_NAME=$(echo "$USER_INFO" | jq -r '.name // .email')
        log "✅ Authenticated as: $USER_NAME"
    else
        log "❌ Not authenticated. Run: render login"
        exit 1
    fi
}

# Function to deploy using Blueprint URL
deploy_via_blueprint() {
    log "🚀 Generating Blueprint deployment URL..."
    
    REPO_URL="https://github.com/AutonomosCdM/vigia"
    BRANCH="feature/mcp-integration-professional"
    
    DEPLOY_URL="https://render.com/deploy?repo=${REPO_URL}&branch=${BRANCH}"
    
    log "📋 Deployment Instructions:"
    echo ""
    echo "1. Open this URL in your browser:"
    echo "   $DEPLOY_URL"
    echo ""
    echo "2. Render will auto-detect render.yaml configuration"
    echo "3. Review and configure environment variables:"
    echo "   - ENVIRONMENT=production ✓"
    echo "   - VIGIA_USE_MOCK_YOLO=true ✓"
    echo "   - MCP_MODE=serverless ✓"
    echo "   - Optional: REDIS_URL, SUPABASE_URL, etc."
    echo ""
    echo "4. Click 'Deploy' to start deployment"
    echo ""
    echo "5. Monitor deployment with:"
    echo "   ./scripts/deployment/render_monitor.sh vigia-medical monitor"
    echo ""
}

# Function to check if service already exists
check_existing_service() {
    log "🔍 Checking for existing services..."
    
    if render services --output json >/dev/null 2>&1; then
        EXISTING=$(render services --output json | jq -r '.[] | select(.name=="vigia-medical") | .name' 2>/dev/null || echo "")
        
        if [ ! -z "$EXISTING" ]; then
            log "⚠️  Service 'vigia-medical' already exists"
            log "To redeploy, trigger a new deploy from the dashboard or via git push"
            return 0
        else
            log "✅ No existing 'vigia-medical' service found"
            return 1
        fi
    else
        log "⚠️  Unable to check existing services (authentication/workspace issue)"
        return 1
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    log "⏳ Waiting for deployment to complete..."
    log "Use Ctrl+C to stop waiting and check manually"
    
    sleep 5
    
    # Try to find the service and monitor
    for i in {1..12}; do
        if render services --output json >/dev/null 2>&1; then
            SERVICE_STATUS=$(render services --output json | jq -r '.[] | select(.name=="vigia-medical") | .status' 2>/dev/null || echo "")
            
            if [ ! -z "$SERVICE_STATUS" ]; then
                log "📊 Service status: $SERVICE_STATUS"
                
                if [ "$SERVICE_STATUS" = "live" ]; then
                    log "🎉 Deployment successful!"
                    
                    SERVICE_URL=$(render services --output json | jq -r '.[] | select(.name=="vigia-medical") | .url')
                    log "🌐 Service URL: $SERVICE_URL"
                    
                    # Test health endpoint
                    sleep 10
                    log "🏥 Testing health endpoint..."
                    if curl -s "$SERVICE_URL/health" >/dev/null; then
                        log "✅ Health endpoint responding"
                    else
                        log "⚠️  Health endpoint not yet responding"
                    fi
                    
                    return 0
                fi
            fi
        fi
        
        sleep 30
    done
    
    log "⏳ Deployment still in progress. Check status manually with:"
    log "   ./scripts/deployment/render_monitor.sh vigia-medical status"
}

# Main execution
main() {
    log "🚀 Starting Render Deployment for Vigia Medical System"
    
    check_prerequisites
    validate_config
    check_auth
    
    if check_existing_service; then
        log "Service already exists. Use git push to trigger redeploy."
    else
        deploy_via_blueprint
        
        read -p "Press Enter after you've started the deployment in the browser..."
        wait_for_deployment
    fi
    
    log "🎯 Deployment process complete!"
    log "Monitor with: ./scripts/deployment/render_monitor.sh vigia-medical full"
}

# Run main function
main "$@"