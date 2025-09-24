"""FastAPI wrapper around the proven codechat CLI functionality"""
import sys
import os
import tempfile
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import codechat
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (ChatRequest, ChatResponse, AgentListResponse, AgentInfo, SessionResponse, 
                    UploadResponse, WorkflowRequest, WorkflowResponse, LoginRequest, LoginResponse,
                    UserResponse, SessionListResponse, SessionDetailResponse)

# Import our proven CLI functionality
try:
    from codechat import AGENT_ROLES, chat_about_code, get_provider, COST_TRACKER
    import workflow  # Import workflow runner
    from auth import authenticate_user, verify_token, get_current_user_optional
    from database import (init_db, create_session, get_user_sessions, get_session, 
                         add_to_conversation, update_user_stats)
    from demo_mode import is_demo_mode, get_demo_provider, DEMO_RESPONSES
    from rate_limiter_persistent import rate_limiter
    from config import config
    print("✅ Successfully imported codechat functionality")
except ImportError as e:
    print(f"❌ Failed to import codechat: {e}")
    sys.exit(1)

# Environment configuration with validation
def get_api_key(provider: str) -> Optional[str]:
    """Get API key for specified provider with fallback"""
    key_map = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'google': 'GOOGLE_API_KEY'
    }
    
    env_key = key_map.get(provider.lower())
    if env_key:
        return os.getenv(env_key)
    return None

def validate_environment():
    """Validate that at least one API key is available"""
    keys = {
        'Anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Google': os.getenv('GOOGLE_API_KEY')
    }
    
    available_keys = [name for name, key in keys.items() if key and key.strip()]
    
    if not available_keys:
        print("⚠️  WARNING: No API keys found in environment!")
        print("   Copy .env.example to .env and add your API keys")
        print("   Available providers will be limited to local models only")
        return False
    else:
        print(f"✅ API keys found for: {', '.join(available_keys)}")
        return True

# Validate environment on startup
validate_environment()

# Initialize database
init_db()

# SAFETY CONFIGURATION - Use centralized config
DEMO_MODE = config.DEMO_MODE
ENABLE_API_CALLS = config.ENABLE_API_CALLS

print(f"🛡️ Safety Mode: DEMO_MODE={DEMO_MODE}, ENABLE_API_CALLS={ENABLE_API_CALLS}")
if DEMO_MODE:
    print("✅ Running in DEMO MODE - No API costs!")
elif ENABLE_API_CALLS:
    print("⚠️ API calls ENABLED - Costs will be incurred!")
else:
    print("✅ Safe mode - API calls disabled")

# Get CORS origins from config
cors_origins = config.CORS_ORIGINS

app = FastAPI(
    title="CodeChat API",
    description="HTTP API wrapper around the comprehensive CTF learning mentor and AI-powered development assistant",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Simple in-memory session storage (Phase 1)
sessions = {}
uploaded_files = {}

def get_session_dir() -> str:
    """Get or create session directory"""
    session_dir = os.path.join(tempfile.gettempdir(), "codechat_sessions")
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

def get_client_ip(request: Request) -> str:
    """Get client IP address (handles proxy headers)"""
    # Check for proxy headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "127.0.0.1"

@app.get("/")
async def root():
    return {"message": "Nathan - AI Development Companion", "version": "1.0.0", "mode": "demo" if DEMO_MODE else "full"}

@app.get("/api/status")
async def get_status():
    """Public status endpoint for monitoring"""
    status = rate_limiter.get_status()
    return {
        "status": "online",
        "mode": "demo" if DEMO_MODE else "full",
        "api_calls_enabled": ENABLE_API_CALLS,
        "rate_limits": status,
        "message": "Nathan is ready to help!" if status["requests_remaining"] > 0 else "Nathan is resting. Try again tomorrow!"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        from database import get_user_by_id
        # Try a simple query
        test_query = get_user_by_id(1) if os.path.exists(os.getenv("DATABASE_PATH", "./data/sessions.db")) else None
        
        # Check rate limiter
        if not hasattr(rate_limiter, 'check_limits'):
            raise Exception("Rate limiter not initialized")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "mode": "demo" if DEMO_MODE else "full"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
        )

@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring"""
    return {
        "timestamp": datetime.now().isoformat(),
        "requests": {
            "total_daily": rate_limiter.daily_requests,
            "requests_per_ip": len(rate_limiter.requests)
        },
        "costs": {
            "daily_total": rate_limiter.daily_cost,
            "daily_limit": rate_limiter.MAX_DAILY_COST,
            "percentage_used": round((rate_limiter.daily_cost / rate_limiter.MAX_DAILY_COST * 100), 2) if rate_limiter.MAX_DAILY_COST > 0 else 0
        },
        "mode": "demo" if DEMO_MODE else "full"
    }

@app.get("/api/agents", response_model=AgentListResponse)
async def list_agents():
    """List all available agent roles"""
    agents = []
    
    # Categorize agents
    categories = {
        "Development": ["architect", "coder", "reviewer", "tester", "documenter", "optimizer"],
        "Learning": ["mentor", "tutor", "clarifier"],
        "Research": ["researcher"],
        "CTF/Security": ["reverse-engineer", "crypto-analyst", "web-hacker", "forensics-expert", "exploit-dev"]
    }
    
    for category, agent_names in categories.items():
        for agent_name in agent_names:
            if agent_name in AGENT_ROLES:
                agents.append(AgentInfo(
                    name=agent_name,
                    description=AGENT_ROLES[agent_name]["description"],
                    category=category
                ))
    
    return AgentListResponse(agents=agents, total=len(agents))

# Authentication Endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple email-only login - creates user if doesn't exist"""
    try:
        result = authenticate_user(request.email)
        return LoginResponse(
            token=result["token"],
            user=result["user"],
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(user: dict = Depends(verify_token)):
    """Get current user info"""
    from database import get_user_by_id
    db_user = get_user_by_id(user["user_id"])
    
    return UserResponse(
        user_id=db_user["id"],
        email=db_user["email"],
        total_questions=db_user["total_questions"],
        total_cost=db_user["total_cost"],
        subscription_tier=db_user["subscription_tier"]
    )

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads for analysis"""
    try:
        # Create unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(get_session_dir(), safe_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Store file info
        uploaded_files[file_id] = {
            "original_name": file.filename,
            "file_path": file_path,
            "size": len(content)
        }
        
        return UploadResponse(
            filename=file.filename,
            file_path=file_id,  # Return file_id for privacy
            size=len(content),
            success=True
        )
        
    except Exception as e:
        return UploadResponse(
            filename=file.filename,
            file_path="",
            size=0,
            success=False,
            error=str(e)
        )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    req: Request,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """Main chat endpoint - mirrors CLI functionality exactly"""
    
    # Get client IP for rate limiting
    client_ip = get_client_ip(req)
    
    # Check rate limits
    allowed, limit_message = rate_limiter.check_limits(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=limit_message)
    
    try:
        # Generate session ID if not provided
        session_id = request.context_session or str(uuid.uuid4())
        
        # Handle file references
        file_content = None
        file_paths = []
        
        if request.files:
            for file_ref in request.files:
                if file_ref in uploaded_files:
                    file_info = uploaded_files[file_ref]
                    file_paths.append(file_info["file_path"])
        
        # Read file content if files provided
        if file_paths:
            combined_content = ""
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        filename = os.path.basename(file_path)
                        combined_content += f"\n=== {filename} ===\n{content}\n"
                except Exception as e:
                    combined_content += f"\n=== {os.path.basename(file_path)} (Error) ===\nCould not read file: {e}\n"
            file_content = combined_content
        
        # Get provider with environment-based API key
        api_key = get_api_key(request.provider)
        if not api_key:
            # Try to fallback to any available key
            for provider_name in ['anthropic', 'openai', 'google']:
                fallback_key = get_api_key(provider_name)
                if fallback_key:
                    api_key = fallback_key
                    request.provider = provider_name
                    break
            
            if not api_key or DEMO_MODE or not ENABLE_API_CALLS:
                # Use demo mode when: no API keys, DEMO_MODE is on, or API calls disabled
                demo_provider = get_demo_provider()
                demo_response = DEMO_RESPONSES.get(request.role or "mentor", DEMO_RESPONSES["mentor"])
                estimated_cost = 0.0
                
                print(f"📝 Demo response for: {client_ip} - Role: {request.role}")
                
                # Handle user session persistence even in testing
                if user:
                    if not request.context_session:
                        session_id = create_session(
                            user["user_id"],
                            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
                        )
                    else:
                        session_id = request.context_session
                    
                    add_to_conversation(session_id, request.message, mock_response, estimated_cost)
                    update_user_stats(user["user_id"], estimated_cost)
                else:
                    sessions[session_id] = {
                        "messages": [{"role": "user", "content": request.message}, {"role": "assistant", "content": mock_response}],
                        "total_cost": estimated_cost,
                        "agent_used": request.role
                    }
                
                return ChatResponse(
                    response=demo_response,
                    agent_used=request.role or "coder",
                    model_used="demo-mode",
                    estimated_cost=estimated_cost,
                    session_id=session_id,
                    success=True
                )
        
        # Only get provider if we have a valid API key
        provider = get_provider(request.provider, api_key)
        
        # Use the proven CLI chat function
        response_text, messages = chat_about_code(
            provider=provider,
            question=request.message,
            code_content=file_content,
            filepath=file_paths[0] if file_paths else None,
            messages=None,  # TODO: Session persistence
            role=request.role
        )
        
        # Track cost (reuse CLI logic)
        estimated_cost = COST_TRACKER.get("total_cost", 0.0)
        
        # Add cost to rate limiter for tracking
        rate_limiter.add_cost(estimated_cost)
        
        # Log the API call
        print(f"💰 API call from {client_ip}: ${estimated_cost:.4f} - Role: {request.role}")
        
        # Handle user session persistence
        if user:
            # Use database for authenticated users
            if not request.context_session:
                # Create new session for user
                session_id = create_session(
                    user["user_id"],
                    title=request.message[:50] + "..." if len(request.message) > 50 else request.message
                )
            else:
                session_id = request.context_session
            
            # Save conversation turn
            add_to_conversation(session_id, request.message, response_text, estimated_cost)
            
            # Update user statistics
            update_user_stats(user["user_id"], estimated_cost)
        else:
            # Store in memory for anonymous users (backward compatibility)
            sessions[session_id] = {
                "messages": messages or [],
                "total_cost": estimated_cost,
                "agent_used": request.role
            }
        
        return ChatResponse(
            response=response_text,
            agent_used=request.role or "coder",
            model_used=provider.model if hasattr(provider, 'model') else "unknown",
            estimated_cost=estimated_cost,
            session_id=session_id,
            success=True
        )
        
    except Exception as e:
        return ChatResponse(
            response="",
            agent_used=request.role or "coder", 
            model_used="unknown",
            estimated_cost=0.0,
            session_id=request.context_session or str(uuid.uuid4()),
            success=False,
            error=str(e)
        )

# Session Management Endpoints  
@app.get("/api/sessions", response_model=SessionListResponse)
async def get_user_sessions_endpoint(user: dict = Depends(verify_token)):
    """Get user's conversation history"""
    sessions_list = get_user_sessions(user["user_id"])
    return SessionListResponse(sessions=sessions_list, total=len(sessions_list))

@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: str, user: dict = Depends(verify_token)):
    """Get specific conversation"""
    session = get_session(session_id, user["user_id"])
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionDetailResponse(
        id=session["id"],
        conversation=session["conversation"],
        total_cost=session["total_cost"],
        created_at=session["created_at"],
        title=session.get("title")
    )

# Backward compatibility endpoint for anonymous users
@app.get("/api/session/{session_id}", response_model=SessionResponse)
async def get_anonymous_session(session_id: str):
    """Get conversation history for anonymous session (backward compatibility)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return SessionResponse(
        session_id=session_id,
        messages=session["messages"],
        total_cost=session["total_cost"],
        agent_usage={session["agent_used"]: 1}
    )

@app.post("/api/workflow", response_model=WorkflowResponse)
async def workflow_endpoint(request: WorkflowRequest):
    """Execute a workflow.yaml file"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Save workflow to temp file
        workflow_file = os.path.join(get_session_dir(), f"{session_id}_workflow.yaml")
        with open(workflow_file, 'w') as f:
            f.write(request.workflow_yaml)
        
        # Execute workflow using CLI logic
        # Note: This is a simplified version - full workflow execution would need more integration
        import yaml
        workflow_data = yaml.safe_load(request.workflow_yaml)
        workflow_name = workflow_data.get("name", "Unnamed Workflow")
        
        # For Phase 1, just validate and return success
        # Full implementation would use workflow.py run_workflow()
        outputs = ["Workflow validation successful", "Ready for execution in full implementation"]
        
        return WorkflowResponse(
            workflow_name=workflow_name,
            steps_completed=0,  # Phase 1 - just validation
            outputs=outputs,
            session_id=session_id,
            total_cost=0.0,
            success=True
        )
        
    except Exception as e:
        return WorkflowResponse(
            workflow_name="Unknown",
            steps_completed=0,
            outputs=[],
            session_id=request.session_id or str(uuid.uuid4()),
            total_cost=0.0,
            success=False,
            error=str(e)
        )

# Admin endpoints with proper security
class AdminRequest(BaseModel):
    admin_token: str

class AdminShutdownRequest(AdminRequest):
    confirm: bool = False

@app.post("/api/admin/costs")
async def get_admin_costs(request: AdminRequest):
    """Check current costs (admin only) - POST for security"""
    if request.admin_token != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "daily_cost": f"${rate_limiter.daily_cost:.4f}",
        "daily_requests": rate_limiter.daily_requests,
        "daily_limit": f"${rate_limiter.MAX_DAILY_COST:.2f}",
        "percentage_used": f"{(rate_limiter.daily_cost / rate_limiter.MAX_DAILY_COST * 100):.1f}%",
        "status": "🟢 Safe" if rate_limiter.daily_cost < 0.80 else "🔴 Warning"
    }

@app.post("/api/admin/shutdown")
async def emergency_shutdown(request: AdminShutdownRequest):
    """Emergency kill switch for API calls"""
    if request.admin_token != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Must confirm shutdown")
    
    global ENABLE_API_CALLS
    ENABLE_API_CALLS = False
    print("🚨 EMERGENCY SHUTDOWN - API calls disabled")
    
    return {"status": "APIs disabled", "mode": "demo", "timestamp": datetime.now().isoformat()}

@app.post("/api/admin/reset-limits")
async def reset_rate_limits(request: AdminRequest):
    """Reset rate limits (admin only)"""
    if request.admin_token != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    rate_limiter.reset_daily()
    return {"status": "Rate limits reset", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)