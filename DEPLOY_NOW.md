# 🚀 Nathan Deployment Quick Guide

## Ready to Deploy nathanmsims.com?

### Quick Deploy (5 minutes)

1. **SSH to your server**:
```bash
ssh your-username@your-server-ip
```

2. **Run these commands**:
```bash
# Install prerequisites
sudo apt update
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Clone and deploy
git clone https://github.com/simsnm/Nathan.git
cd Nathan
chmod +x scripts/deploy_nathanmsims.sh
./scripts/deploy_nathanmsims.sh
```

3. **Save the admin password** shown at completion

### That's it! Nathan is live at https://nathanmsims.com

## Test Your Deployment

```bash
# Check it's working
curl https://nathanmsims.com/api/status

# Try a chat
curl -X POST https://nathanmsims.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Nathan!", "role": "mentor"}'
```

## Monitor

```bash
# View logs
sudo journalctl -u nathan -f

# Check status
/var/www/nathan/monitor.sh
```

---
Nathan is SAFE with demo mode - zero API costs! 🎉