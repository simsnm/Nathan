"""Pydantic models for request/response schemas"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class ChatRequest(BaseModel):
    message: str
    role: Optional[str] = "coder"
    files: Optional[List[str]] = []
    auto_model: bool = True
    context_session: Optional[str] = None
    provider: Optional[str] = "claude"
    ctf_mode: bool = False
    hint_mode: bool = False
    collaborative: bool = False

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    model_used: str
    estimated_cost: float
    session_id: str
    success: bool = True
    error: Optional[str] = None

class AgentInfo(BaseModel):
    name: str
    description: str
    category: str

class AgentListResponse(BaseModel):
    agents: List[AgentInfo]
    total: int

class SessionResponse(BaseModel):
    session_id: str
    messages: List[dict]
    total_cost: float
    agent_usage: dict

class UploadResponse(BaseModel):
    filename: str
    file_path: str
    size: int
    success: bool
    error: Optional[str] = None

class WorkflowRequest(BaseModel):
    workflow_yaml: str
    session_id: Optional[str] = None

class WorkflowResponse(BaseModel):
    workflow_name: str
    steps_completed: int
    outputs: List[str]
    session_id: str
    total_cost: float
    success: bool
    error: Optional[str] = None

# User System Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    created_at: datetime = Field(default_factory=datetime.now)
    skill_levels: Dict[str, int] = Field(default_factory=dict)  # {"python": 3, "security": 2}
    total_questions: int = 0
    total_cost: float = 0.0
    subscription_tier: str = "free"  # free, pro

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation: List[Dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_cost: float = 0.0
    title: Optional[str] = None

# Auth Models
class LoginRequest(BaseModel):
    email: str

class LoginResponse(BaseModel):
    token: str
    user: Dict
    success: bool = True

class UserResponse(BaseModel):
    user_id: str
    email: str
    total_questions: int
    total_cost: float
    subscription_tier: str

class SessionListResponse(BaseModel):
    sessions: List[Dict]
    total: int

class SessionDetailResponse(BaseModel):
    id: str
    conversation: List[Dict]
    total_cost: float
    created_at: datetime
    title: Optional[str] = None