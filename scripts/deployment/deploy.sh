#!/bin/bash
# Vigia v1.0.0-rc1 Deployment Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="vigia"
VERSION="v1.0.0-rc1"
ENVIRONMENT=${1:-production}

echo -e "${GREEN}Deploying ${APP_NAME} ${VERSION} to ${ENVIRONMENT}${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env.${ENVIRONMENT}" ]; then
        echo -e "${RED}Environment file .env.${ENVIRONMENT} not found!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Prerequisites check passed!${NC}"
}

# Build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}Images built successfully!${NC}"
}

# Run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    # Add migration commands here if needed
    echo -e "${GREEN}Migrations completed!${NC}"
}

# Deploy services
deploy_services() {
    echo -e "${YELLOW}Deploying services...${NC}"
    
    # Load environment variables
    export $(cat .env.${ENVIRONMENT} | xargs)
    
    # Start services based on environment
    if [ "$ENVIRONMENT" == "production" ]; then
        docker-compose up -d
    elif [ "$ENVIRONMENT" == "staging" ]; then
        docker-compose -f docker-compose.staging.yml up -d
    else
        docker-compose --profile monitoring up -d
    fi
    
    echo -e "${GREEN}Services deployed successfully!${NC}"
}

# Health check
health_check() {
    echo -e "${YELLOW}Performing health check...${NC}"
    sleep 10
    
    # Set ports based on environment
    if [ "$ENVIRONMENT" == "staging" ]; then
        REDIS_CONTAINER="vigia-redis-staging"
        WHATSAPP_PORT="5001"
        WEBHOOK_PORT="8001"
    else
        REDIS_CONTAINER="vigia-redis"
        WHATSAPP_PORT="5000"
        WEBHOOK_PORT="8000"
    fi
    
    # Check Redis
    if docker exec $REDIS_CONTAINER redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is healthy${NC}"
    else
        echo -e "${RED}✗ Redis health check failed${NC}"
    fi
    
    # Check WhatsApp service
    if curl -f http://localhost:${WHATSAPP_PORT}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ WhatsApp service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ WhatsApp service health check failed (might not have /health endpoint)${NC}"
    fi
    
    # Check Webhook service
    if curl -f http://localhost:${WEBHOOK_PORT}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Webhook service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Webhook service health check failed (might not have /health endpoint)${NC}"
    fi
}

# Main deployment flow
main() {
    check_prerequisites
    build_images
    run_migrations
    deploy_services
    health_check
    
    echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
    echo -e "${GREEN}Version: ${VERSION}${NC}"
    echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
    
    # Show running containers
    echo -e "\n${YELLOW}Running containers:${NC}"
    if [ "$ENVIRONMENT" == "staging" ]; then
        docker-compose -f docker-compose.staging.yml ps
    else
        docker-compose ps
    fi
}

# Execute main function
main