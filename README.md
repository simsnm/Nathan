# Nathan

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Size](https://img.shields.io/github/languages/code-size/simsnm/Nathan)](https://github.com/simsnm/Nathan)
[![Last Commit](https://img.shields.io/github/last-commit/simsnm/Nathan)](https://github.com/simsnm/Nathan)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Time](https://img.shields.io/badge/built%20in-6%20hours-brightgreen)](./ABOUT.md)

An AI development assistant that reduces API costs by 90% through intelligent model routing.

> **Built in 6 hours** by someone who learned to code 3 months ago with a broken hand. [Read the full story →](./ABOUT.md)

## Features

- **15 Specialized Agents**: From code review to CTF challenges
- **Smart Routing**: Automatically selects the cheapest capable model
- **Demo Mode**: Try without API keys
- **Session Persistence**: Remembers conversations across sessions
- **Web Interface**: Clean, responsive UI
- **CLI Tool**: Direct command-line access

## ⚡ Built Different

This isn't your typical GitHub project:
- **Development time**: 6 hours total
- **Developer experience**: 3 months (first project!)
- **Productivity**: 500+ lines/hour of production code
- **Result**: Fully deployed, production-ready platform

Nathan was built using the same AI-assisted workflow it now provides to others.

## Quick Start

```bash
# Clone repository
git clone https://github.com/simsnm/Nathan.git
cd Nathan

# Try demo mode (no API keys needed)
./nathan demo "Explain async/await"

# Or run web interface
cd web_app && python main.py
# Visit http://localhost:8000
```

## Requirements

Check your environment before installation:

```bash
# Check Python version (need 3.11+)
python --version

# Check pip is installed
pip --version

# Check git is installed
git --version
```

## Installation

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (optional)
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### CLI Examples
```bash
# Code review
./nathan review code.py

# Learning mode
./nathan learn "buffer overflows"

# CTF help
./nathan ctf challenge.bin

# General questions
./nathan "How do I implement a REST API?"
```

### Available Agents

| Agent | Purpose | Example Use Case |
|-------|---------|-----------------|
| `mentor` | Teaching concepts | Learning new technologies |
| `reviewer` | Code analysis | Security and quality checks |
| `coder` | Implementation | Writing new features |
| `architect` | System design | Planning architecture |
| `tester` | Test generation | Creating test suites |
| `reverse-engineer` | Binary analysis | CTF challenges |
| `crypto-analyst` | Cryptography | Cipher breaking |
| `web-hacker` | Web security | OWASP testing |

### Cost Optimization

Nathan automatically routes queries to minimize costs:

- Simple questions → GPT-3.5 Turbo ($0.001)
- Code review → Claude Haiku ($0.003)
- Complex analysis → GPT-4 ($0.03)
- Specialized tasks → Claude Opus ($0.06)

Average savings: 90% compared to using premium models exclusively.

## Web Interface

The web interface provides:
- Agent selection dropdown
- File upload support
- Conversation history
- User accounts (optional)
- Cost tracking

## Deployment

### Docker
```bash
docker-compose up -d
```

### Production
See [DEPLOYMENT.md](DEPLOYMENT.md) for full production deployment guide.

### Quick Deploy
```bash
./scripts/deploy.sh production your-domain.com
```

## Configuration

Environment variables (`.env` file):

```env
# API Keys
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
GOOGLE_API_KEY=your-key

# Optional
DEMO_MODE=false
DATABASE_PATH=./data/sessions.db
```

## Architecture

```
Nathan/
├── codechat.py          # Core CLI engine
├── nathan              # CLI wrapper
├── demo_mode.py        # Demo responses
├── web_app/           
│   ├── main.py        # FastAPI backend
│   ├── auth.py        # Authentication
│   └── database.py    # Session storage
├── web_frontend/      
│   └── index.html     # Web interface
└── scripts/           # Deployment scripts
```

## API Documentation

### Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Your question",
  "role": "mentor",
  "files": []
}
```

### List Agents
```http
GET /api/agents
```

Full API documentation available at `/docs` when running the web server.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

## Author

**Nathan M. Sims** - Learning to code at 10x speed with AI

- **Experience**: 3 months (started after breaking hand)
- **First Project**: This one - Nathan
- **Method**: AI-assisted development
- **Philosophy**: Build what you need, ship fast, learn faster
- **Contact**: nathan.m.sims@gmail.com

[Read the full story →](./ABOUT.md)

## Links

- GitHub: https://github.com/simsnm/Nathan
- Website: https://nathanmsims.com (launching tonight!)
- Story: [How I built this in 6 hours](./ABOUT.md)