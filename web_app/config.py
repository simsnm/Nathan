"""Configuration management with persistent secrets"""
import os
import secrets
import json
from pathlib import Path
from typing import Optional

class Config:
    """Configuration with persistent JWT secret"""
    
    def __init__(self):
        self.config_dir = Path(os.getenv("CONFIG_DIR", "/var/nathan/config"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_file = self.config_dir / "secrets.json"
        
        # Load or generate secrets
        self._load_or_generate_secrets()
        
        # Environment configuration
        self.DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
        self.ENABLE_API_CALLS = os.getenv("ENABLE_API_CALLS", "false").lower() == "true"
        
        # API Keys
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        
        # Database
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/sessions.db")
        self.RATE_LIMIT_DB = os.getenv("RATE_LIMIT_DB", "/var/nathan/rate_limits.db")
        
        # Rate limiting
        self.MAX_REQUESTS_PER_IP_HOUR = int(os.getenv("MAX_REQUESTS_PER_IP_HOUR", "10"))
        self.MAX_REQUESTS_PER_IP_DAY = int(os.getenv("MAX_REQUESTS_PER_IP_DAY", "50"))
        self.MAX_DAILY_COST = float(os.getenv("MAX_DAILY_COST", "1.00"))
        self.MAX_DAILY_REQUESTS = int(os.getenv("MAX_DAILY_REQUESTS", "200"))
        
        # CORS
        cors_str = os.getenv('CORS_ORIGINS', '["http://localhost:3000", "http://localhost:8000"]')
        try:
            self.CORS_ORIGINS = json.loads(cors_str)
        except:
            self.CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
    
    def _load_or_generate_secrets(self):
        """Load existing secrets or generate new ones"""
        if self.secrets_file.exists():
            # Load existing secrets
            try:
                with open(self.secrets_file, 'r') as f:
                    secrets_data = json.load(f)
                    self.JWT_SECRET_KEY = secrets_data.get('jwt_secret')
                    self.ADMIN_PASSWORD = secrets_data.get('admin_password')
                    print("✅ Loaded existing secrets")
            except Exception as e:
                print(f"⚠️ Failed to load secrets: {e}")
                self._generate_new_secrets()
        else:
            # Generate new secrets
            self._generate_new_secrets()
    
    def _generate_new_secrets(self):
        """Generate and persist new secrets"""
        self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(16)
        
        # Save to file
        secrets_data = {
            'jwt_secret': self.JWT_SECRET_KEY,
            'admin_password': self.ADMIN_PASSWORD
        }
        
        try:
            # Create file with restricted permissions
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets_data, f, indent=2)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.secrets_file, 0o600)
            
            print(f"✅ Generated new secrets")
            print(f"📝 Admin password: {self.ADMIN_PASSWORD}")
            print(f"   Save this password! It won't be shown again.")
        except Exception as e:
            print(f"⚠️ Failed to save secrets: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        key_map = {
            'anthropic': self.ANTHROPIC_API_KEY,
            'claude': self.ANTHROPIC_API_KEY,
            'openai': self.OPENAI_API_KEY,
            'google': self.GOOGLE_API_KEY
        }
        return key_map.get(provider.lower())
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEMO_MODE and self.ENABLE_API_CALLS
    
    def get_status(self) -> dict:
        """Get configuration status"""
        return {
            "mode": "demo" if self.DEMO_MODE else "full",
            "api_calls_enabled": self.ENABLE_API_CALLS,
            "has_anthropic_key": bool(self.ANTHROPIC_API_KEY),
            "has_openai_key": bool(self.OPENAI_API_KEY),
            "has_google_key": bool(self.GOOGLE_API_KEY),
            "rate_limits": {
                "per_ip_hour": self.MAX_REQUESTS_PER_IP_HOUR,
                "per_ip_day": self.MAX_REQUESTS_PER_IP_DAY,
                "daily_cost": self.MAX_DAILY_COST
            }
        }

# Global config instance
config = Config()