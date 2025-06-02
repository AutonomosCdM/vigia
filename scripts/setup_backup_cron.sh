#!/bin/bash
# Setup automated backups for Vigia

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🕐 Setting up automated backups${NC}"
echo "================================"

# Create backup directory
sudo mkdir -p /backups/vigia
sudo chown $(whoami):$(whoami) /backups/vigia

# Create backup script wrapper
cat > /tmp/vigia_backup_cron.sh << 'EOF'
#!/bin/bash
# Vigia automated backup wrapper

# Load environment variables
export BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"
export BACKUP_S3_BUCKET="${BACKUP_S3_BUCKET}"

# Change to Vigia directory
cd /path/to/vigia

# Run backup
./scripts/backup.sh >> /var/log/vigia_backup.log 2>&1
EOF

# Make it executable
chmod +x /tmp/vigia_backup_cron.sh
sudo mv /tmp/vigia_backup_cron.sh /usr/local/bin/vigia_backup_cron.sh

# Update path in script
sudo sed -i "s|/path/to/vigia|$(pwd)|g" /usr/local/bin/vigia_backup_cron.sh

# Create log file
sudo touch /var/log/vigia_backup.log
sudo chown $(whoami):$(whoami) /var/log/vigia_backup.log

# Setup cron job
echo -e "\n${YELLOW}Choose backup schedule:${NC}"
echo "1) Daily at 2 AM"
echo "2) Weekly on Sunday at 2 AM"
echo "3) Twice daily (2 AM and 2 PM)"
echo "4) Custom schedule"

read -p "Select option (1-4): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        SCHEDULE_DESC="Daily at 2 AM"
        ;;
    2)
        CRON_SCHEDULE="0 2 * * 0"
        SCHEDULE_DESC="Weekly on Sunday at 2 AM"
        ;;
    3)
        CRON_SCHEDULE="0 2,14 * * *"
        SCHEDULE_DESC="Twice daily at 2 AM and 2 PM"
        ;;
    4)
        read -p "Enter cron schedule (e.g., '0 3 * * *'): " CRON_SCHEDULE
        SCHEDULE_DESC="Custom: $CRON_SCHEDULE"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

# Add to crontab
(crontab -l 2>/dev/null || true; echo "$CRON_SCHEDULE /usr/local/bin/vigia_backup_cron.sh") | crontab -

echo -e "\n${GREEN}✅ Automated backup configured!${NC}"
echo -e "Schedule: ${SCHEDULE_DESC}"
echo -e "Log file: /var/log/vigia_backup.log"
echo -e "\n${YELLOW}Important:${NC}"
echo "1. Set BACKUP_ENCRYPTION_KEY in your environment"
echo "2. Optionally set BACKUP_S3_BUCKET for cloud backups"
echo "3. Monitor /var/log/vigia_backup.log for backup status"

# Setup log rotation
cat > /tmp/vigia_backup_logrotate << EOF
/var/log/vigia_backup.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF

sudo mv /tmp/vigia_backup_logrotate /etc/logrotate.d/vigia_backup

echo -e "\n${GREEN}Log rotation configured${NC}"