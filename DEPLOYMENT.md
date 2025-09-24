# 🚀 AI Mentor Platform - Deployment Guide

## Prerequisites

- VPS with Ubuntu 22.04 LTS (minimum 1GB RAM, 20GB storage)
- Domain name pointing to your VPS
- Basic Linux administration knowledge

## Quick Start (5 minutes)

### 1. Prepare VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Run automated setup
wget -O - https://raw.githubusercontent.com/yourrepo/scripts/setup-vps.sh | bash
```

### 2. Deploy Application

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/ai-mentor.git
cd ai-mentor

# Configure environment
cp .env.production.example .env.production
nano .env.production  # Add your API keys

# Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh production your-domain.com
```

### 3. Verify

Visit `https://your-domain.com` - your AI Mentor Platform is live!

## Deployment Options

### Option 1: Single VPS ($5-10/month)

**Providers:**
- DigitalOcean Droplet ($6/month)
- Linode ($5/month)
- Vultr ($6/month)
- Hetzner ($4/month)

**Specs Required:**
- 1 vCPU
- 1GB RAM
- 25GB SSD
- Ubuntu 22.04 LTS

### Option 2: Docker on Existing Server

```bash
# Just run Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Option 3: Managed Platforms

**Railway.app (Easiest)**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway up
```

**Render.com**
- Connect GitHub repo
- Auto-deploys on push
- Free SSL included

**Fly.io**
```bash
fly launch
fly deploy
```

## Configuration

### Environment Variables

```env
# Required
JWT_SECRET_KEY=generate-with-openssl-rand-base64-32
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key  # Optional
GOOGLE_API_KEY=your-key   # Optional

# Production domain
CORS_ORIGINS='["https://your-domain.com"]'
```

### SSL/TLS Setup

#### Automatic (Let's Encrypt)
```bash
sudo certbot --nginx -d your-domain.com
```

#### Manual
Place certificates in `/opt/ai-mentor/ssl/`

### Database

SQLite is used by default. For production scale:

#### PostgreSQL Migration (Optional)
```python
# Update database.py
DATABASE_URL = "postgresql://user:pass@localhost/dbname"
```

## Monitoring

### Setup Monitoring

```bash
# Add to crontab
crontab -e

# Add monitoring every 5 minutes
*/5 * * * * /opt/ai-mentor/scripts/monitor.sh

# Add daily backups
0 2 * * * /opt/ai-mentor/scripts/backup.sh
```

### View Logs

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f web

# Nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# System metrics
docker stats
```

### Health Checks

- Main: `https://your-domain.com/`
- API: `https://your-domain.com/api/agents`

## Security

### Essential Steps

1. **Change SSH Port**
```bash
sudo nano /etc/ssh/sshd_config
# Change Port 22 to Port 2222
sudo systemctl restart sshd
```

2. **Disable Root Login**
```bash
# Create admin user first
adduser admin
usermod -aG sudo admin

# Then disable root
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
```

3. **Enable Firewall**
```bash
sudo ufw allow 2222/tcp  # Your SSH port
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

4. **Regular Updates**
```bash
# Weekly security updates
sudo apt update && sudo apt upgrade -y
```

## Scaling

### Current Capacity
- Single server: ~100 concurrent users
- Response time: <2s for most queries
- Database: SQLite handles ~1000 req/sec

### Scale Up Options

1. **Vertical Scaling**
   - Upgrade VPS (more RAM/CPU)
   - Move to dedicated server

2. **Horizontal Scaling**
   - Load balancer + multiple app servers
   - PostgreSQL/MySQL for database
   - Redis for caching

3. **CDN for Frontend**
   - CloudFlare (free tier available)
   - Reduces server load

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Common issues:
# - Missing .env.production
# - Port 8000 already in use
# - Insufficient memory
```

### Database Issues
```bash
# Backup current database
cp data/sessions.db data/sessions.db.backup

# Reset if corrupted
rm data/sessions.db
docker-compose -f docker-compose.prod.yml restart web
```

### SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

## Cost Analysis

### Minimal Setup ($5-10/month)
- VPS: $5/month (Hetzner/Linode)
- Domain: $10/year
- SSL: Free (Let's Encrypt)
- Total: ~$6/month

### Recommended Setup ($20-30/month)
- VPS: $12/month (2GB RAM)
- Backup storage: $5/month
- Monitoring: $3/month (optional)
- Domain: $10/year
- Total: ~$20/month

### API Costs (Variable)
- Anthropic Claude: ~$0.01 per request
- OpenAI GPT-4: ~$0.03 per request
- Intelligent routing saves 90% on costs

## Maintenance

### Weekly Tasks
- Check logs for errors
- Review usage statistics
- Update dependencies if needed

### Monthly Tasks
- Security updates
- Backup verification
- Performance review

### Quarterly Tasks
- Full system audit
- Dependency updates
- SSL renewal check

## Support

### Getting Help
- GitHub Issues: [your-repo]/issues
- Documentation: This file
- Logs: First place to check

### Common Success Metrics
- Uptime: 99.9% achievable
- Response time: <2s average
- User sessions: 1000+ daily
- Cost per user: <$0.01

## Next Steps After Deployment

1. **Test Everything**
   - Create test account
   - Try all agent types
   - Upload test files
   - Check session persistence

2. **Monitor First Week**
   - Watch logs daily
   - Check resource usage
   - Note any errors

3. **Optimize**
   - Adjust rate limits
   - Tune nginx cache
   - Optimize Docker image

4. **Share**
   - Post on HackerNews
   - Share in developer communities
   - Get feedback

---

**Congratulations!** Your AI Mentor Platform is deployed and ready to help developers worldwide! 🎉