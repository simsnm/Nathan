# Web App Development Plan

## Overview
Transform the proven CLI tool into a web/mobile application while maintaining the same disciplined development approach that took us from 87 lines to 2108 lines of working code.

**Core Principle:** Build slowly and purposefully with a plan. Test each phase before moving to the next.

## Current State
- ✅ Working CLI tool (2108 lines)
- ✅ CTF learning mentor with 8 specialized agents
- ✅ Intelligent model selection and cost optimization
- ✅ Production hardening (error handling, security, logging)
- ✅ Proven user value and methodology

## Target Vision
**"GitHub Copilot meets Khan Academy"** - AI mentorship accessible to every developer through a slick web interface that hides all complexity.

## Development Phases

### Phase 1: Core Backend API (Weeks 1-2)
**Goal:** Make CLI functionality accessible via HTTP API
**Success Criteria:** `curl` requests produce same results as CLI commands

**Implementation:**
```python
# FastAPI wrapper around existing logic
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    result = await run_codechat_logic(request)
    return ChatResponse(response=result, cost=estimated_cost)

@app.post("/api/upload")
async def upload_code(files: List[UploadFile]):
    # Handle file uploads, return file IDs for chat context
    
@app.get("/api/agents")
async def list_agents():
    # Return available agent roles and descriptions
```

**Key Endpoints:**
- `POST /api/chat` - Main chat interface
- `POST /api/upload` - File upload handling
- `GET /api/agents` - List available agent roles
- `GET /api/session/{id}` - Retrieve conversation history
- `POST /api/workflow` - Execute workflow.yaml

**Estimated Lines:** 300-500 (thin API layer)

**Testing:**
```bash
# CLI equivalent: ./codechat.py "review this code" -r reviewer
curl -X POST /api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "review this code", "role": "reviewer", "files": ["uploaded_file_id"]}'

# Should produce identical results
```

### Phase 2: Minimal Web Interface (Weeks 3-4)
**Goal:** Basic HTML/JS frontend with one core feature working
**Success Criteria:** Users can upload code and get AI mentorship in browser

**Implementation:**
```html
<!DOCTYPE html>
<html>
<head><title>AI Code Mentor</title></head>
<body>
    <div class="container">
        <h1>AI Code Mentor</h1>
        
        <!-- File Upload -->
        <input type="file" id="codeFile" multiple>
        
        <!-- Agent Selection -->
        <select id="agentRole">
            <option value="reviewer">Code Reviewer</option>
            <option value="architect">Architect</option>
            <option value="mentor">Mentor</option>
        </select>
        
        <!-- Question Input -->
        <textarea id="question" placeholder="What would you like help with?"></textarea>
        
        <!-- Submit -->
        <button onclick="askQuestion()">Get Help</button>
        
        <!-- Response -->
        <div id="response"></div>
    </div>
</body>
</html>
```

**Key Features:**
- File upload with drag-and-drop
- Agent role selection
- Basic chat interface
- Syntax-highlighted code display
- Session persistence

**Estimated Lines:** 200-300 HTML/JS/CSS

**Testing:**
- Upload a Python file
- Ask "review for security issues" 
- Verify response quality matches CLI

### Phase 3: Incremental Feature Addition (Weeks 5-8)

**Week 5: User Accounts & Sessions**
```sql
-- Simple user system
CREATE TABLE users (id, email, created_at);
CREATE TABLE sessions (id, user_id, conversation_history, created_at);
CREATE TABLE progress (user_id, skill_area, level, last_updated);
```

**Week 6: Progress Tracking UI**
```html
<div class="progress-dashboard">
    <h2>Your Learning Progress</h2>
    <div class="skill-bar">
        <span>Python</span>
        <div class="progress"><div class="fill" style="width: 60%"></div></div>
    </div>
    <div class="skill-bar">
        <span>Security</span>
        <div class="progress"><div class="fill" style="width: 87%"></div></div>
    </div>
</div>
```

**Week 7: Multi-Agent Workflows**
```javascript
// Visual workflow builder
const workflow = {
    steps: [
        {role: 'researcher', prompt: 'Research best practices'},
        {role: 'architect', prompt: 'Design the system'},
        {role: 'coder', prompt: 'Implement it'},
        {role: 'reviewer', prompt: 'Security review'}
    ]
};
```

**Week 8: Advanced File Management**
```html
<div class="file-manager">
    <div class="file-tree">
        <!-- Project structure visualization -->
    </div>
    <div class="editor">
        <!-- Basic code editor with syntax highlighting -->
    </div>
</div>
```

**Testing at Each Stage:**
- Core functionality still works
- New features add value
- Performance remains acceptable
- User experience improves

### Phase 4: Polish & Mobile (Weeks 9-12)

**Week 9-10: UX Polish**
- Responsive design
- Loading states
- Error handling
- Keyboard shortcuts
- Dark/light theme

**Week 11-12: Mobile Optimization**
- Touch-friendly interface
- Mobile code editor
- Offline capability
- Progressive Web App (PWA)

## Technical Architecture

### Backend Stack
```
FastAPI (Python) - Leverage existing CLI logic
├── /api/chat - Main chat endpoint
├── /api/upload - File handling
├── /api/auth - User authentication  
├── /api/progress - Learning tracking
└── /api/workflow - Workflow execution

Database: SQLite → PostgreSQL (as we scale)
File Storage: Local → S3/CloudFlare R2
Authentication: Simple JWT → Auth0/Firebase
```

### Frontend Stack
```
Phase 2: Vanilla HTML/JS/CSS (prove concept)
Phase 3: Add Vite + vanilla JS (better dev experience)  
Phase 4: Consider Vue/React (if complexity demands it)

NOT starting with framework - keep it simple initially
```

## Key Design Principles

### 1. **Maintain CLI Parity**
- Every web feature should match CLI functionality
- Don't break existing workflows
- API should be thin wrapper around proven logic

### 2. **Progressive Enhancement**
- Start with basic HTML forms (works without JS)
- Add JavaScript for better UX
- Add real-time features last

### 3. **User-Centric Development**
- Test with real users at each phase
- Measure: time to first value, feature adoption, user retention
- Simple onboarding: sign up → upload code → get help

### 4. **Cost Consciousness**  
- Show cost estimates prominently
- Smart model selection (inherited from CLI)
- Usage limits and billing integration

## Success Metrics

### Phase 1 (API):
- ✅ 100% feature parity with CLI via API
- ✅ Response time < 2 seconds
- ✅ Handles file uploads properly

### Phase 2 (Basic Web):
- ✅ Users can complete full workflow in browser
- ✅ Interface is intuitive (no documentation needed)
- ✅ Works on mobile browsers

### Phase 3 (Features):
- ✅ User retention > 70% week-to-week
- ✅ Average session time > 10 minutes
- ✅ Feature adoption > 50% for new additions

### Phase 4 (Polish):
- ✅ Feels like professional product
- ✅ Mobile experience equivalent to desktop
- ✅ Ready for beta users

## Risk Mitigation

### Technical Risks:
- **API wrapper complexity** → Start simple, refactor later
- **Frontend framework choice** → Delay decision, start vanilla
- **File upload security** → Validate everything, sandbox execution

### Product Risks:  
- **Feature creep** → Stick to plan, test each phase
- **Poor UX** → User test early and often
- **Performance issues** → Monitor and optimize incrementally

### Market Risks:
- **Competition** → Focus on unique mentorship angle
- **User adoption** → Start with existing CLI users
- **Monetization** → Freemium model, prove value first

## Next Steps

1. **Week 1:** Set up FastAPI project, implement basic `/api/chat` endpoint
2. **Test immediately:** Verify API produces same results as CLI
3. **Document learnings:** What works, what needs adjustment
4. **Plan Week 2:** Based on Week 1 results

**Remember:** Build one working thing, test it, then add the next feature. The same discipline that built a 2108-line CLI tool will build a successful web application.

---

*This document will be updated as we learn and iterate. The plan is a guide, not a prescription - adapt as needed while maintaining the core principle of incremental, tested progress.*