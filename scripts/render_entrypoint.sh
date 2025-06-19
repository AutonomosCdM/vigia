#!/bin/bash
# Vigia Render Deployment Entrypoint
# Handles multiple service types for Render platform

set -e

# Set defaults
PORT=${PORT:-8000}
ENVIRONMENT=${ENVIRONMENT:-production}

echo "🏥 Starting Vigia Medical System on Render"
echo "   Port: $PORT"
echo "   Environment: $ENVIRONMENT"
echo "   Service: ${1:-web}"

# Function to start web server
start_web() {
    echo "🌐 Starting unified web server..."
    cd /app
    
    # Start FastAPI with uvicorn
    exec uvicorn vigia_detect.api.standalone:app \
        --host 0.0.0.0 \
        --port $PORT \
        --workers 1 \
        --timeout-keep-alive 65 \
        --access-log \
        --log-level info \
        --reload-exclude-dir logs \
        --reload-exclude-dir data
}

# Function to start worker
start_worker() {
    echo "👷 Starting Celery worker..."
    cd /app
    
    # Start Celery worker for background tasks
    exec celery -A vigia_detect.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=100
}

# Function to start scheduler
start_scheduler() {
    echo "⏰ Starting Celery beat scheduler..."
    cd /app
    
    # Start Celery beat for scheduled tasks
    exec celery -A vigia_detect.tasks.celery_app beat \
        --loglevel=info
}

# Health check function
health_check() {
    echo "✅ Health check endpoint active"
    exit 0
}

# Main service selector
case "${1:-web}" in
    web)
        start_web
        ;;
    worker)
        start_worker
        ;;
    scheduler)
        start_scheduler
        ;;
    health)
        health_check
        ;;
    *)
        echo "❌ Unknown service: $1"
        echo "Available services: web, worker, scheduler, health"
        exit 1
        ;;
esac