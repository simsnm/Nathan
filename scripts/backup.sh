#!/bin/bash
set -e

# Backup script for AI Mentor Platform
# Creates timestamped backups of database and configuration

BACKUP_DIR="/opt/backups/ai-mentor"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ai-mentor-backup-$TIMESTAMP"

echo "🔄 Starting backup: $BACKUP_NAME"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "💾 Backing up database..."
if [ -f "/opt/ai-mentor/data/sessions.db" ]; then
    cp /opt/ai-mentor/data/sessions.db "$BACKUP_DIR/$BACKUP_NAME-database.db"
    echo "✅ Database backed up"
else
    echo "⚠️  No database found"
fi

# Backup environment files
echo "📋 Backing up configuration..."
cd /opt/ai-mentor
tar -czf "$BACKUP_DIR/$BACKUP_NAME-config.tar.gz" \
    .env.production \
    nginx.conf \
    docker-compose.prod.yml \
    2>/dev/null || true

echo "✅ Configuration backed up"

# Clean old backups (keep last 7 days)
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR/$BACKUP_NAME-*"

# Optional: Upload to S3 or external storage
# aws s3 cp "$BACKUP_DIR/$BACKUP_NAME-*" s3://your-backup-bucket/