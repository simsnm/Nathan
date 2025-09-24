"""Simple email-based authentication with JWT tokens"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_user_by_email, get_user_by_id, create_user

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 1 week

security = HTTPBearer(auto_error=False)

def create_access_token(data: Dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict:
    """Verify JWT token and return user data"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify user still exists
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"user_id": user_id, "email": email}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """Get current user if authenticated, None otherwise (for optional auth)"""
    if not credentials:
        return None
    
    try:
        return verify_token(credentials)
    except HTTPException:
        return None

def authenticate_user(email: str) -> Dict:
    """Simple email-only authentication - creates user if doesn't exist"""
    # Basic email validation
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    # Get or create user
    user = get_user_by_email(email)
    if not user:
        user_id = create_user(email)
        user = get_user_by_id(user_id)
    
    # Create token
    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "total_questions": user["total_questions"],
            "total_cost": user["total_cost"],
            "subscription_tier": user["subscription_tier"],
            "created_at": user["created_at"]
        }
    }