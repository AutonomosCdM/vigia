#!/bin/bash
# Setup automated Supabase backups via cron

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_SCRIPT="${SCRIPT_DIR}/supabase_backup.sh"
BACKUP_DIR="${HOME}/vigia_backups"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}⚙️  Vigia Supabase Backup Cron Setup${NC}"
echo "========================================"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Function to add cron job
add_cron_job() {
    SCHEDULE="$1"
    BACKUP_TYPE="$2"
    
    # Create cron command
    CRON_CMD="${SCHEDULE} BACKUP_DIR=${BACKUP_DIR} ${BACKUP_SCRIPT} ${BACKUP_TYPE} >> ${LOG_FILE} 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "${BACKUP_SCRIPT}.*${BACKUP_TYPE}"; then
        echo -e "${YELLOW}⚠  Cron job for ${BACKUP_TYPE} backup already exists${NC}"
    else
        # Add to crontab
        (crontab -l 2>/dev/null; echo "${CRON_CMD}") | crontab -
        echo -e "${GREEN}✓ Added cron job for ${BACKUP_TYPE} backup: ${SCHEDULE}${NC}"
    fi
}

# Function to remove existing cron jobs
remove_existing_jobs() {
    echo -e "\n${YELLOW}Removing existing Vigia backup cron jobs...${NC}"
    
    # Remove lines containing our backup script
    crontab -l 2>/dev/null | grep -v "${BACKUP_SCRIPT}" | crontab - || true
    
    echo -e "${GREEN}✓ Existing jobs removed${NC}"
}

# Function to show current cron jobs
show_cron_jobs() {
    echo -e "\n${YELLOW}Current Vigia backup cron jobs:${NC}"
    
    if crontab -l 2>/dev/null | grep "${BACKUP_SCRIPT}"; then
        crontab -l | grep "${BACKUP_SCRIPT}"
    else
        echo "  No Vigia backup cron jobs found"
    fi
}

# Main setup
main() {
    # Parse command line arguments
    ACTION="${1:-setup}"
    
    case "$ACTION" in
        "setup")
            echo -e "\n${GREEN}Setting up automated backups...${NC}"
            
            # Ask for backup preferences
            echo -e "\n${YELLOW}Select backup schedule:${NC}"
            echo "1) Daily full backup at 2 AM"
            echo "2) Hourly data backup"
            echo "3) Custom schedule"
            echo "4) Production schedule (daily full + hourly data)"
            read -p "Choice (1-4): " CHOICE
            
            case "$CHOICE" in
                "1")
                    remove_existing_jobs
                    add_cron_job "0 2 * * *" "full"
                    ;;
                "2")
                    remove_existing_jobs
                    add_cron_job "0 * * * *" "data"
                    ;;
                "3")
                    echo -e "\n${YELLOW}Enter cron schedule (e.g., '0 */6 * * *' for every 6 hours):${NC}"
                    read -p "Schedule: " CUSTOM_SCHEDULE
                    echo -e "\n${YELLOW}Enter backup type (full/schema/data):${NC}"
                    read -p "Type: " BACKUP_TYPE
                    remove_existing_jobs
                    add_cron_job "${CUSTOM_SCHEDULE}" "${BACKUP_TYPE}"
                    ;;
                "4")
                    remove_existing_jobs
                    # Daily full backup at 2 AM
                    add_cron_job "0 2 * * *" "full"
                    # Hourly data backup
                    add_cron_job "0 * * * *" "data"
                    ;;
                *)
                    echo -e "${RED}❌ Invalid choice${NC}"
                    exit 1
                    ;;
            esac
            
            # Create log rotation config
            echo -e "\n${YELLOW}Setting up log rotation...${NC}"
            cat > "${BACKUP_DIR}/logrotate.conf" << EOF
${LOG_FILE} {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
            echo -e "${GREEN}✓ Log rotation configured${NC}"
            
            ;;
        "remove")
            remove_existing_jobs
            ;;
        "show")
            show_cron_jobs
            ;;
        *)
            echo -e "${RED}❌ Unknown action: $ACTION${NC}"
            echo "Usage: $0 [setup|remove|show]"
            exit 1
            ;;
    esac
    
    # Show current jobs
    show_cron_jobs
    
    echo -e "\n${GREEN}✅ Setup completed!${NC}"
    echo -e "\nBackup directory: ${BACKUP_DIR}"
    echo -e "Log file: ${LOG_FILE}"
    echo -e "\nTo view logs: tail -f ${LOG_FILE}"
    echo -e "To list backups: ls -lh ${BACKUP_DIR}"
}

# Show usage if --help is passed
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [setup|remove|show]"
    echo ""
    echo "Actions:"
    echo "  setup  - Configure automated backup cron jobs (default)"
    echo "  remove - Remove all Vigia backup cron jobs"
    echo "  show   - Display current Vigia backup cron jobs"
    exit 0
fi

# Check prerequisites
if ! command -v supabase &> /dev/null; then
    echo -e "${RED}❌ Supabase CLI not found${NC}"
    echo "Please install Supabase CLI first"
    exit 1
fi

if [ ! -f "${BACKUP_SCRIPT}" ]; then
    echo -e "${RED}❌ Backup script not found: ${BACKUP_SCRIPT}${NC}"
    exit 1
fi

# Run main function
main "$@"