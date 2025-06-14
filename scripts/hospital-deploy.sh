#!/bin/bash
# Vigia Hospital Deployment Script
# Production-ready deployment for medical facilities

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOSPITAL_NAME="${HOSPITAL_NAME:-Hospital}"
ENVIRONMENT="${ENVIRONMENT:-hospital}"
COMPOSE_FILE="docker-compose.hospital.yml"
ENV_FILE=".env.hospital"
DATA_DIR="/var/lib/vigia"
SSL_DIR="/etc/vigia/ssl"
SECRETS_DIR="/etc/vigia/secrets"

# Logging function
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        error "Please run as a user with docker permissions"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
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
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running or not accessible"
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups | grep -q docker; then
        error "Current user is not in docker group"
        error "Please add user to docker group: sudo usermod -aG docker \$USER"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Setup directories
setup_directories() {
    log "Setting up hospital data directories..."
    
    # Create data directories
    sudo mkdir -p "$DATA_DIR"/{postgres,redis,models,images,audit,backups}
    sudo mkdir -p "$SSL_DIR"
    sudo mkdir -p "$SECRETS_DIR"
    
    # Set permissions
    sudo chown -R 1000:1000 "$DATA_DIR"
    sudo chmod -R 755 "$DATA_DIR"
    sudo chmod 600 "$SECRETS_DIR"/*
    
    success "Directories created and secured"
}

# Generate SSL certificates (self-signed for testing)
generate_ssl_certificates() {
    log "Generating SSL certificates..."
    
    if [[ ! -f "$SSL_DIR/vigia.crt" ]]; then
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/vigia.key" \
            -out "$SSL_DIR/vigia.crt" \
            -subj "/C=US/ST=State/L=City/O=$HOSPITAL_NAME/CN=vigia.hospital.local"
        
        sudo chmod 600 "$SSL_DIR/vigia.key"
        sudo chmod 644 "$SSL_DIR/vigia.crt"
        
        success "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
}

# Setup Docker secrets
setup_secrets() {
    log "Setting up Docker secrets..."
    
    # Initialize Docker Swarm if not already
    if ! docker info | grep -q "Swarm: active"; then
        log "Initializing Docker Swarm for secrets management..."
        docker swarm init
    fi
    
    # Create secrets if they don't exist
    create_secret() {
        local secret_name=$1
        local secret_file="$SECRETS_DIR/$secret_name"
        
        if ! docker secret ls | grep -q "$secret_name"; then
            if [[ -f "$secret_file" ]]; then
                docker secret create "$secret_name" "$secret_file"
                log "Created secret: $secret_name"
            else
                warn "Secret file not found: $secret_file"
                warn "Please create this file with the appropriate value"
            fi
        else
            log "Secret already exists: $secret_name"
        fi
    }
    
    # Generate random secrets if files don't exist
    generate_secret_file() {
        local secret_name=$1
        local secret_file="$SECRETS_DIR/$secret_name"
        
        if [[ ! -f "$secret_file" ]]; then
            case "$secret_name" in
                "postgres_password")
                    openssl rand -base64 32 | sudo tee "$secret_file" > /dev/null
                    ;;
                "redis_password")
                    openssl rand -base64 32 | sudo tee "$secret_file" > /dev/null
                    ;;
                "encryption_key")
                    openssl rand -base64 32 | sudo tee "$secret_file" > /dev/null
                    ;;
                "jwt_secret")
                    openssl rand -base64 64 | sudo tee "$secret_file" > /dev/null
                    ;;
                "backup_encryption_key")
                    openssl rand -base64 32 | sudo tee "$secret_file" > /dev/null
                    ;;
                "grafana_password")
                    openssl rand -base64 16 | sudo tee "$secret_file" > /dev/null
                    ;;
                "flower_auth")
                    echo "admin:$(openssl passwd -apr1 admin)" | sudo tee "$secret_file" > /dev/null
                    ;;
                *)
                    warn "Manual configuration required for: $secret_name"
                    echo "REPLACE_WITH_ACTUAL_VALUE" | sudo tee "$secret_file" > /dev/null
                    ;;
            esac
            sudo chmod 600 "$secret_file"
        fi
    }
    
    # List of required secrets
    secrets=(
        "postgres_user"
        "postgres_password"
        "redis_password"
        "encryption_key"
        "jwt_secret"
        "ssl_cert"
        "ssl_key"
        "twilio_sid"
        "twilio_token"
        "slack_token"
        "slack_signing"
        "agentops_api_key"
        "flower_auth"
        "grafana_password"
        "backup_encryption_key"
    )
    
    # Generate secret files
    for secret in "${secrets[@]}"; do
        generate_secret_file "$secret"
    done
    
    # Special handling for postgres_user
    if [[ ! -f "$SECRETS_DIR/postgres_user" ]]; then
        echo "vigia_user" | sudo tee "$SECRETS_DIR/postgres_user" > /dev/null
        sudo chmod 600 "$SECRETS_DIR/postgres_user"
    fi
    
    # Copy SSL certificates to secrets
    sudo cp "$SSL_DIR/vigia.crt" "$SECRETS_DIR/ssl_cert"
    sudo cp "$SSL_DIR/vigia.key" "$SECRETS_DIR/ssl_key"
    
    # Create Docker secrets
    for secret in "${secrets[@]}"; do
        create_secret "$secret"
    done
    
    success "Docker secrets configured"
}

# Validate configuration
validate_configuration() {
    log "Validating configuration..."
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Validate compose file
    if ! docker-compose -f "$COMPOSE_FILE" config > /dev/null; then
        error "Invalid Docker compose configuration"
        exit 1
    fi
    
    success "Configuration validation passed"
}

# Pull Docker images
pull_images() {
    log "Pulling Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    success "Docker images pulled"
}

# Deploy services
deploy_services() {
    log "Deploying Vigia medical services..."
    
    # Start services in order
    log "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-postgres vigia-redis
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 30
    
    # Start core services
    log "Starting core medical services..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-celery-worker vigia-celery-beat
    
    # Start application services
    log "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-detection vigia-whatsapp vigia-slack
    
    # Start reverse proxy
    log "Starting reverse proxy..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-nginx
    
    # Start monitoring
    log "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-flower vigia-prometheus vigia-grafana
    
    # Start backup service
    log "Starting backup service..."
    docker-compose -f "$COMPOSE_FILE" up -d vigia-backup
    
    success "All services deployed"
}

# Health check
health_check() {
    log "Performing health checks..."
    
    # Wait for services to start
    sleep 60
    
    # Check service health
    services=(
        "vigia-postgres:5432"
        "vigia-redis:6379"
        "vigia-detection:8000"
        "vigia-whatsapp:8001"
    )
    
    for service in "${services[@]}"; do
        service_name=$(echo "$service" | cut -d: -f1)
        service_port=$(echo "$service" | cut -d: -f2)
        
        if docker-compose -f "$COMPOSE_FILE" exec -T "$service_name" netstat -tuln | grep -q ":$service_port"; then
            success "$service_name is healthy"
        else
            warn "$service_name health check failed"
        fi
    done
    
    # Check HTTPS endpoint
    if curl -k -s https://localhost/health > /dev/null; then
        success "HTTPS endpoint is responding"
    else
        warn "HTTPS endpoint health check failed"
    fi
}

# Show deployment info
show_deployment_info() {
    log "Vigia Hospital Deployment Complete!"
    echo
    echo "=== Deployment Information ==="
    echo "Environment: $ENVIRONMENT"
    echo "Hospital: $HOSPITAL_NAME"
    echo "Data Directory: $DATA_DIR"
    echo "SSL Directory: $SSL_DIR"
    echo
    echo "=== Service URLs ==="
    echo "Main Application: https://vigia.hospital.local"
    echo "WhatsApp Webhook: https://vigia.hospital.local/webhook/whatsapp"
    echo "Monitoring: https://vigia-admin.hospital.local:8443"
    echo "Flower (Celery): http://localhost:5555"
    echo "Grafana: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo
    echo "=== Next Steps ==="
    echo "1. Add 'vigia.hospital.local' to your /etc/hosts file"
    echo "2. Configure external secrets in $SECRETS_DIR"
    echo "3. Update SSL certificates with hospital-issued certs"
    echo "4. Configure hospital network settings"
    echo "5. Set up backup destinations"
    echo "6. Review and customize medical protocols"
    echo
    echo "=== Logs ==="
    echo "View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "Service status: docker-compose -f $COMPOSE_FILE ps"
    echo
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    # Any cleanup tasks if needed
}

# Main deployment function
main() {
    log "Starting Vigia Hospital Deployment for $HOSPITAL_NAME"
    
    check_root
    check_prerequisites
    setup_directories
    generate_ssl_certificates
    setup_secrets
    validate_configuration
    pull_images
    deploy_services
    health_check
    show_deployment_info
    
    success "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log "Stopping Vigia services..."
        docker-compose -f "$COMPOSE_FILE" down
        success "Services stopped"
        ;;
    "restart")
        log "Restarting Vigia services..."
        docker-compose -f "$COMPOSE_FILE" down
        docker-compose -f "$COMPOSE_FILE" up -d
        success "Services restarted"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "update")
        log "Updating Vigia deployment..."
        docker-compose -f "$COMPOSE_FILE" pull
        docker-compose -f "$COMPOSE_FILE" up -d
        success "Deployment updated"
        ;;
    "backup")
        log "Creating manual backup..."
        docker-compose -f "$COMPOSE_FILE" exec vigia-backup /usr/local/bin/backup.sh
        success "Backup completed"
        ;;
    "help")
        echo "Vigia Hospital Deployment Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  deploy    - Deploy Vigia hospital system (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - Show logs (optionally for specific service)"
        echo "  update    - Update and restart services"
        echo "  backup    - Create manual backup"
        echo "  help      - Show this help message"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

# Trap to ensure cleanup on exit
trap cleanup EXIT