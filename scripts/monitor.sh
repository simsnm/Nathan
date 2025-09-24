#!/bin/bash

# Simple monitoring script for AI Mentor Platform
# Can be run via cron: */5 * * * * /opt/ai-mentor/scripts/monitor.sh

HEALTH_URL="http://localhost:8000/"
ALERT_EMAIL="admin@your-domain.com"
LOG_FILE="/var/log/ai-mentor-monitor.log"

# Check if service is responding
if ! curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "[$(date)] ❌ Health check failed" >> $LOG_FILE
    
    # Try to restart
    echo "[$(date)] 🔄 Attempting restart..." >> $LOG_FILE
    cd /opt/ai-mentor
    docker-compose -f docker-compose.prod.yml restart web
    
    # Wait and check again
    sleep 10
    if ! curl -f $HEALTH_URL > /dev/null 2>&1; then
        echo "[$(date)] ❌ Restart failed - sending alert" >> $LOG_FILE
        # Send alert (requires mail setup)
        echo "AI Mentor Platform is down!" | mail -s "ALERT: Service Down" $ALERT_EMAIL 2>/dev/null || true
    else
        echo "[$(date)] ✅ Service recovered after restart" >> $LOG_FILE
    fi
else
    echo "[$(date)] ✅ Health check passed" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df /opt/ai-mentor | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$(date)] ⚠️  Disk usage high: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "[$(date)] ⚠️  Memory usage high: ${MEM_USAGE}%" >> $LOG_FILE
fi

# Rotate log file if too large (>10MB)
if [ -f $LOG_FILE ] && [ $(stat -c%s "$LOG_FILE") -gt 10485760 ]; then
    mv $LOG_FILE "${LOG_FILE}.old"
    touch $LOG_FILE
fi