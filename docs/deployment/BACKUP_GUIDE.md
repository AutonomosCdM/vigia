# Vigia Backup Guide

## Overview

This guide covers the complete backup strategy for the Vigia system, including database backups via Supabase, Redis data persistence, and configuration backups.

## Prerequisites

- Supabase CLI installed and linked to the project
- Access to the `autonomos-agent` Supabase project
- Write permissions to backup directories

## Supabase Database Backups

### Initial Setup

1. **Link to Supabase Project** (already completed):
   ```bash
   supabase link --project-ref drhatkonaoogphskkmuq
   ```

2. **Verify Connection**:
   ```bash
   supabase projects list
   # Should show autonomos-agent with a * indicating it's linked
   ```

### Manual Backups

Use the dedicated Supabase backup script:

```bash
# Full backup (schema + data)
./scripts/supabase_backup.sh full

# Schema only
./scripts/supabase_backup.sh schema

# Data only
./scripts/supabase_backup.sh data
```

Backups are stored in `/tmp/vigia_supabase_backups/` by default.

### Automated Backups

Set up automated backups using cron:

```bash
# Interactive setup
./scripts/setup_supabase_backup_cron.sh setup

# View current backup jobs
./scripts/setup_supabase_backup_cron.sh show

# Remove backup jobs
./scripts/setup_supabase_backup_cron.sh remove
```

#### Recommended Schedules

- **Production**: Daily full backup at 2 AM + hourly data backups
- **Staging**: Daily full backup at 2 AM
- **Development**: Weekly full backup

### Complete System Backup

For a complete system backup including Redis, logs, and configurations:

```bash
# Set encryption key for secure backups
export BACKUP_ENCRYPTION_KEY="your-secure-key"

# Run full system backup
./scripts/backup.sh
```

## Backup Contents

### Database Backup Includes

- **Schema**: All table definitions, indexes, constraints, and RLS policies
- **Data**: All records from public schema
- **Auth**: User accounts and authentication data
- **Storage**: File metadata (actual files need separate backup)

### System Backup Includes

1. **Database**: Complete Supabase dump
2. **Redis**: Cached medical protocols and embeddings
3. **Configuration**: docker-compose.yml, monitoring configs
4. **Logs**: Application and error logs
5. **Detection Results**: Processed images and analysis results

## Restoration

### Database Restoration

```bash
# Restore full backup
psql $DATABASE_URL < backup_file.sql

# Restore using Supabase CLI (when available)
supabase db push < backup_file.sql
```

### System Restoration

```bash
# Decrypt backup
export BACKUP_ENCRYPTION_KEY="your-secure-key"
./scripts/restore.sh /path/to/backup.tar.gz.enc
```

## Best Practices

1. **Regular Testing**: Test restoration process monthly
2. **Off-site Storage**: Store backups in multiple locations
3. **Encryption**: Always encrypt backups containing medical data
4. **Retention Policy**: Keep daily backups for 7 days, weekly for 4 weeks, monthly for 1 year
5. **Monitoring**: Set up alerts for backup failures

## Backup Verification

```bash
# Verify backup integrity
tar -tzf backup.tar.gz

# Check backup size trends
ls -lh ~/vigia_backups/ | tail -20

# View backup logs
tail -f ~/vigia_backups/backup.log
```

## Troubleshooting

### Common Issues

1. **"Cannot find project ref"**: Run `supabase link` with correct project ref
2. **"Permission denied"**: Check file permissions and database access
3. **"Connection timeout"**: Verify internet connection and Supabase status
4. **"Disk full"**: Clean old backups or increase storage

### Emergency Contacts

- Supabase Support: https://supabase.com/support
- System Admin: [Contact Information]

## Security Considerations

- Backups contain sensitive medical data
- Always use encryption for backups
- Restrict access to backup files
- Audit backup access regularly
- Comply with HIPAA requirements for data retention

## Next Steps

1. Set up automated backups for production
2. Configure off-site backup storage (S3/GCS)
3. Implement backup monitoring and alerting
4. Create disaster recovery plan
5. Schedule regular restoration drills