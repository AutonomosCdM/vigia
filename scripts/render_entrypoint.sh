#!/bin/bash

# Vigia Render Entrypoint Script
# Handles different service modes for Render deployment

set -e

# Set default port if not provided by Render
export PORT=${PORT:-8000}

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if Redis is available
check_redis() {
    if [ -n "$REDIS_URL" ]; then
        log "Redis URL detected: $REDIS_URL"
        return 0
    else
        log "No Redis URL detected, running in standalone mode"
        return 1
    fi
}

# Function to check if database is available
check_database() {
    if [ -n "$DATABASE_URL" ] || [ -n "$SUPABASE_URL" ]; then
        log "Database connection detected"
        return 0
    else
        log "No database connection detected, running in standalone mode"
        return 1
    fi
}

# Function to start unified web server
start_web_server() {
    log "Starting unified web server on port $PORT"
    
    # Check available services
    check_redis && export REDIS_AVAILABLE=true || export REDIS_AVAILABLE=false
    check_database && export DATABASE_AVAILABLE=true || export DATABASE_AVAILABLE=false
    
    # Start the unified web server directly
    cd /app
    exec python vigia_detect/web/unified_server.py \
        --port=$PORT \
        --host=0.0.0.0 \
        --redis-available=$REDIS_AVAILABLE \
        --database-available=$DATABASE_AVAILABLE
}

# Function to start WhatsApp service only
start_whatsapp() {
    log "Starting WhatsApp service on port $PORT"
    export FLASK_PORT=$PORT
    exec python -m vigia_detect.messaging.whatsapp.server
}

# Function to start webhook service only
start_webhook() {
    log "Starting webhook service on port $PORT"
    exec python -m vigia_detect.webhook.server --port=$PORT --host=0.0.0.0
}

# Function to start CLI processing
start_cli() {
    log "Starting CLI image processing"
    exec python -m vigia_detect.cli.process_images_refactored "$@"
}

# Function to start Celery worker
start_worker() {
    log "Starting Celery worker"
    if [ -z "$CELERY_BROKER_URL" ] && [ -z "$REDIS_URL" ]; then
        log "ERROR: No broker URL provided for Celery worker"
        exit 1
    fi
    
    # Use Redis URL as broker if CELERY_BROKER_URL not set
    export CELERY_BROKER_URL=${CELERY_BROKER_URL:-$REDIS_URL}
    
    exec celery -A vigia_detect.tasks worker \
        --loglevel=INFO \
        --concurrency=2 \
        --max-tasks-per-child=100
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  web       Start unified web server (default)"
    echo "  whatsapp  Start WhatsApp service only"
    echo "  webhook   Start webhook service only"
    echo "  worker    Start Celery worker"
    echo "  cli       Start CLI processing"
    echo "  help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PORT              Port to run web services (default: 8000)"
    echo "  REDIS_URL         Redis connection URL (optional)"
    echo "  DATABASE_URL      Database connection URL (optional)"
    echo "  SUPABASE_URL      Supabase connection URL (optional)"
    echo "  CELERY_BROKER_URL Celery broker URL (optional, defaults to REDIS_URL)"
}

# Main execution logic
case "${1:-web}" in
    web)
        start_web_server
        ;;
    whatsapp)
        start_whatsapp
        ;;
    webhook)
        start_webhook
        ;;
    worker)
        shift
        start_worker "$@"
        ;;
    cli)
        shift
        start_cli "$@"
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    *)
        log "ERROR: Unknown command: $1"
        show_usage
        exit 1
        ;;
esac