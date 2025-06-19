#!/bin/bash
# 🚀 Deploy MCP Messaging Services for Vigía
# Deployment automático de servicios MCP para WhatsApp y Slack médicos

set -e

PROJECT_ROOT="/Users/autonomos_dev/Projects/vigia"
cd "$PROJECT_ROOT"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[MCP-DEPLOY]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para validar credentials
validate_credentials() {
    log "Validando credentials MCP..."
    
    if [ -f "config/.env.mcp" ]; then
        source config/.env.mcp
    else
        warning "No se encontró config/.env.mcp, usando variables de entorno"
    fi
    
    # Validar Twilio
    if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ]; then
        warning "Twilio credentials no configuradas"
    else
        success "Twilio credentials ✓"
    fi
    
    # Validar Slack
    if [ -z "$SLACK_BOT_TOKEN" ] || [ -z "$SLACK_SIGNING_SECRET" ]; then
        warning "Slack credentials no configuradas"
    else
        success "Slack credentials ✓"
    fi
}

# Función para test de conectividad
test_mcp_connectivity() {
    log "Testing MCP server connectivity..."
    
    # Test Docker MCP
    if command -v uvx &> /dev/null; then
        log "Testing Docker MCP server..."
        timeout 10s uvx mcp-server-docker --version || warning "Docker MCP test timeout"
    else
        warning "uvx no encontrado, instalando..."
        pip install uv
        uv tool install mcp-server-docker
    fi
    
    # Test Twilio MCP
    if [ ! -z "$TWILIO_ACCOUNT_SID" ]; then
        log "Testing Twilio MCP server..."
        timeout 10s npx -y @twilio-alpha/mcp --version || warning "Twilio MCP test timeout"
    fi
    
    # Test Slack MCP
    if [ ! -z "$SLACK_BOT_TOKEN" ]; then
        log "Testing Slack MCP server..."
        timeout 10s npx -y @avimbu/slack-mcp-server --version || warning "Slack MCP test timeout"
    fi
    
    success "MCP connectivity tests completed"
}

# Función para deploy Docker Compose
deploy_docker_services() {
    log "Deploying MCP Docker services..."
    
    if [ -f "deploy/docker/docker-compose.mcp-hub.yml" ]; then
        log "Using existing docker-compose.mcp-hub.yml"
    else
        log "Creating docker-compose.mcp-hub.yml..."
        create_docker_compose_mcp
    fi
    
    # Deploy services
    docker-compose -f deploy/docker/docker-compose.mcp-hub.yml up -d
    
    # Wait for services
    log "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    check_service_health
}

# Función para crear docker-compose MCP
create_docker_compose_mcp() {
    cat > deploy/docker/docker-compose.mcp-hub.yml << 'EOF'
version: '3.8'

services:
  mcp-twilio-whatsapp:
    image: node:18-alpine
    command: npx -y @twilio-alpha/mcp
    environment:
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
    volumes:
      - ./data/mcp-logs:/app/logs
    networks:
      - vigia-mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "process.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-slack:
    image: node:18-alpine  
    command: npx -y @avimbu/slack-mcp-server
    environment:
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
    volumes:
      - ./data/slack-sessions:/app/sessions
    networks:
      - vigia-mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "process.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-whatsapp-direct:
    image: node:18-alpine
    command: npx -y whatsapp-mcp-server
    environment:
      - WHATSAPP_SESSION_PATH=/app/sessions
    volumes:
      - ./data/whatsapp-sessions:/app/sessions
    networks:
      - vigia-mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "process.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-gateway:
    build:
      context: .
      dockerfile: docker/mcp/Dockerfile.gateway
    environment:
      - REDIS_URL=redis://redis:6379
      - MCP_TWILIO_URL=http://mcp-twilio-whatsapp:8080
      - MCP_SLACK_URL=http://mcp-slack:8080
    depends_on:
      - redis
      - mcp-twilio-whatsapp
      - mcp-slack
    networks:
      - vigia-mcp-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - vigia-mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  vigia-mcp-network:
    driver: bridge

volumes:
  redis-data:
EOF
    
    success "Created docker-compose.mcp-hub.yml"
}

# Función para check health
check_service_health() {
    log "Checking service health..."
    
    services=("mcp-twilio-whatsapp" "mcp-slack" "mcp-whatsapp-direct" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose -f deploy/docker/docker-compose.mcp-hub.yml ps | grep -q "$service.*Up"; then
            success "$service is running ✓"
        else
            warning "$service is not running properly"
        fi
    done
}

# Función para integration tests
run_integration_tests() {
    log "Running MCP integration tests..."
    
    # Test básico de conectividad
    python3 -c "
import json
import os
import sys

# Test .mcp.json exists and is valid
if os.path.exists('.mcp.json'):
    with open('.mcp.json', 'r') as f:
        config = json.load(f)
    print('✓ .mcp.json is valid JSON')
    
    required_mcps = ['docker-server', 'twilio-whatsapp', 'slack']
    for mcp in required_mcps:
        if mcp in config.get('mcpServers', {}):
            print(f'✓ {mcp} configured')
        else:
            print(f'⚠ {mcp} not configured')
else:
    print('❌ .mcp.json not found')
    sys.exit(1)
" || error "Integration tests failed"
    
    success "Integration tests passed"
}

# Función para show status
show_status() {
    log "MCP Services Status:"
    echo ""
    
    # Show Docker services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f deploy/docker/docker-compose.mcp-hub.yml ps
    fi
    
    echo ""
    log "MCP Configuration:"
    if [ -f ".mcp.json" ]; then
        python3 -c "
import json
with open('.mcp.json', 'r') as f:
    config = json.load(f)
for name, server in config.get('mcpServers', {}).items():
    print(f'  ✓ {name}: {server.get(\"description\", \"No description\")}')
"
    fi
    
    echo ""
    log "Time Tracking:"
    if [ -f "scripts/utilities/claude_time_tracker.py" ]; then
        python scripts/utilities/claude_time_tracker.py dashboard
    fi
}

# Función para logs
show_logs() {
    log "Showing MCP service logs..."
    docker-compose -f deploy/docker/docker-compose.mcp-hub.yml logs -f
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            log "🚀 Starting MCP Messaging Deployment for Vigía"
            validate_credentials
            test_mcp_connectivity
            deploy_docker_services
            run_integration_tests
            success "🎉 MCP Messaging deployment completed!"
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "test")
            validate_credentials
            test_mcp_connectivity
            run_integration_tests
            ;;
        "stop")
            log "Stopping MCP services..."
            docker-compose -f deploy/docker/docker-compose.mcp-hub.yml down
            success "MCP services stopped"
            ;;
        "restart")
            log "Restarting MCP services..."
            docker-compose -f deploy/docker/docker-compose.mcp-hub.yml restart
            success "MCP services restarted"
            ;;
        *)
            echo "Usage: $0 {deploy|status|logs|test|stop|restart}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy MCP messaging services"
            echo "  status  - Show services status and configuration"
            echo "  logs    - Show service logs"
            echo "  test    - Run connectivity and integration tests"
            echo "  stop    - Stop all MCP services"
            echo "  restart - Restart all MCP services"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"