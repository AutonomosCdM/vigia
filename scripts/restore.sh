#!/bin/bash
# Vigia Restore Script
# Restores system from encrypted backups

set -e

# Configuration
BACKUP_DIR="/backups/vigia"
RESTORE_DIR="/tmp/vigia_restore_$$"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 Vigia Restore System${NC}"
echo "=========================="

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <backup_file.tar.gz.enc>${NC}"
    echo -e "\nAvailable backups:"
    ls -lh "${BACKUP_DIR}"/vigia_backup_*.tar.gz.enc 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Create restore directory
mkdir -p "${RESTORE_DIR}"

# Function to decrypt backup
decrypt_backup() {
    echo -e "\n${YELLOW}Decrypting backup...${NC}"
    
    # Check if decryption key is set
    if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
        echo -e "${RED}❌ BACKUP_ENCRYPTION_KEY not set${NC}"
        echo -e "Please set the encryption key used during backup"
        exit 1
    fi
    
    # Decrypt backup
    openssl enc -d -aes-256-cbc -pbkdf2 \
        -in "$BACKUP_FILE" \
        -out "${RESTORE_DIR}/backup.tar.gz" \
        -pass env:BACKUP_ENCRYPTION_KEY
    
    # Extract backup
    cd "${RESTORE_DIR}"
    tar -xzf backup.tar.gz
    rm backup.tar.gz
    
    echo -e "${GREEN}✓ Backup decrypted${NC}"
}

# Function to restore database
restore_database() {
    echo -e "\n${YELLOW}Restoring database...${NC}"
    
    DB_BACKUP=$(find "${RESTORE_DIR}" -name "*_database.sql" -type f | head -1)
    
    if [ -n "$DB_BACKUP" ]; then
        echo -e "${YELLOW}⚠ Database restore requires manual intervention${NC}"
        echo -e "Database backup found at: $DB_BACKUP"
        echo -e "To restore Supabase database:"
        echo -e "1. supabase db reset"
        echo -e "2. psql \$DATABASE_URL < $DB_BACKUP"
    else
        echo -e "${YELLOW}⚠ No database backup found${NC}"
    fi
}

# Function to restore Redis
restore_redis() {
    echo -e "\n${YELLOW}Restoring Redis data...${NC}"
    
    REDIS_BACKUP=$(find "${RESTORE_DIR}" -name "*_redis.rdb" -type f | head -1)
    
    if [ -n "$REDIS_BACKUP" ]; then
        if docker ps | grep -q vigia-redis; then
            # Stop Redis to restore
            docker stop vigia-redis
            
            # Copy backup file
            docker cp "$REDIS_BACKUP" vigia-redis:/data/dump.rdb
            
            # Start Redis
            docker start vigia-redis
            
            echo -e "${GREEN}✓ Redis data restored${NC}"
        else
            echo -e "${YELLOW}⚠ Redis container not running${NC}"
            echo -e "Redis backup available at: $REDIS_BACKUP"
        fi
    else
        echo -e "${YELLOW}⚠ No Redis backup found${NC}"
    fi
}

# Function to restore configuration
restore_config() {
    echo -e "\n${YELLOW}Restoring configuration...${NC}"
    
    CONFIG_BACKUP=$(find "${RESTORE_DIR}" -name "*_config.tar.gz" -type f | head -1)
    
    if [ -n "$CONFIG_BACKUP" ]; then
        # Extract config to temp directory
        TEMP_CONFIG="${RESTORE_DIR}/config"
        mkdir -p "$TEMP_CONFIG"
        tar -xzf "$CONFIG_BACKUP" -C "$TEMP_CONFIG"
        
        echo -e "${GREEN}✓ Configuration extracted to: $TEMP_CONFIG${NC}"
        echo -e "${YELLOW}Review and manually copy needed configuration files${NC}"
    else
        echo -e "${YELLOW}⚠ No configuration backup found${NC}"
    fi
}

# Function to restore logs
restore_logs() {
    echo -e "\n${YELLOW}Restoring logs...${NC}"
    
    LOGS_BACKUP=$(find "${RESTORE_DIR}" -name "*_logs.tar.gz" -type f | head -1)
    
    if [ -n "$LOGS_BACKUP" ]; then
        # Ask for confirmation
        read -p "Restore logs? This will merge with existing logs (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            tar -xzf "$LOGS_BACKUP" -C .
            echo -e "${GREEN}✓ Logs restored${NC}"
        else
            echo -e "${YELLOW}Logs restoration skipped${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No logs backup found${NC}"
    fi
}

# Function to restore detection results
restore_detections() {
    echo -e "\n${YELLOW}Restoring detection results...${NC}"
    
    DETECTIONS_BACKUP=$(find "${RESTORE_DIR}" -name "*_detections.tar.gz" -type f | head -1)
    
    if [ -n "$DETECTIONS_BACKUP" ]; then
        read -p "Restore detection results? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p data/output
            tar -xzf "$DETECTIONS_BACKUP" -C .
            echo -e "${GREEN}✓ Detection results restored${NC}"
        else
            echo -e "${YELLOW}Detection results restoration skipped${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No detection results backup found${NC}"
    fi
}

# Function to verify services
verify_services() {
    echo -e "\n${YELLOW}Verifying services...${NC}"
    
    # Check Docker services
    if command -v docker-compose &> /dev/null; then
        echo -e "\nCurrent service status:"
        docker-compose ps
    fi
    
    echo -e "\n${YELLOW}Recommended steps:${NC}"
    echo "1. Review restored configuration files"
    echo "2. Update .env files with current credentials"
    echo "3. Restart services: docker-compose restart"
    echo "4. Check logs: docker-compose logs -f"
}

# Main restore process
main() {
    echo -e "\n${GREEN}Starting restore from: $(basename $BACKUP_FILE)${NC}"
    
    # Confirm restore
    echo -e "${RED}⚠️  WARNING: Restore will modify current system state${NC}"
    read -p "Continue with restore? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Restore cancelled${NC}"
        exit 0
    fi
    
    # Perform restore
    decrypt_backup
    restore_database
    restore_redis
    restore_config
    restore_logs
    restore_detections
    
    # Verify
    verify_services
    
    # Cleanup
    echo -e "\n${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "${RESTORE_DIR}"
    
    echo -e "\n${GREEN}✅ Restore completed!${NC}"
    echo -e "${YELLOW}Please review all restored files and restart services${NC}"
}

# Run main function
main