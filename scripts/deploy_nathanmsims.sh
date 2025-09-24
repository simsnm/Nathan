#!/bin/bash
#################################################
# Nathan Safe Deployment Script for nathanmsims.com
# This script deploys Nathan with comprehensive safety features
#################################################

set -e  # Exit on error

# Configuration
DOMAIN="nathanmsims.com"
GITHUB_REPO="https://github.com/simsnm/Nathan.git"
DEPLOY_DIR="/var/www/nathan"
SERVICE_NAME="nathan"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -hex 16)}"

echo "🚀 Starting Safe Deployment to $DOMAIN"
echo "================================================"

# Step 1: Server Setup
echo "📦 Step 1: Setting up server directories..."
sudo mkdir -p $DEPLOY_DIR
sudo mkdir -p /var/nathan  # For database
sudo chown $USER:$USER $DEPLOY_DIR
sudo chown $USER:$USER /var/nathan

# Step 2: Clone/Update Repository
echo "📥 Step 2: Cloning Nathan repository..."
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd $DEPLOY_DIR
    git pull origin main
else
    git clone $GITHUB_REPO $DEPLOY_DIR
    cd $DEPLOY_DIR
fi

# Step 3: Create SAFE Production Configuration
echo "🔒 Step 3: Creating safe production configuration..."
cat > $DEPLOY_DIR/.env.production << EOF
#################################################
# SAFE PRODUCTION CONFIG - nathanmsims.com
# Generated: $(date)
#################################################

# SAFETY SETTINGS - Keep demo mode ON for safety!
DEMO_MODE=true                    # Demo mode ON - no API costs
ENABLE_API_CALLS=false            # API calls OFF - extra safety

# Rate Limiting (strict for public deployment)
MAX_REQUESTS_PER_IP_HOUR=10       # Per IP per hour
MAX_REQUESTS_PER_IP_DAY=50        # Per IP per day  
MAX_DAILY_COST=1.00               # Max $1 per day if APIs enabled
MAX_DAILY_REQUESTS=200            # Total requests per day

# Database
DATABASE_PATH=/var/nathan/nathan.db

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=$ADMIN_PASSWORD

# CORS (your domain)
CORS_ORIGINS='["https://nathanmsims.com", "https://www.nathanmsims.com", "http://localhost:8000"]'

# Server
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/nathan/nathan.log

# API Keys (ONLY add if you want full mode - keep empty for safety!)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
EOF

# Step 4: Setup Python Environment
echo "🐍 Step 4: Setting up Python environment..."
cd $DEPLOY_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Create Systemd Service
echo "⚙️ Step 5: Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Nathan AI Assistant (Safe Mode)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
Environment="PYTHONPATH=$DEPLOY_DIR"
EnvironmentFile=$DEPLOY_DIR/.env.production
ExecStart=$DEPLOY_DIR/venv/bin/python web_app/main.py
Restart=always
RestartSec=10

# Safety limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Configure Nginx
echo "🌐 Step 6: Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << 'EOF'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=nathan_limit:10m rate=10r/h;
limit_conn_zone $binary_remote_addr zone=nathan_conn:10m;

server {
    server_name nathanmsims.com www.nathanmsims.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req zone=nathan_limit burst=5 nodelay;
    limit_conn nathan_conn 10;
    
    location / {
        # Serve static frontend
        root /var/www/nathan/web_frontend;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        # Proxy to backend
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Block admin endpoints from public
    location /api/admin {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://localhost:8000;
    }
    
    listen 80;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
sudo nginx -t

# Step 7: Start Services
echo "🚀 Step 7: Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME
sudo systemctl reload nginx

# Step 8: Setup SSL Certificate
echo "🔐 Step 8: Setting up SSL certificate..."
if ! sudo certbot certificates | grep -q $DOMAIN; then
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m nathan.m.sims@gmail.com
else
    echo "SSL certificate already exists for $DOMAIN"
fi

# Step 9: Create monitoring script
echo "📊 Step 9: Creating monitoring script..."
cat > $DEPLOY_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Nathan Monitoring Script

echo "Nathan Service Status:"
echo "======================"
systemctl status nathan --no-pager | head -n 10

echo -e "\nAPI Status:"
echo "==========="
curl -s http://localhost:8000/api/status | python3 -m json.tool

echo -e "\nRecent Logs:"
echo "============"
sudo journalctl -u nathan -n 20 --no-pager

echo -e "\nNginx Access (last 10):"
echo "======================="
sudo tail -n 10 /var/log/nginx/access.log | grep -E "api/chat|api/status"

echo -e "\nCost Status (requires admin password):"
echo "======================================"
echo "Run: curl 'http://localhost:8000/api/admin/costs?password=YOUR_ADMIN_PASSWORD'"
EOF
chmod +x $DEPLOY_DIR/monitor.sh

# Step 10: Verify Deployment
echo "✅ Step 10: Verifying deployment..."
sleep 3  # Give services time to start

# Test local API
if curl -s http://localhost:8000/api/status | grep -q "online"; then
    echo "✅ Local API is responding"
else
    echo "❌ Local API is not responding"
    sudo journalctl -u $SERVICE_NAME -n 50
    exit 1
fi

# Test public domain
if curl -s https://$DOMAIN/api/status 2>/dev/null | grep -q "online"; then
    echo "✅ Public domain is responding with SSL"
elif curl -s http://$DOMAIN/api/status | grep -q "online"; then
    echo "⚠️ Public domain responding on HTTP (SSL not yet configured)"
else
    echo "❌ Public domain is not responding"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "📝 Important Information:"
echo "-------------------------"
echo "🌐 Website: https://$DOMAIN"
echo "📊 Status: https://$DOMAIN/api/status"
echo "🔑 Admin Password: $ADMIN_PASSWORD"
echo "📁 Deploy Directory: $DEPLOY_DIR"
echo "📄 Config File: $DEPLOY_DIR/.env.production"
echo "🔍 Monitor Script: $DEPLOY_DIR/monitor.sh"
echo ""
echo "⚙️ Useful Commands:"
echo "-------------------"
echo "View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "Check status:     sudo systemctl status $SERVICE_NAME"
echo "Monitor:          $DEPLOY_DIR/monitor.sh"
echo "Edit config:      nano $DEPLOY_DIR/.env.production"
echo ""
echo "🔒 Emergency Commands:"
echo "----------------------"
echo "Disable APIs:     curl -X POST http://localhost:8000/api/admin/shutdown -d 'password=$ADMIN_PASSWORD'"
echo "Check costs:      curl 'http://localhost:8000/api/admin/costs?password=$ADMIN_PASSWORD'"
echo ""
echo "💡 Next Steps:"
echo "--------------"
echo "1. Save the admin password securely"
echo "2. Test the website at https://$DOMAIN"
echo "3. Monitor logs for first users"
echo "4. Share on social media when ready"
echo ""
echo "Nathan is now LIVE and SAFE at $DOMAIN! 🚀"