# CodeChat API - Phase 1

HTTP API wrapper around the comprehensive CTF learning mentor and AI-powered development assistant.

## What's Working

✅ **Core Functionality (307 lines)**
- FastAPI server with proven CLI integration
- File upload and processing
- All 15 agent roles (including CTF specialists)
- Session management
- Workflow validation
- Error handling

## API Endpoints

### Chat
```bash
POST /api/chat
{
  "message": "Review this code for security issues",
  "role": "reviewer", 
  "files": ["file_id_from_upload"],
  "auto_model": true,
  "ctf_mode": false
}
```

### File Upload  
```bash
POST /api/upload
# Multipart form data with file
```

### Agents
```bash
GET /api/agents
# Returns all 15 available agents with categories
```

### Sessions
```bash
GET /api/session/{session_id}
# Returns conversation history and costs
```

### Workflows
```bash
POST /api/workflow
{
  "workflow_yaml": "name: Test\nsteps: []"
}
```

## Setup & Usage

```bash
# 1. Copy environment template
cp ../.env.example ../.env
# Add your API keys to .env

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Start API server
python main.py

# 4. Test endpoints (optional)
curl http://localhost:8000/api/agents
```

## Environment Variables

The API requires API keys in a `.env` file in the project root:

```bash
# Required: At least one API key
ANTHROPIC_API_KEY=sk-ant-your_key_here
OPENAI_API_KEY=sk-your_openai_key_here

# Optional: CORS and server config  
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
```

**Security:** The .env file is never committed to git. The API provides helpful error messages if keys are missing.

## Architecture

**Thin Wrapper Approach:**
- Reuses ALL existing CLI logic (2108 lines)
- No code duplication
- Same mentorship quality
- Same agent roles and functionality

**File Structure:**
```
web_app/
├── main.py       # FastAPI app (250 lines)
├── models.py     # Pydantic models (57 lines)
├── test_api.py   # Tests (209 lines)
└── requirements.txt
```

## Test Results

```
✅ All 15 agent roles available including CTF specialists
✅ File upload and processing working
✅ Session management working  
✅ Error handling working
✅ Same mentorship quality as CLI
```

## Phase 1 Success Criteria - ACHIEVED

✅ Upload Python file via API  
✅ Ask "Find security issues" with reviewer role  
✅ Get same quality response as CLI  
✅ Session persistence works  
✅ Multiple agent roles work  
✅ Under 500 lines total (307 lines)

**Ready for Phase 2: Web Frontend**