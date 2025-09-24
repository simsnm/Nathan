# 🛡️ SAFE DEPLOYMENT PLAN FOR NATHANMSIMS.COM

## ⏰ Tonight's Timeline
- **6:00 PM** - Add safety code to repo
- **6:15 PM** - Push to GitHub  
- **6:30 PM** - Deploy to server
- **6:45 PM** - Test demo mode
- **7:00 PM** - nathanmsims.com is LIVE! 🎉

## 📋 Pre-Deployment Checklist
- [ ] GitHub repo public: ✅ github.com/simsnm/Nathan
- [ ] Server access ready
- [ ] 45-60 minutes available tonight
- [ ] Admin password ready for emergency controls

## 🔒 STEP 1: Add Cost Protection Files (Do First!)

### Create `demo_mode.py`
```python
# demo_mode.py - Safe demo responses (NO API CALLS)
DEMO_RESPONSES = {
    "hello": "👋 Hi! I'm Nathan, your AI development companion!",
    "help": "I can help with code review, debugging, learning, and more! This is demo mode - add API keys for full features.",
    "async": "Async/await allows non-blocking code execution. Think of it like ordering coffee - you don't stand at the counter, you wait for your name to be called!",
    "recursion": "Recursion is when a function calls itself. Like Russian dolls - each one contains a smaller version of itself!",
    "ctf": "I love CTF challenges! In demo mode, I can explain concepts. Add API keys for real challenge analysis.",
    "review": "In full mode, I review code for security, performance, and best practices. Demo mode shows what I can do!",
    "python": "Python is great for beginners and experts alike! Its clear syntax makes it perfect for learning programming concepts.",
    "security": "Security is crucial! Always validate inputs, use parameterized queries, and never trust user data!",
    "default": "I'm Nathan! I'm in demo mode right now. Visit github.com/simsnm/Nathan for setup instructions."
}

def get_demo_response(message: str, role: str = "mentor"):
    """Return demo response without any API calls"""
    message_lower = message.lower()
    
    # Check for keywords
    for key in DEMO_RESPONSES:
        if key in message_lower:
            return {
                "response": DEMO_RESPONSES[key],
                "agent_used": f"Demo Nathan ({role})",
                "model_used": "demo",
                "estimated_cost": 0.0
            }
    
    return {
        "response": DEMO_RESPONSES["default"],
        "agent_used": "Demo Nathan",
        "model_used": "demo",
        "estimated_cost": 0.0
    }
```

### Create `rate_limiter.py`
```python
# rate_limiter.py - Protect against abuse
from datetime import datetime, timedelta
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.daily_cost = 0.0
        self.daily_requests = 0
        
        # STRICT LIMITS FOR SAFETY
        self.MAX_REQUESTS_PER_IP_HOUR = 5
        self.MAX_REQUESTS_PER_IP_DAY = 20
        self.MAX_DAILY_COST = 1.00  # $1 max per day
        self.MAX_DAILY_REQUESTS = 100  # Total across all users
        
    def check_limits(self, client_ip: str) -> tuple[bool, str]:
        """Check if request is allowed"""
        now = datetime.now()
        
        # Check daily totals
        if self.daily_cost >= self.MAX_DAILY_COST:
            logger.warning(f"Daily cost limit hit: ${self.daily_cost}")
            return False, "Daily cost limit reached. Nathan needs rest!"
        
        if self.daily_requests >= self.MAX_DAILY_REQUESTS:
            logger.warning(f"Daily request limit hit: {self.daily_requests}")
            return False, "Daily request limit reached. Try tomorrow!"
        
        # Check IP limits
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Clean old requests
        self.requests[client_ip] = [
            req for req in self.requests[client_ip] 
            if req > day_ago
        ]
        
        # Count recent requests
        hourly = sum(1 for req in self.requests[client_ip] if req > hour_ago)
        daily = len(self.requests[client_ip])
        
        if hourly >= self.MAX_REQUESTS_PER_IP_HOUR:
            return False, f"Too many requests (limit: {self.MAX_REQUESTS_PER_IP_HOUR}/hour). Try again later!"
        
        if daily >= self.MAX_REQUESTS_PER_IP_DAY:
            return False, f"Daily limit reached (limit: {self.MAX_REQUESTS_PER_IP_DAY}/day). Try tomorrow!"
        
        # Request allowed
        self.requests[client_ip].append(now)
        self.daily_requests += 1
        
        return True, "OK"
    
    def add_cost(self, cost: float):
        """Track costs"""
        self.daily_cost += cost
        logger.info(f"Cost added: ${cost:.4f}, Daily total: ${self.daily_cost:.4f}")
        
    def reset_daily(self):
        """Reset daily counters (call via cron)"""
        logger.info(f"Daily reset - Requests: {self.daily_requests}, Cost: ${self.daily_cost:.4f}")
        self.daily_cost = 0.0
        self.daily_requests = 0
        self.requests.clear()

# Global instance
rate_limiter = RateLimiter()
```

## 🔧 STEP 2: Update main.py with Safety Features

Add these imports and changes to `web_app/main.py`:

```python
# Add at top of file
import os
from demo_mode import get_demo_response
from rate_limiter import rate_limiter

# SAFETY FIRST - Default to demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ENABLE_API_CALLS = os.getenv("ENABLE_API_CALLS", "false").lower() == "true"

# Admin password for emergency controls
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-" + os.urandom(8).hex())

# Helper to get client IP
def get_client_ip(request: Request) -> str:
    return request.client.host

# Update the chat endpoint
@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest, 
    req: Request,
    user: Dict = Depends(get_current_user_optional)
):
    client_ip = get_client_ip(req)
    
    # Rate limiting
    allowed, message = rate_limiter.check_limits(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    # DEMO MODE - Safe, no API calls
    if DEMO_MODE or not ENABLE_API_CALLS:
        logger.info(f"Demo response for IP: {client_ip}")
        return get_demo_response(request.message, request.role)
    
    # Only call real APIs if explicitly enabled
    try:
        result = await run_codechat_logic(request)
        rate_limiter.add_cost(result.estimated_cost)
        
        # Emergency warning if costs spike
        if rate_limiter.daily_cost > 0.80:  # 80% of limit
            logger.warning(f"⚠️ COST WARNING: ${rate_limiter.daily_cost:.2f} of $1.00 daily limit")
            
        return result
        
    except Exception as e:
        logger.error(f"API call failed: {e}")
        # Fallback to demo mode on error
        return get_demo_response(request.message, request.role)

# Add status endpoint
@app.get("/api/status")
async def get_status():
    """Public status endpoint"""
    return {
        "status": "online",
        "mode": "demo" if DEMO_MODE else "full",
        "message": "Nathan is ready to help!",
        "daily_requests": rate_limiter.daily_requests,
        "limits": {
            "requests_per_hour": rate_limiter.MAX_REQUESTS_PER_IP_HOUR,
            "requests_per_day": rate_limiter.MAX_REQUESTS_PER_IP_DAY
        },
        "github": "https://github.com/simsnm/Nathan"
    }

# Emergency controls
@app.post("/api/admin/shutdown")
async def emergency_shutdown(password: str):
    """Emergency kill switch for API calls"""
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    global ENABLE_API_CALLS
    ENABLE_API_CALLS = False
    logger.critical("EMERGENCY SHUTDOWN - API calls disabled")
    return {"status": "APIs disabled", "mode": "demo"}

@app.get("/api/admin/costs")
async def get_costs(password: str):
    """Check current costs (admin only)"""
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "daily_cost": f"${rate_limiter.daily_cost:.4f}",
        "daily_requests": rate_limiter.daily_requests,
        "daily_limit": f"${rate_limiter.MAX_DAILY_COST:.2f}",
        "percentage_used": f"{(rate_limiter.daily_cost / rate_limiter.MAX_DAILY_COST * 100):.1f}%",
        "status": "🟢 Safe" if rate_limiter.daily_cost < 0.80 else "🔴 Warning"
    }
```

## 🚀 STEP 3: Deployment Commands (Run Tonight)

### 3.1 Push Safety Code to GitHub
```bash
cd ~/Projects/llm\ manager
git add demo_mode.py rate_limiter.py
git add web_app/main.py
git commit -m "Add safety features: demo mode and rate limiting"
git push origin main
```

### 3.2 Server Deployment
```bash
# SSH to your server
ssh user@your-server

# Clone Nathan
git clone https://github.com/simsnm/Nathan.git
cd Nathan

# Create SAFE production config
cat > .env.production << 'EOF'
# SAFETY FIRST - Demo mode only!
DEMO_MODE=true
ENABLE_API_CALLS=false

# Admin password (CHANGE THIS!)
ADMIN_PASSWORD=your-secret-admin-password-here

# If you enable APIs later (keep false for now!)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx

# Safety limits
MAX_DAILY_COST=1.00
MAX_REQUESTS_PER_IP=10

# Database
DATABASE_PATH=/var/nathan/sessions.db

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["https://nathanmsims.com","http://localhost:8000"]

# Server
HOST=0.0.0.0
PORT=8000
EOF

# Create data directory
sudo mkdir -p /var/nathan
sudo chown $USER:$USER /var/nathan

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Nathan (test first)
python web_app/main.py

# For production, use systemd service (see below)
```

### 3.3 Create Systemd Service
```bash
sudo cat > /etc/systemd/system/nathan.service << 'EOF'
[Unit]
Description=Nathan AI Assistant
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/Nathan
Environment="PATH=/home/your-username/Nathan/venv/bin"
ExecStart=/home/your-username/Nathan/venv/bin/python web_app/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nathan
sudo systemctl start nathan
sudo systemctl status nathan
```

### 3.4 Nginx Configuration
```bash
sudo cat > /etc/nginx/sites-available/nathan << 'EOF'
server {
    server_name nathanmsims.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/nathan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d nathanmsims.com
```

## ✅ STEP 4: Verify Everything Works

### Test Commands
```bash
# Check status
curl https://nathanmsims.com/api/status

# Test demo mode
curl -X POST https://nathanmsims.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Nathan!", "role": "mentor"}'

# Test rate limiting (should block after 5)
for i in {1..10}; do
  echo "Request $i:"
  curl -X POST https://nathanmsims.com/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "test", "role": "mentor"}'
  echo ""
done

# Check admin costs (use your admin password)
curl "https://nathanmsims.com/api/admin/costs?password=your-admin-password"
```

## 🎯 Success Criteria

By 7:00 PM tonight:
- ✅ nathanmsims.com responds with demo Nathan
- ✅ Rate limiting prevents abuse (5 req/hour per IP)
- ✅ Demo mode active (ZERO API costs)
- ✅ Admin endpoints work for monitoring
- ✅ SSL certificate active (https works)

## 🚨 Emergency Procedures

### If Something Goes Wrong
```bash
# View logs
sudo journalctl -u nathan -f

# Restart service
sudo systemctl restart nathan

# Emergency shutdown
curl -X POST https://nathanmsims.com/api/admin/shutdown \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}'

# Check costs
curl "https://nathanmsims.com/api/admin/costs?password=your-admin-password"
```

## 📊 Post-Launch Monitoring

### Watch for:
1. Traffic levels (how many people try Nathan?)
2. Rate limit hits (are limits appropriate?)
3. Error logs (any crashes?)
4. Demo responses (are they helpful?)

### Tomorrow's Tasks:
1. Check logs for first users
2. Adjust rate limits if needed
3. Add more demo responses based on queries
4. Share on social media if stable

## 💰 Cost Safety Summary

With this setup:
- **Demo Mode**: $0 (no API calls)
- **If APIs enabled**: Max $1/day (hard limit)
- **Rate limiting**: Max 100 requests/day total
- **Per user**: Max 20 requests/day
- **Emergency shutdown**: One command to stop everything

## 🎉 You're Ready!

This plan ensures:
- **ZERO risk** of unexpected costs
- **Professional deployment** 
- **Real user experience** with demo mode
- **Full monitoring** capabilities
- **Emergency controls** if needed

**nathanmsims.com will be live and safe tonight!** 🚀

---
*Save this file and follow it step-by-step tonight. Good luck!*