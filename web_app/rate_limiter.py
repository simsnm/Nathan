"""Rate limiting and cost protection for Nathan - Safety first!"""

from datetime import datetime, timedelta
from collections import defaultdict
import json
import os

class RateLimiter:
    """Protect against abuse and control costs"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.daily_cost = 0.0
        self.daily_requests = 0
        self.last_reset = datetime.now()
        
        # STRICT LIMITS FOR SAFETY - Configurable via environment
        self.MAX_REQUESTS_PER_IP_HOUR = int(os.getenv("MAX_REQUESTS_PER_IP_HOUR", "10"))
        self.MAX_REQUESTS_PER_IP_DAY = int(os.getenv("MAX_REQUESTS_PER_IP_DAY", "50"))
        self.MAX_DAILY_COST = float(os.getenv("MAX_DAILY_COST", "1.00"))  # $1 max per day default
        self.MAX_DAILY_REQUESTS = int(os.getenv("MAX_DAILY_REQUESTS", "200"))  # Total across all users
        
        # Load saved state if exists
        self.load_state()
    
    def check_limits(self, client_ip: str) -> tuple[bool, str]:
        """Check if request is allowed"""
        now = datetime.now()
        
        # Reset daily counters if new day
        if (now - self.last_reset).days >= 1:
            self.reset_daily()
        
        # Check daily totals
        if self.daily_cost >= self.MAX_DAILY_COST:
            return False, f"Daily cost limit reached (${self.MAX_DAILY_COST}). Nathan needs rest! Try tomorrow."
        
        if self.daily_requests >= self.MAX_DAILY_REQUESTS:
            return False, f"Daily request limit reached ({self.MAX_DAILY_REQUESTS}). Try tomorrow!"
        
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
            return False, f"Too many requests ({hourly}/{self.MAX_REQUESTS_PER_IP_HOUR} per hour). Try again later!"
        
        if daily >= self.MAX_REQUESTS_PER_IP_DAY:
            return False, f"Daily limit reached ({daily}/{self.MAX_REQUESTS_PER_IP_DAY} per day). Try again tomorrow!"
        
        # Request allowed
        self.requests[client_ip].append(now)
        self.daily_requests += 1
        self.save_state()
        
        return True, "OK"
    
    def add_cost(self, cost: float):
        """Track costs"""
        self.daily_cost += cost
        self.save_state()
        
        # Emergency warning
        if self.daily_cost > (self.MAX_DAILY_COST * 0.8):
            print(f"⚠️ COST WARNING: ${self.daily_cost:.2f} of ${self.MAX_DAILY_COST} limit used!")
    
    def reset_daily(self):
        """Reset daily counters"""
        self.daily_cost = 0.0
        self.daily_requests = 0
        self.last_reset = datetime.now()
        self.requests.clear()
        self.save_state()
        print(f"✅ Daily limits reset at {self.last_reset}")
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            "daily_cost": round(self.daily_cost, 3),
            "daily_cost_limit": self.MAX_DAILY_COST,
            "daily_requests": self.daily_requests,
            "daily_requests_limit": self.MAX_DAILY_REQUESTS,
            "cost_remaining": round(self.MAX_DAILY_COST - self.daily_cost, 3),
            "requests_remaining": self.MAX_DAILY_REQUESTS - self.daily_requests,
            "last_reset": self.last_reset.isoformat(),
            "limits": {
                "per_hour": self.MAX_REQUESTS_PER_IP_HOUR,
                "per_day": self.MAX_REQUESTS_PER_IP_DAY,
                "daily_cost": self.MAX_DAILY_COST,
                "total_requests": self.MAX_DAILY_REQUESTS
            }
        }
    
    def save_state(self):
        """Save state to file for persistence across restarts"""
        state_file = "/tmp/nathan_rate_limiter_state.json"
        try:
            state = {
                "daily_cost": self.daily_cost,
                "daily_requests": self.daily_requests,
                "last_reset": self.last_reset.isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Warning: Could not save rate limiter state: {e}")
    
    def load_state(self):
        """Load saved state"""
        state_file = "/tmp/nathan_rate_limiter_state.json"
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.daily_cost = state.get("daily_cost", 0.0)
                    self.daily_requests = state.get("daily_requests", 0)
                    self.last_reset = datetime.fromisoformat(state.get("last_reset", datetime.now().isoformat()))
                    
                    # Reset if it's a new day
                    if (datetime.now() - self.last_reset).days >= 1:
                        self.reset_daily()
        except Exception as e:
            print(f"Warning: Could not load rate limiter state: {e}")

# Global rate limiter instance
rate_limiter = RateLimiter()