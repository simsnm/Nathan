#!/bin/bash
set -e

# VPS Setup Script for AI Mentor Platform
# Tested on Ubuntu 22.04 LTS
# Usage: wget -O - https://raw.githubusercontent.com/yourrepo/scripts/setup-vps.sh | bash

echo "🚀 Setting up VPS for AI Mentor Platform"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Install essential tools
echo "🔧 Installing essential tools..."
sudo apt-get install -y \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    ncdu

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Setup fail2ban
echo "🛡️ Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/ai-mentor
sudo chown $USER:$USER /opt/ai-mentor

# Setup swap (for small VPS)
echo "💾 Setting up swap space..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
else
    echo "Swap already configured"
fi

# Create deployment user (optional)
echo "👤 Creating deployment user..."
if ! id -u deploy > /dev/null 2>&1; then
    sudo useradd -m -s /bin/bash deploy
    sudo usermod -aG docker deploy
    echo "User 'deploy' created. Set password with: sudo passwd deploy"
fi

echo "✅ VPS setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Clone your repository to /opt/ai-mentor"
echo "  2. Copy .env.production.example to .env.production and configure"
echo "  3. Run deployment script: ./scripts/deploy.sh production your-domain.com"
echo "  4. Set up monitoring (optional)"
echo ""
echo "🔒 Security reminders:"
echo "  - Change SSH port in /etc/ssh/sshd_config"
echo "  - Disable root login"
echo "  - Set up SSH key authentication"
echo "  - Regular system updates: apt-get update && apt-get upgrade"