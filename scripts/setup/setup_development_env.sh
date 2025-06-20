#!/bin/bash
# Vigia Development Environment Setup
# Sets up local development with real services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🏥 Vigia Development Environment Setup${NC}"
echo "Setting up local development with real services..."
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local host=$2
    local port=$3
    local max_wait=${4:-30}
    
    echo -n "Waiting for $service to be ready..."
    for i in $(seq 1 $max_wait); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}❌ $service failed to start within $max_wait seconds${NC}"
    return 1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is required but not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is required but not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}❌ pip is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites found${NC}"
echo

# Setup .env file
echo -e "${YELLOW}📝 Setting up environment configuration...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.development" ]; then
        cp .env.development .env
        echo -e "${GREEN}✓ Copied .env.development to .env${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env with your actual API credentials${NC}"
    else
        echo -e "${RED}❌ .env.development not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"

if [ -f "requirements-cloudrun.txt" ]; then
    pip install -r requirements-cloudrun.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements-cloudrun.txt not found${NC}"
    exit 1
fi

# Start Docker services
echo -e "${YELLOW}🐳 Starting Docker services...${NC}"

# Stop any existing services
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Start core services
docker-compose -f docker-compose.dev.yml up -d postgres-dev redis-dev

# Wait for services to be ready
wait_for_service "PostgreSQL" "localhost" "5432" 30
wait_for_service "Redis" "localhost" "6379" 30

# Start Celery and monitoring services
echo -e "${YELLOW}🔄 Starting Celery services...${NC}"
docker-compose -f docker-compose.dev.yml up -d celery-worker-dev flower-dev

# Start optional monitoring services
echo -e "${YELLOW}📊 Starting monitoring services...${NC}"
docker-compose -f docker-compose.dev.yml up -d redis-commander pgadmin

echo -e "${GREEN}✓ All Docker services started${NC}"
echo

# Setup Ollama for local AI (optional)
echo -e "${YELLOW}🤖 Setting up Ollama for local AI...${NC}"

if command_exists ollama; then
    echo "Pulling MedGemma model (this may take a while)..."
    ollama pull medgemma:7b || echo -e "${YELLOW}⚠️  MedGemma model not available, will use alternative${NC}"
    echo -e "${GREEN}✓ Ollama configured${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not installed. Install from https://ollama.ai for local AI${NC}"
fi

# Create data directories
echo -e "${YELLOW}📁 Creating data directories...${NC}"

mkdir -p data/uploads
mkdir -p data/images
mkdir -p data/models
mkdir -p logs
mkdir -p secrets

echo -e "${GREEN}✓ Data directories created${NC}"

# Test database connection
echo -e "${YELLOW}🔗 Testing database connection...${NC}"

python3 -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect('postgresql://vigia_user:vigia_password@localhost:5432/vigia_dev')
    cur = conn.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()
    print(f'✓ Database connection successful: {version[0][:50]}...')
    cur.close()
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || exit 1

# Test Redis connection
echo -e "${YELLOW}🔗 Testing Redis connection...${NC}"

python3 -c "
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✓ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
" || exit 1

# Show service URLs
echo
echo -e "${GREEN}🎉 Development environment setup complete!${NC}"
echo
echo -e "${BLUE}📋 Service Information:${NC}"
echo "  🐘 PostgreSQL:     localhost:5432 (vigia_dev/vigia_user/vigia_password)"
echo "  🔴 Redis:          localhost:6379"
echo "  🌸 Flower:         http://localhost:5555 (Celery monitoring)"
echo "  📊 pgAdmin:        http://localhost:8080 (admin@vigia.dev/admin123)"
echo "  🔧 Redis Commander: http://localhost:8081"
echo
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. Edit .env with your API credentials (Supabase, Twilio, Slack, etc.)"
echo "  2. Run tests: python -m pytest tests/ --real-services"
echo "  3. Start the main application: python -m vigia_detect.api.main"
echo "  4. Send test WhatsApp: python examples/whatsapp_integration_demo.py"
echo
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  - Configure real API credentials in .env before testing integrations"
echo "  - Use 'docker-compose -f docker-compose.dev.yml logs' to view service logs"
echo "  - Use 'docker-compose -f docker-compose.dev.yml down' to stop all services"
echo

# Optional: Start main application
read -p "Start the main Vigia application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 Starting Vigia application...${NC}"
    python -m vigia_detect.api.main
fi