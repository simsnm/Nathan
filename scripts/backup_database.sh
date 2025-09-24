#!/bin/bash
#################################################
# Nathan Database Backup Script
# Runs daily via cron to backup SQLite databases
#################################################

# Configuration
BACKUP_DIR="/var/nathan/backups"
DB_DIR="/var/nathan"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Databases to backup
DATABASES=(
    "nathan.db"
    "rate_limits.db"
)

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🔒 Starting Nathan database backup - $TIMESTAMP"
echo "================================================"

# Function to backup a database
backup_db() {
    local db_name=$1
    local db_path="$DB_DIR/$db_name"
    local backup_name="${db_name%.db}_${TIMESTAMP}.db"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [ -f "$db_path" ]; then
        echo "📦 Backing up $db_name..."
        
        # Use SQLite backup command for consistency
        sqlite3 "$db_path" ".backup '$backup_path'"
        
        if [ $? -eq 0 ]; then
            # Compress the backup
            gzip "$backup_path"
            echo "✅ Backed up to ${backup_name}.gz"
            
            # Verify backup
            if gunzip -t "${backup_path}.gz" 2>/dev/null; then
                echo "✅ Backup verified successfully"
            else
                echo "❌ Backup verification failed!"
                return 1
            fi
        else
            echo "❌ Failed to backup $db_name"
            return 1
        fi
    else
        echo "⚠️ Database $db_name not found at $db_path"
    fi
}

# Function to run VACUUM on database
optimize_db() {
    local db_name=$1
    local db_path="$DB_DIR/$db_name"
    
    if [ -f "$db_path" ]; then
        echo "🔧 Optimizing $db_name..."
        sqlite3 "$db_path" "VACUUM;"
        sqlite3 "$db_path" "ANALYZE;"
        echo "✅ Optimization complete"
    fi
}

# Backup all databases
for db in "${DATABASES[@]}"; do
    backup_db "$db"
done

# Optimize databases (after backup for safety)
echo ""
echo "🔧 Running database optimization..."
for db in "${DATABASES[@]}"; do
    optimize_db "$db"
done

# Clean old backups
echo ""
echo "🧹 Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete
DELETED_COUNT=$(find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS | wc -l)
echo "✅ Removed $DELETED_COUNT old backup(s)"

# Generate backup report
echo ""
echo "📊 Backup Summary:"
echo "=================="
echo "Backup directory: $BACKUP_DIR"
echo "Current backups:"
ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null | tail -5

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
echo ""
echo "Total backup size: $TOTAL_SIZE"

# Check disk space
DISK_USAGE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ WARNING: Disk usage is ${DISK_USAGE}% - consider cleaning up!"
fi

echo ""
echo "✅ Backup completed at $(date)"

# Exit code for cron monitoring
exit 0