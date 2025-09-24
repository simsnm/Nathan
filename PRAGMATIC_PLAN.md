# Pragmatic Plan: Multi-AI Code Generation System

## Current State
- `codechat.py`: 87 lines, works, talks to Claude about code
- Can read files, take stdin, get AI responses

## Goal
Multi-AI system where different models collaborate to produce actual code files.

## Build Order (One Feature at a Time)

### Phase 1: Make Current Tool More Useful ✓
- [x] Basic CLI that talks to Claude
- [x] Add ability to write response to a file (not just print)
- [x] Add conversation context (remember previous messages)

### Phase 2: Support Multiple AI Providers ✓
- [x] Abstract the Claude-specific code into a provider interface
- [x] Add OpenAI support (same interface, different implementation)
- [x] Add provider selection via CLI flag
- [x] Add local model support (Ollama)

### Phase 3: Basic Agent Roles
- [ ] Define simple roles (architect, coder, reviewer)
- [ ] Route questions to specific models based on role
- [ ] Still single-threaded, sequential operation

### Phase 4: Multi-Step Workflows
- [ ] Add ability to chain responses (output of one -> input to next)
- [ ] Save intermediate results
- [ ] Simple workflow definition (YAML or JSON)

### Phase 5: Code File Generation
- [ ] Parse code blocks from responses
- [ ] Write code to actual files
- [ ] Handle multiple files from single response

### Phase 6: Collaborative Agents
- [ ] Multiple agents working on same problem
- [ ] Combine responses intelligently
- [ ] Conflict resolution between different AI suggestions

## Development Rules
1. **Each feature must work before moving to next**
2. **No feature should break existing functionality**
3. **Every feature gets tested with real API calls**
4. **Keep it under 500 lines until Phase 4**
5. **No databases, no web servers, no microservices**

## Next Step
Add file writing capability to current tool. User can say:
```bash
codechat.py -f broken.py "Fix this code" --output fixed.py
```

This writes the response (including code) to fixed.py.

## Success Metrics
- Phase 1-2: Tool is useful for daily coding tasks
- Phase 3-4: Can automate simple multi-step tasks
- Phase 5-6: Can generate small working projects

## What We're NOT Building
- No GUI
- No real-time collaboration
- No "learning" or training
- No cloud deployment
- No "revolutionary" anything

Just a tool that uses multiple AIs to write code that works.