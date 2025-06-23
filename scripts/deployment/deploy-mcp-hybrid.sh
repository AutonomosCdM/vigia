#!/bin/bash
# Vigia MCP Hybrid Deployment Script
# Deploy both Docker Hub MCP services and Custom Medical MCP servers

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-production}"
SKIP_SECRETS="${SKIP_SECRETS:-false}"
SKIP_BUILDS="${SKIP_BUILDS:-false}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check Docker Swarm (for secrets)
    if ! docker info | grep -q "Swarm: active"; then
        log "Initializing Docker Swarm for secrets management..."
        docker swarm init --advertise-addr 127.0.0.1 || {
            warn "Docker Swarm already initialized or failed to initialize"
        }
    fi
    
    # Check available disk space (need at least 10GB)
    local available_space=$(df / | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 10485760 ]]; then  # 10GB in KB
        warn "Low disk space detected. Recommended: 10GB+ free space"
    fi
    
    # Check memory (need at least 8GB)
    local total_memory=$(free -m | awk 'NR==2{print $2}')
    if [[ $total_memory -lt 8192 ]]; then  # 8GB in MB
        warn "Low memory detected. Recommended: 8GB+ RAM"
    fi
    
    success "Prerequisites check completed"
}

# Setup secrets
setup_secrets() {
    if [[ "$SKIP_SECRETS" == "true" ]]; then
        log "Skipping secrets setup (SKIP_SECRETS=true)"
        return 0
    fi
    
    log "Setting up MCP secrets..."
    
    if [[ -f "./scripts/setup-mcp-secrets.sh" ]]; then
        ./scripts/setup-mcp-secrets.sh setup
    else
        error "MCP secrets setup script not found"
        exit 1
    fi
    
    success "MCP secrets configured"
}

# Build custom images
build_custom_images() {
    if [[ "$SKIP_BUILDS" == "true" ]]; then
        log "Skipping image builds (SKIP_BUILDS=true)"
        return 0
    fi
    
    log "Building custom MCP images..."
    
    # Create Dockerfiles for custom services
    create_dockerfiles
    
    # Build images
    local images=(
        "vigia/mcp-lpp-detector"
        "vigia/mcp-fhir-gateway" 
        "vigia/mcp-medical-knowledge"
        "vigia/mcp-clinical-processor"
        "vigia/mcp-gateway-router"
    )
    
    for image in "${images[@]}"; do
        log "Building $image..."
        
        case $image in
            "vigia/mcp-lpp-detector")
                docker build -f docker/mcp/lpp-detector.dockerfile -t "$image:latest" . || {
                    error "Failed to build $image"
                    exit 1
                }
                ;;
            "vigia/mcp-fhir-gateway")
                docker build -f docker/mcp/fhir-gateway.dockerfile -t "$image:latest" . || {
                    error "Failed to build $image"
                    exit 1
                }
                ;;
            "vigia/mcp-medical-knowledge")
                docker build -f docker/mcp/medical-knowledge.dockerfile -t "$image:latest" . || {
                    error "Failed to build $image"
                    exit 1
                }
                ;;
            "vigia/mcp-clinical-processor")
                docker build -f docker/mcp/clinical-processor.dockerfile -t "$image:latest" . || {
                    error "Failed to build $image"
                    exit 1
                }
                ;;
            "vigia/mcp-gateway-router")
                docker build -f docker/mcp/gateway-router.dockerfile -t "$image:latest" . || {
                    error "Failed to build $image"
                    exit 1
                }
                ;;
        esac
        
        success "Built $image"
    done
    
    success "All custom MCP images built successfully"
}

# Create Dockerfiles
create_dockerfiles() {
    log "Creating Dockerfiles for custom MCP services..."
    
    mkdir -p docker/mcp
    
    # LPP Detector Dockerfile
    cat > docker/mcp/lpp-detector.dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY vigia_detect/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional MCP dependencies
RUN pip install fastapi uvicorn aiohttp

# Copy application code
COPY vigia_detect/ /app/vigia_detect/
COPY models/ /app/models/

# Create MCP server startup script
RUN echo '#!/bin/bash\npython -m vigia_detect.mcp.medical_server --server lpp --port 8080' > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]
EOF

    # FHIR Gateway Dockerfile
    cat > docker/mcp/fhir-gateway.dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY vigia_detect/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install fastapi uvicorn aiohttp fhir.resources

# Copy application code
COPY vigia_detect/ /app/vigia_detect/

# Create MCP server startup script
RUN echo '#!/bin/bash\npython -m vigia_detect.mcp.medical_server --server fhir --port 8080' > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]
EOF

    # Medical Knowledge Dockerfile
    cat > docker/mcp/medical-knowledge.dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY vigia_detect/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install fastapi uvicorn aiohttp sentence-transformers

# Copy application code
COPY vigia_detect/ /app/vigia_detect/
COPY docs/medical/ /app/docs/
COPY vigia_detect/references/ /app/references/

# Create knowledge base server
RUN echo '#!/bin/bash\npython -c "from vigia_detect.mcp.medical_server import VigiaMLPServer; import uvicorn; server = VigiaMLPServer({\"compliance_level\": \"hipaa\"}); uvicorn.run(server.app, host=\"0.0.0.0\", port=8080)"' > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]
EOF

    # Clinical Processor Dockerfile
    cat > docker/mcp/clinical-processor.dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY vigia_detect/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install fastapi uvicorn aiohttp reportlab cryptography

# Copy application code
COPY vigia_detect/ /app/vigia_detect/

# Create clinical processor server
RUN echo '#!/bin/bash\npython -c "from vigia_detect.mcp.medical_server import VigiaMLPServer; import uvicorn; server = VigiaMLPServer({\"compliance_level\": \"hipaa\"}); uvicorn.run(server.app, host=\"0.0.0.0\", port=8080)"' > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]
EOF

    # Gateway Router Dockerfile
    cat > docker/mcp/gateway-router.dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY vigia_detect/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install fastapi uvicorn aiohttp

# Copy application code
COPY vigia_detect/ /app/vigia_detect/

# Create gateway router server
RUN echo '#!/bin/bash\npython -c "from vigia_detect.mcp.gateway import MCPGateway; import uvicorn; from fastapi import FastAPI; app = FastAPI(); uvicorn.run(app, host=\"0.0.0.0\", port=8080)"' > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]
EOF

    success "Dockerfiles created"
}

# Deploy Docker Hub MCP services
deploy_hub_services() {
    log "Deploying Docker Hub MCP services..."
    
    # Create networks first
    create_networks
    
    # Deploy hub services
    docker-compose -f docker-compose.mcp-hub.yml up -d || {
        error "Failed to deploy Docker Hub MCP services"
        exit 1
    }
    
    # Wait for services to be healthy
    wait_for_services_healthy "docker-compose.mcp-hub.yml"
    
    success "Docker Hub MCP services deployed"
}

# Deploy custom medical services
deploy_custom_services() {
    log "Deploying custom medical MCP services..."
    
    # Deploy custom services
    docker-compose -f docker-compose.mcp-custom.yml up -d || {
        error "Failed to deploy custom medical MCP services"
        exit 1
    }
    
    # Wait for services to be healthy
    wait_for_services_healthy "docker-compose.mcp-custom.yml"
    
    success "Custom medical MCP services deployed"
}

# Create Docker networks
create_networks() {
    log "Creating Docker networks..."
    
    local networks=(
        "vigia_mcp_network"
        "vigia_medical_internal"
        "vigia_billing_network"
        "vigia_audit_network"
        "vigia_his_integration"
        "vigia_monitoring"
    )
    
    for network in "${networks[@]}"; do
        if ! docker network ls | grep -q "$network"; then
            docker network create "$network" || {
                warn "Failed to create network $network (may already exist)"
            }
        fi
    done
    
    success "Docker networks created"
}

# Wait for services to be healthy
wait_for_services_healthy() {
    local compose_file=$1
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    
    log "Waiting for services to be healthy (timeout: ${timeout}s)..."
    
    while [[ $elapsed -lt $timeout ]]; do
        local unhealthy_services=()
        
        # Get service status
        while IFS= read -r line; do
            if [[ $line == *"(unhealthy)"* ]]; then
                local service_name=$(echo "$line" | awk '{print $1}')
                unhealthy_services+=("$service_name")
            fi
        done < <(docker-compose -f "$compose_file" ps)
        
        if [[ ${#unhealthy_services[@]} -eq 0 ]]; then
            success "All services are healthy"
            return 0
        fi
        
        log "Waiting for services: ${unhealthy_services[*]}"
        sleep 10
        elapsed=$((elapsed + 10))
    done
    
    error "Some services failed health checks after ${timeout}s"
    return 1
}

# Validate deployment
validate_deployment() {
    log "Validating MCP deployment..."
    
    # Test service endpoints
    local endpoints=(
        "http://localhost:8081/health"  # GitHub MCP
        "http://localhost:8082/health"  # Stripe MCP
        "http://localhost:8083/health"  # Redis MCP
        "http://localhost:8084/health"  # MongoDB MCP
        "http://localhost:8085/health"  # LPP Detector
        "http://localhost:8086/health"  # FHIR Gateway
        "http://localhost:8087/health"  # Medical Knowledge
        "http://localhost:8088/health"  # Clinical Processor
        "http://localhost:8089/health"  # MCP Router
    )
    
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null; then
            success "✓ $(echo $endpoint | cut -d'/' -f3)"
        else
            failed_endpoints+=("$endpoint")
            error "✗ $(echo $endpoint | cut -d'/' -f3)"
        fi
    done
    
    if [[ ${#failed_endpoints[@]} -eq 0 ]]; then
        success "All MCP services are responding"
        return 0
    else
        error "Failed endpoints: ${failed_endpoints[*]}"
        return 1
    fi
}

# Show deployment status
show_deployment_status() {
    log "=== VIGIA MCP HYBRID DEPLOYMENT STATUS ==="
    
    # Service counts
    local hub_services=$(docker-compose -f docker-compose.mcp-hub.yml ps | grep -c "Up")
    local custom_services=$(docker-compose -f docker-compose.mcp-custom.yml ps | grep -c "Up")
    
    info "Docker Hub MCP Services: $hub_services/4 running"
    info "Custom Medical Services: $custom_services/5 running"
    
    # Service URLs
    echo ""
    info "Service Endpoints:"
    echo "  🔗 MCP Gateway (Load Balancer): http://localhost:8080"
    echo "  🔗 GitHub MCP: http://localhost:8081"
    echo "  🔗 Stripe MCP: http://localhost:8082"
    echo "  🔗 Redis MCP: http://localhost:8083"
    echo "  🔗 MongoDB MCP: http://localhost:8084"
    echo "  🏥 LPP Detection MCP: http://localhost:8085"
    echo "  🏥 FHIR Gateway MCP: http://localhost:8086"
    echo "  🏥 Medical Knowledge MCP: http://localhost:8087"
    echo "  🏥 Clinical Processor MCP: http://localhost:8088"
    echo "  🔀 Unified MCP Router: http://localhost:8089"
    echo "  📊 Prometheus Monitoring: http://localhost:9090"
    
    # Usage examples
    echo ""
    info "Usage Examples:"
    echo "  # Test MCP Gateway status"
    echo "  curl http://localhost:8080/gateway/status"
    echo ""
    echo "  # Test LPP detection"
    echo "  curl -X POST http://localhost:8085/medical/call \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"tool\": \"detect_pressure_injury\", \"parameters\": {\"image_path\": \"/path/to/image.jpg\"}, \"medical_context\": {\"patient_id\": \"PAT123\", \"compliance_level\": \"hipaa\"}}'"
    echo ""
    echo "  # Test FHIR integration"
    echo "  curl -X POST http://localhost:8086/medical/call \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"tool\": \"create_fhir_observation\", \"parameters\": {\"lpp_observation\": {}}, \"medical_context\": {\"compliance_level\": \"hipaa\"}}'"
    
    echo ""
    success "Vigia MCP Hybrid deployment completed successfully! 🚀🏥"
}

# Cleanup function
cleanup_deployment() {
    log "Cleaning up MCP deployment..."
    
    docker-compose -f docker-compose.mcp-custom.yml down || true
    docker-compose -f docker-compose.mcp-hub.yml down || true
    
    success "MCP deployment cleaned up"
}

# Main deployment function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "Starting Vigia MCP Hybrid Deployment..."
            check_prerequisites
            setup_secrets
            build_custom_images
            deploy_hub_services
            deploy_custom_services
            validate_deployment
            show_deployment_status
            ;;
        "hub-only")
            log "Deploying Docker Hub MCP services only..."
            check_prerequisites
            setup_secrets
            create_networks
            deploy_hub_services
            validate_deployment
            ;;
        "custom-only")
            log "Deploying custom medical MCP services only..."
            check_prerequisites
            setup_secrets
            build_custom_images
            create_networks
            deploy_custom_services
            validate_deployment
            ;;
        "validate")
            log "Validating MCP deployment..."
            validate_deployment
            show_deployment_status
            ;;
        "status")
            show_deployment_status
            ;;
        "cleanup")
            cleanup_deployment
            ;;
        "help")
            echo "Vigia MCP Hybrid Deployment Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy      - Deploy complete hybrid MCP infrastructure (default)"
            echo "  hub-only    - Deploy Docker Hub MCP services only"
            echo "  custom-only - Deploy custom medical MCP services only"
            echo "  validate    - Validate existing deployment"
            echo "  status      - Show deployment status"
            echo "  cleanup     - Clean up MCP deployment"
            echo "  help        - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DEPLOYMENT_MODE           - Deployment mode (production, staging)"
            echo "  SKIP_SECRETS             - Skip secrets setup (true/false)"
            echo "  SKIP_BUILDS              - Skip image builds (true/false)"
            echo "  HEALTH_CHECK_TIMEOUT     - Health check timeout in seconds"
            ;;
        *)
            error "Unknown command: $action"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup_deployment INT TERM

# Run main function
main "$@"