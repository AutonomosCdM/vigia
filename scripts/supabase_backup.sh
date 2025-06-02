#!/bin/bash
# Supabase-specific backup script for Vigia
# Handles both schema and data backups

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/tmp/vigia_supabase_backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vigia_supabase_${DATE}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗄️  Vigia Supabase Backup Utility${NC}"
echo "====================================="

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Check if supabase is linked
check_supabase_link() {
    if ! supabase projects list 2>&1 | grep -q "LINKED.*\*"; then
        echo -e "${RED}❌ Project not linked to Supabase${NC}"
        echo -e "${YELLOW}Run: supabase link --project-ref drhatkonaoogphskkmuq${NC}"
        exit 1
    fi
}

# Function to backup schema
backup_schema() {
    echo -e "\n${YELLOW}Backing up database schema...${NC}"
    
    supabase db dump --linked --file "${BACKUP_DIR}/${BACKUP_NAME}_schema.sql"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Schema backup completed${NC}"
        echo -e "  Schema saved to: ${BACKUP_DIR}/${BACKUP_NAME}_schema.sql"
    else
        echo -e "${RED}❌ Schema backup failed${NC}"
        return 1
    fi
}

# Function to backup data
backup_data() {
    echo -e "\n${YELLOW}Backing up database data...${NC}"
    
    supabase db dump --linked --data-only --file "${BACKUP_DIR}/${BACKUP_NAME}_data.sql"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Data backup completed${NC}"
        echo -e "  Data saved to: ${BACKUP_DIR}/${BACKUP_NAME}_data.sql"
    else
        echo -e "${RED}❌ Data backup failed${NC}"
        return 1
    fi
}

# Function to backup specific schemas
backup_specific_schemas() {
    echo -e "\n${YELLOW}Backing up specific schemas...${NC}"
    
    # Backup auth schema
    echo -e "  Backing up auth schema..."
    supabase db dump --linked --schema auth --file "${BACKUP_DIR}/${BACKUP_NAME}_auth.sql"
    
    # Backup storage schema
    echo -e "  Backing up storage schema..."
    supabase db dump --linked --schema storage --file "${BACKUP_DIR}/${BACKUP_NAME}_storage.sql"
    
    # Backup public schema
    echo -e "  Backing up public schema..."
    supabase db dump --linked --schema public --file "${BACKUP_DIR}/${BACKUP_NAME}_public.sql"
    
    echo -e "${GREEN}✓ Schema-specific backups completed${NC}"
}

# Function to create compressed archive
create_archive() {
    echo -e "\n${YELLOW}Creating compressed archive...${NC}"
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" ${BACKUP_NAME}_*.sql
    
    # Remove individual SQL files if archive was created successfully
    if [ -f "${BACKUP_NAME}.tar.gz" ]; then
        rm -f ${BACKUP_NAME}_*.sql
        echo -e "${GREEN}✓ Archive created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"
        
        # Show archive size
        SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        echo -e "  Archive size: ${SIZE}"
    fi
}

# Function to list recent backups
list_backups() {
    echo -e "\n${YELLOW}Recent backups:${NC}"
    ls -lht "${BACKUP_DIR}" | grep "vigia_supabase_" | head -10
}

# Main backup process
main() {
    # Parse command line arguments
    BACKUP_TYPE="${1:-full}"
    
    echo -e "\n${GREEN}Starting ${BACKUP_TYPE} backup at $(date)${NC}"
    
    # Check Supabase link
    check_supabase_link
    
    case "$BACKUP_TYPE" in
        "full")
            backup_schema
            backup_data
            backup_specific_schemas
            ;;
        "schema")
            backup_schema
            backup_specific_schemas
            ;;
        "data")
            backup_data
            ;;
        *)
            echo -e "${RED}❌ Unknown backup type: $BACKUP_TYPE${NC}"
            echo -e "Usage: $0 [full|schema|data]"
            exit 1
            ;;
    esac
    
    # Create archive
    create_archive
    
    # List recent backups
    list_backups
    
    echo -e "\n${GREEN}✅ Backup completed successfully!${NC}"
}

# Show usage if --help is passed
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [full|schema|data]"
    echo ""
    echo "Backup types:"
    echo "  full   - Backup both schema and data (default)"
    echo "  schema - Backup only database schema"
    echo "  data   - Backup only database data"
    echo ""
    echo "Environment variables:"
    echo "  BACKUP_DIR - Directory to store backups (default: /tmp/vigia_supabase_backups)"
    exit 0
fi

# Run main function
main "$@"