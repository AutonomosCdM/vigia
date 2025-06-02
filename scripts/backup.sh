#!/bin/bash
# Vigia Backup Script
# Creates encrypted backups of critical data

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/tmp/vigia_backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vigia_backup_${DATE}"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔒 Vigia Backup System${NC}"
echo "=========================="

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Function to backup database
backup_database() {
    echo -e "\n${YELLOW}Backing up database...${NC}"
    
    # Export Supabase data (if using Supabase CLI)
    if command -v supabase &> /dev/null; then
        # Use linked project dump with file output
        supabase db dump --linked --data-only --file "${BACKUP_DIR}/${BACKUP_NAME}_database.sql"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Database backup completed${NC}"
            echo -e "  Database dump saved to: ${BACKUP_DIR}/${BACKUP_NAME}_database.sql"
        else
            echo -e "${RED}❌ Database backup failed${NC}"
            echo -e "${YELLOW}Make sure you're connected to the internet and have valid credentials${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Supabase CLI not found, skipping DB backup${NC}"
    fi
}

# Function to backup Redis data
backup_redis() {
    echo -e "\n${YELLOW}Backing up Redis data...${NC}"
    
    if docker ps | grep -q vigia-redis; then
        docker exec vigia-redis redis-cli BGSAVE
        sleep 5  # Wait for background save
        docker cp vigia-redis:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}_redis.rdb"
        echo -e "${GREEN}✓ Redis backup completed${NC}"
    else
        echo -e "${YELLOW}⚠ Redis container not running${NC}"
    fi
}

# Function to backup configuration
backup_config() {
    echo -e "\n${YELLOW}Backing up configuration...${NC}"
    
    # Create temp directory for configs
    TEMP_CONFIG="${BACKUP_DIR}/${BACKUP_NAME}_config"
    mkdir -p "${TEMP_CONFIG}"
    
    # Copy configuration files (excluding secrets)
    cp docker-compose.yml "${TEMP_CONFIG}/"
    cp -r monitoring/ "${TEMP_CONFIG}/" 2>/dev/null || true
    cp requirements.txt "${TEMP_CONFIG}/" 2>/dev/null || true
    cp .env.template "${TEMP_CONFIG}/" 2>/dev/null || true
    
    # Create config archive
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz" -C "${TEMP_CONFIG}" .
    rm -rf "${TEMP_CONFIG}"
    
    echo -e "${GREEN}✓ Configuration backup completed${NC}"
}

# Function to backup logs
backup_logs() {
    echo -e "\n${YELLOW}Backing up logs...${NC}"
    
    if [ -d "logs" ]; then
        # Compress logs
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz" logs/
        echo -e "${GREEN}✓ Logs backup completed${NC}"
    else
        echo -e "${YELLOW}⚠ No logs directory found${NC}"
    fi
}

# Function to backup detection results
backup_detections() {
    echo -e "\n${YELLOW}Backing up detection results...${NC}"
    
    if [ -d "data/output" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_detections.tar.gz" data/output/
        echo -e "${GREEN}✓ Detection results backup completed${NC}"
    else
        echo -e "${YELLOW}⚠ No detection results found${NC}"
    fi
}

# Function to encrypt backup
encrypt_backup() {
    echo -e "\n${YELLOW}Encrypting backup...${NC}"
    
    # Check if encryption key is set
    if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
        echo -e "${RED}❌ BACKUP_ENCRYPTION_KEY not set. Skipping encryption.${NC}"
        echo -e "${YELLOW}Set BACKUP_ENCRYPTION_KEY environment variable for encrypted backups${NC}"
        return
    fi
    
    # Create single archive of all backups
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" ${BACKUP_NAME}_*.{sql,rdb,tar.gz} 2>/dev/null || true
    
    # Encrypt with OpenSSL
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${BACKUP_NAME}.tar.gz" \
        -out "${BACKUP_NAME}.tar.gz.enc" \
        -pass env:BACKUP_ENCRYPTION_KEY
    
    # Remove unencrypted files
    rm -f ${BACKUP_NAME}_*.{sql,rdb,tar.gz}
    rm -f "${BACKUP_NAME}.tar.gz"
    
    echo -e "${GREEN}✓ Backup encrypted${NC}"
}

# Function to clean old backups
cleanup_old_backups() {
    echo -e "\n${YELLOW}Cleaning old backups...${NC}"
    
    # Find and remove backups older than retention period
    find "${BACKUP_DIR}" -name "vigia_backup_*.tar.gz.enc" -mtime +${RETENTION_DAYS} -delete
    
    echo -e "${GREEN}✓ Old backups cleaned${NC}"
}

# Function to upload to cloud (optional)
upload_to_cloud() {
    echo -e "\n${YELLOW}Uploading to cloud storage...${NC}"
    
    # Check if cloud backup is configured
    if [ -z "$BACKUP_S3_BUCKET" ]; then
        echo -e "${YELLOW}⚠ Cloud backup not configured${NC}"
        return
    fi
    
    # Upload to S3 (requires AWS CLI)
    if command -v aws &> /dev/null; then
        aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" \
            "s3://${BACKUP_S3_BUCKET}/vigia-backups/" \
            --storage-class STANDARD_IA
        
        echo -e "${GREEN}✓ Backup uploaded to S3${NC}"
    else
        echo -e "${RED}❌ AWS CLI not found${NC}"
    fi
}

# Main backup process
main() {
    echo -e "\n${GREEN}Starting backup at $(date)${NC}"
    
    # Perform backups
    backup_database
    backup_redis
    backup_config
    backup_logs
    backup_detections
    
    # Encrypt everything
    encrypt_backup
    
    # Upload to cloud if configured
    upload_to_cloud
    
    # Clean old backups
    cleanup_old_backups
    
    # Summary
    echo -e "\n${GREEN}✅ Backup completed successfully!${NC}"
    echo -e "Backup location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc"
    
    # Show backup size
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" ]; then
        SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" | cut -f1)
        echo -e "Backup size: ${SIZE}"
    fi
}

# Run main function
main