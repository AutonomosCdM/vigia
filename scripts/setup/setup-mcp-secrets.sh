#!/bin/bash
# Vigia MCP Secrets Management
# Setup Docker secrets for MCP services

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
    
    if ! docker swarm ca >/dev/null 2>&1; then
        log "Initializing Docker Swarm for secrets management..."
        docker swarm init --advertise-addr 127.0.0.1 || {
            warn "Docker Swarm already initialized or failed to initialize"
        }
    fi
    
    success "Docker Swarm ready for secrets management"
}

# Generate secure random password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Create Docker secret safely
create_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=${3:-""}
    
    # Check if secret already exists
    if docker secret ls --format "{{.Name}}" | grep -q "^${secret_name}$"; then
        warn "Secret ${secret_name} already exists, skipping..."
        return 0
    fi
    
    # Create the secret
    echo "$secret_value" | docker secret create "$secret_name" - >/dev/null
    success "Created secret: ${secret_name} ${description}"
}

# Setup GitHub integration secrets
setup_github_secrets() {
    log "Setting up GitHub MCP secrets..."
    
    # Prompt for GitHub token or use environment variable
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        echo -n "Enter GitHub Personal Access Token: "
        read -s github_token
        echo
    else
        github_token="$GITHUB_TOKEN"
    fi
    
    # Generate webhook secret
    github_webhook_secret=$(generate_password 32)
    
    create_secret "vigia_github_token" "$github_token" "(GitHub API access)"
    create_secret "vigia_github_webhook_secret" "$github_webhook_secret" "(GitHub webhook validation)"
    
    success "GitHub MCP secrets configured"
}

# Setup Stripe integration secrets
setup_stripe_secrets() {
    log "Setting up Stripe MCP secrets..."
    
    # Prompt for Stripe API key or use environment variable
    if [[ -z "${STRIPE_API_KEY:-}" ]]; then
        echo -n "Enter Stripe API Key (sk_live_... or sk_test_...): "
        read -s stripe_api_key
        echo
    else
        stripe_api_key="$STRIPE_API_KEY"
    fi
    
    # Generate webhook secret
    stripe_webhook_secret=$(generate_password 32)
    
    create_secret "vigia_stripe_api_key" "$stripe_api_key" "(Stripe API access)"
    create_secret "vigia_stripe_webhook_secret" "$stripe_webhook_secret" "(Stripe webhook validation)"
    
    success "Stripe MCP secrets configured"
}

# Setup Redis secrets
setup_redis_secrets() {
    log "Setting up Redis MCP secrets..."
    
    # Generate Redis password
    redis_password=$(generate_password 24)
    
    create_secret "vigia_redis_password" "$redis_password" "(Redis authentication)"
    
    success "Redis MCP secrets configured"
}

# Setup MongoDB secrets
setup_mongodb_secrets() {
    log "Setting up MongoDB MCP secrets..."
    
    # Generate MongoDB credentials
    mongodb_user="vigia_audit_admin"
    mongodb_password=$(generate_password 32)
    
    # Create credentials JSON
    mongodb_credentials=$(cat <<EOF
{
    "username": "$mongodb_user",
    "password": "$mongodb_password",
    "database": "vigia_audit",
    "authSource": "admin"
}
EOF
)
    
    create_secret "vigia_mongodb_audit_user" "$mongodb_user" "(MongoDB audit user)"
    create_secret "vigia_mongodb_audit_password" "$mongodb_password" "(MongoDB audit password)"
    create_secret "vigia_mongodb_audit_credentials" "$mongodb_credentials" "(MongoDB full credentials)"
    
    success "MongoDB MCP secrets configured"
}

# Setup medical-specific secrets
setup_medical_secrets() {
    log "Setting up medical compliance secrets..."
    
    # Medical encryption key
    medical_encryption_key=$(generate_password 64)
    
    # Digital signature certificate password
    cert_password=$(generate_password 24)
    
    # PHI encryption salt
    phi_salt=$(generate_password 32)
    
    create_secret "vigia_medical_encryption_key" "$medical_encryption_key" "(PHI encryption)"
    create_secret "vigia_cert_password" "$cert_password" "(Digital signature cert)"
    create_secret "vigia_phi_salt" "$phi_salt" "(PHI data salt)"
    
    success "Medical compliance secrets configured"
}

# Verify secrets were created
verify_secrets() {
    log "Verifying MCP secrets..."
    
    local expected_secrets=(
        "vigia_github_token"
        "vigia_github_webhook_secret"
        "vigia_stripe_api_key"
        "vigia_stripe_webhook_secret"
        "vigia_redis_password"
        "vigia_mongodb_audit_user"
        "vigia_mongodb_audit_password"
        "vigia_mongodb_audit_credentials"
        "vigia_medical_encryption_key"
        "vigia_cert_password"
        "vigia_phi_salt"
    )
    
    local created_secrets=()
    for secret in "${expected_secrets[@]}"; do
        if docker secret ls --format "{{.Name}}" | grep -q "^${secret}$"; then
            created_secrets+=("$secret")
        else
            error "Secret not found: $secret"
        fi
    done
    
    success "Verified ${#created_secrets[@]}/${#expected_secrets[@]} secrets created"
    
    # Display summary
    log "Created secrets summary:"
    for secret in "${created_secrets[@]}"; do
        local created_date=$(docker secret inspect "$secret" --format "{{.CreatedAt}}")
        echo "  ✓ $secret (created: $created_date)"
    done
}

# Generate environment file for reference
generate_env_reference() {
    log "Generating .env.mcp.example file..."
    
    cat > .env.mcp.example << 'EOF'
# Vigia MCP Environment Configuration
# This file shows which secrets are configured via Docker Secrets
# DO NOT put actual secret values in this file

# MCP Services Configuration
MCP_MODE=production
MEDICAL_COMPLIANCE_LEVEL=hipaa
PHI_PROTECTION_ENABLED=true
AUDIT_LOG_ENABLED=true

# GitHub MCP Service
# Secret: vigia_github_token
GITHUB_ORG=vigia-medical
GITHUB_WEBHOOK_URL=https://mcp-gateway.vigia.local/mcp/github/webhook

# Stripe MCP Service  
# Secret: vigia_stripe_api_key
STRIPE_MODE=production
STRIPE_WEBHOOK_URL=https://mcp-gateway.vigia.local/mcp/stripe/webhook

# Redis MCP Service
# Secret: vigia_redis_password
REDIS_URL=redis://redis-medical:6379
REDIS_MEDICAL_CACHE_TTL=900

# MongoDB MCP Service
# Secret: vigia_mongodb_audit_credentials
MONGODB_AUDIT_URL=mongodb://mongodb-audit:27017/vigia_audit
MONGODB_RETENTION_DAYS=2555

# Medical Compliance
# Secrets: vigia_medical_encryption_key, vigia_phi_salt, vigia_cert_password
AUDIT_LOG_RETENTION_DAYS=2555
DIGITAL_SIGNATURE_ENABLED=true
PHI_ENCRYPTION_ALGORITHM=AES-256-GCM

# MCP Gateway
MCP_GATEWAY_HOST=mcp-gateway.vigia.local
MCP_GATEWAY_PORT=8080
MCP_GATEWAY_SSL_PORT=8443

# Rate Limiting
MCP_RATE_LIMIT_GENERAL=10
MCP_RATE_LIMIT_MEDICAL=20
MCP_RATE_LIMIT_BILLING=5

# Monitoring
MCP_HEALTH_CHECK_INTERVAL=30s
MCP_METRICS_ENABLED=true
MCP_LOGGING_LEVEL=INFO
EOF

    success "Created .env.mcp.example reference file"
}

# Clean up function
cleanup_secrets() {
    log "Cleaning up MCP secrets..."
    
    local secrets_to_remove=(
        "vigia_github_token"
        "vigia_github_webhook_secret"
        "vigia_stripe_api_key"
        "vigia_stripe_webhook_secret"
        "vigia_redis_password"
        "vigia_mongodb_audit_user"
        "vigia_mongodb_audit_password"
        "vigia_mongodb_audit_credentials"
        "vigia_medical_encryption_key"
        "vigia_cert_password"
        "vigia_phi_salt"
    )
    
    for secret in "${secrets_to_remove[@]}"; do
        if docker secret ls --format "{{.Name}}" | grep -q "^${secret}$"; then
            docker secret rm "$secret" >/dev/null 2>&1 && success "Removed secret: $secret" || warn "Failed to remove secret: $secret"
        fi
    done
    
    success "Secret cleanup completed"
}

# Main function
main() {
    case "${1:-setup}" in
        "setup"|"create")
            log "Setting up Vigia MCP secrets..."
            check_docker
            setup_github_secrets
            setup_stripe_secrets
            setup_redis_secrets
            setup_mongodb_secrets
            setup_medical_secrets
            verify_secrets
            generate_env_reference
            success "MCP secrets setup completed successfully!"
            ;;
        "verify")
            log "Verifying MCP secrets..."
            check_docker
            verify_secrets
            ;;
        "cleanup"|"remove")
            log "Cleaning up MCP secrets..."
            check_docker
            cleanup_secrets
            ;;
        "help")
            echo "Vigia MCP Secrets Management"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  setup    - Create all MCP secrets (default)"
            echo "  create   - Alias for setup"
            echo "  verify   - Verify secrets exist"
            echo "  cleanup  - Remove all MCP secrets"
            echo "  remove   - Alias for cleanup"
            echo "  help     - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  GITHUB_TOKEN    - GitHub Personal Access Token"
            echo "  STRIPE_API_KEY  - Stripe API Key (production or test)"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"