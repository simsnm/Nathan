#!/usr/bin/env python3
"""
codechat - A simple CLI tool to chat with Claude about code
"""

import os
import sys
import argparse
import re
import json
import fnmatch
import requests
import urllib.parse
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codechat.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Cost tracking
COST_TRACKER = {
    "total_tokens": 0,
    "total_cost": 0.0,
    "requests": 0,
    "saved": 0.0,
    "model_usage": {}
}

# Model routing configuration
MODEL_ROUTING = {
    "simple": {"models": ["ollama:codellama", "gpt-3.5-turbo"], "keywords": ["fix", "typo", "format", "rename", "simple", "comment"]},
    "medium": {"models": ["gpt-3.5-turbo", "claude-instant"], "keywords": ["implement", "function", "add", "feature", "debug", "test"]},
    "complex": {"models": ["claude-3-5-sonnet-20241022", "gpt-4"], "keywords": ["design", "architect", "security", "review", "optimize", "research"]},
    "local_first": {"models": ["ollama:codellama"], "keywords": ["boilerplate", "template"]}
}

# Model capabilities and costs
MODEL_CAPABILITIES = {
    "claude-3-5-sonnet-20241022": {"cost_per_1k": 0.03, "provider": "claude"},
    "gpt-4": {"cost_per_1k": 0.03, "provider": "openai"},
    "gpt-3.5-turbo": {"cost_per_1k": 0.001, "provider": "openai"}, 
    "claude-instant": {"cost_per_1k": 0.008, "provider": "claude"},
    "ollama:codellama": {"cost_per_1k": 0, "provider": "ollama"}
}

# Agent role definitions with strict constraints
AGENT_ROLES = {
    "clarifier": {
        "description": "Clarifies user intent before any work begins",
        "prompt_prefix": """You are a requirements clarifier. Your ONLY job is to understand what the user wants.
You must:
1. Ask clarifying questions to understand the user's true intent
2. Be specific - don't accept vague requirements
3. Summarize what you understand
4. End with EXACTLY this format for confirmation:

UNDERSTANDING SUMMARY:
[Your summary here]

Is this correct? (y/n)

DO NOT provide solutions, implementations, or move forward without confirmation.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["text"]
    },
    "architect": {
        "description": "Designs system architecture and high-level structure",
        "prompt_prefix": """You are a senior software architect. Focus ONLY on system design, patterns, and structure.
You must NOT write any code. Output only:
- Architecture descriptions
- Design patterns
- Component diagrams (as text/markdown)
- API specifications
- Data models
If asked to implement, refuse and only provide design.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": "no_code",  # Will strip any code blocks
        "allowed_output": ["markdown", "text", "yaml", "json"]
    },
    "coder": {
        "description": "Writes actual implementation code",
        "prompt_prefix": """You are an expert programmer. Write ONLY the code that was requested.
Do NOT:
- Add extra features not asked for
- Write tests unless specifically asked
- Add documentation beyond minimal comments
- Create additional classes or functions unless required
- Critique or review the design
Just implement exactly what was asked.""",
        "preferred_provider": "openai",
        "preferred_model": "gpt-4",
        "output_filter": "code_only",
        "allowed_output": ["code"]
    },
    "reviewer": {
        "description": "Reviews code for bugs, security, and best practices",
        "prompt_prefix": """You are a senior code reviewer. ONLY review and critique code.
Do NOT:
- Write fixes or implementations
- Provide corrected code
- Implement solutions
Only identify issues, explain problems, and describe what should be fixed.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": "no_code",
        "allowed_output": ["markdown", "text"]
    },
    "tester": {
        "description": "Writes test cases and finds edge cases",
        "prompt_prefix": """You are a QA engineer. Write ONLY test code.
Do NOT modify the implementation. Only write tests.""",
        "preferred_provider": "openai",
        "preferred_model": "gpt-4",
        "output_filter": "tests_only",
        "allowed_output": ["code"]
    },
    "documenter": {
        "description": "Writes clear documentation and comments",
        "prompt_prefix": """You are a technical writer. Write ONLY documentation.
Do NOT write or modify code. Only create documentation, comments, and explanations.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": "no_code",
        "allowed_output": ["markdown", "text"]
    },
    "optimizer": {
        "description": "Optimizes code for performance",
        "prompt_prefix": """You are a performance engineer. ONLY optimize existing code.
Do NOT add features or change functionality. Only improve performance.""",
        "preferred_provider": "ollama",
        "preferred_model": "codellama",
        "output_filter": "code_only",
        "allowed_output": ["code"]
    },
    "researcher": {
        "description": "Researches documentation, dependencies, and best practices",
        "prompt_prefix": """You are a technical researcher. Your job is to find and summarize information.
You should:
1. Find relevant documentation and API references
2. Research package dependencies and alternatives
3. Locate code examples and best practices
4. Check security advisories and known issues
5. Provide clear, actionable summaries
DO NOT implement code. Only research and document findings.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text", "json"]
    },
    "mentor": {
        "description": "Senior developer mentor who teaches while solving problems",
        "prompt_prefix": """You are a senior developer mentor. Your job is to elevate the user's skills while solving their problem.

ALWAYS follow this format:
1. ANALYSIS: What's the current state and what needs improvement
2. SOLUTION: The technical solution with detailed explanations
3. WHY THIS WAY: Explain your reasoning and decision process
4. ALTERNATIVES: What other approaches exist and why you didn't choose them
5. LEARNING NOTES: Key patterns, principles, or concepts being used
6. SKILL DEVELOPMENT: What the user should learn next

Be specific about trade-offs, explain your thinking process, and always include the WHY behind decisions.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text"]
    },
    "tutor": {
        "description": "Interactive tutor who teaches step-by-step",
        "prompt_prefix": """You are an experienced developer teaching step-by-step. Be interactive and educational.

YOUR APPROACH:
1. Start by assessing current understanding with questions
2. Build knowledge incrementally - don't overwhelm
3. Ask 'Why do you think...?' questions to check understanding
4. Provide hands-on exercises and examples
5. Explain concepts before showing code
6. Check understanding before moving to next concept

ALWAYS include:
- Questions to assess understanding
- Step-by-step explanations
- Practice exercises
- Real-world context for concepts

Be patient, encouraging, and focus on building understanding rather than just delivering solutions.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text"]
    },
    "reverse-engineer": {
        "description": "Binary analysis, assembly, malware reverse engineering",
        "prompt_prefix": """You are an expert reverse engineer who teaches step-by-step binary analysis.
ALWAYS follow this CTF approach:
1. RECONNAISSANCE: file, strings, checksec, entropy analysis
2. STATIC ANALYSIS: disassembly, control flow, vulnerability identification  
3. DYNAMIC ANALYSIS: debugging, runtime behavior, memory layout
4. EXPLOITATION: payload development, bypass techniques

Explain assembly clearly, show tool commands, identify vulnerability patterns. Guide through gdb, ghidra, objdump usage.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text", "code"]
    },
    "crypto-analyst": {
        "description": "Cryptanalysis, cipher breaking, hash analysis",
        "prompt_prefix": """You are a cryptography expert who breaks down complex crypto challenges.
CTF CRYPTO METHODOLOGY:
1. CIPHER IDENTIFICATION: frequency analysis, pattern recognition
2. WEAKNESS ANALYSIS: implementation flaws, mathematical vulnerabilities
3. ATTACK VECTORS: timing attacks, padding oracle, chosen plaintext
4. EXPLOITATION: key recovery, plaintext extraction

Explain mathematical concepts simply. Show practical attacks with code examples.""",
        "preferred_provider": "claude", 
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text", "code"]
    },
    "web-hacker": {
        "description": "Web app security, OWASP Top 10, client/server attacks",
        "prompt_prefix": """You are a web security expert who teaches practical exploitation.
WEB CTF APPROACH:
1. RECONNAISSANCE: directory enumeration, technology stack identification
2. VULNERABILITY SCANNING: OWASP Top 10, input validation flaws
3. EXPLOITATION: manual testing, payload crafting, bypass techniques
4. POST-EXPLOITATION: privilege escalation, data extraction

Show both manual and automated approaches. Explain defense bypasses systematically.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022", 
        "output_filter": None,
        "allowed_output": ["markdown", "text", "code"]
    },
    "forensics-expert": {
        "description": "Digital forensics, memory analysis, network forensics",
        "prompt_prefix": """You are a digital forensics expert who teaches evidence analysis.
FORENSICS CTF METHODOLOGY:
1. EVIDENCE ACQUISITION: file recovery, metadata extraction, timeline creation
2. ARTIFACT ANALYSIS: file signatures, hidden data, steganography
3. MEMORY FORENSICS: process analysis, network connections, malware detection
4. NETWORK FORENSICS: packet analysis, protocol reconstruction, data carving

Guide through systematic investigation approaches. Explain artifact interpretation.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text", "code"]
    },
    "exploit-dev": {
        "description": "Exploit development, shellcode, ROP/JOP chains",
        "prompt_prefix": """You are an exploit development expert who teaches practical pwning.
PWN CTF METHODOLOGY:
1. VULNERABILITY ANALYSIS: bug classification, exploitability assessment
2. EXPLOITATION STRATEGY: stack/heap overflow, format string, use-after-free
3. BYPASS TECHNIQUES: ASLR, DEP, stack canaries, FORTIFY_SOURCE  
4. PAYLOAD DEVELOPMENT: shellcode, ROP chains, return-to-libc

Always explain the vulnerability first. Show step-by-step exploitation methodology.""",
        "preferred_provider": "claude",
        "preferred_model": "claude-3-5-sonnet-20241022",
        "output_filter": None,
        "allowed_output": ["markdown", "text", "code"]
    }
}

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

class AIProvider:
    """Base class for AI providers"""
    def chat(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        raise NotImplementedError

class ClaudeProvider(AIProvider):
    """Anthropic Claude provider"""
    def __init__(self, api_key: str):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")
    
    def chat(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        def _call():
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=messages
            )
            # Track costs (approximate)
            COST_TRACKER["requests"] += 1
            COST_TRACKER["total_tokens"] += max_tokens
            COST_TRACKER["total_cost"] += (max_tokens / 1000) * 0.03  # ~$0.03 per 1K tokens
            return response.content[0].text
        
        return retry_with_backoff(_call)

class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""
    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Install openai: pip install openai")
    
    def chat(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

class OllamaProvider(AIProvider):
    """Local Ollama provider"""
    def __init__(self, model: str = "codellama", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    def chat(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        import requests
        
        # Convert messages to Ollama format
        prompt = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Ollama error: {response.status_code}")

def analyze_task_complexity(prompt, role, context_size=0):
    """Analyze task complexity to select appropriate model"""
    prompt_lower = prompt.lower()
    
    # Role-based complexity
    if role in ["architect", "researcher"]:
        return "complex"
    elif role in ["reviewer", "optimizer"]:
        return "complex" if "security" in prompt_lower else "medium"
    elif role in ["coder"]:
        return "medium"
    elif role in ["tester", "documenter"]:
        return "medium" if context_size > 10000 else "simple"
    
    # Keyword-based complexity
    for complexity, config in MODEL_ROUTING.items():
        if any(keyword in prompt_lower for keyword in config["keywords"]):
            return complexity
    
    # Context-based complexity
    if context_size > 50000:
        return "complex"
    elif context_size > 10000:
        return "medium"
    
    return "simple"

def get_available_models():
    """Check which models are available based on API keys and local setup"""
    available = []
    
    # Check Claude
    if os.environ.get('ANTHROPIC_API_KEY'):
        available.extend(["claude-3-5-sonnet-20241022", "claude-instant"])
    
    # Check OpenAI
    if os.environ.get('OPENAI_API_KEY'):
        available.extend(["gpt-4", "gpt-3.5-turbo"])
    
    # Assume Ollama is available locally (could test with ping)
    available.extend(["ollama:codellama", "ollama:llama2"])
    
    return available

def select_optimal_model(prompt, role=None, context_size=0, force_model=None, optimize_for="cost"):
    """Select optimal model based on task complexity and preferences"""
    
    if force_model:
        logger.info(f"Using forced model: {force_model}")
        return force_model, MODEL_CAPABILITIES.get(force_model, {}).get("provider", "claude")
    
    # Analyze task
    complexity = analyze_task_complexity(prompt, role, context_size)
    available_models = get_available_models()
    
    # Get candidate models for this complexity
    candidate_models = MODEL_ROUTING[complexity]["models"]
    
    # Filter by availability
    available_candidates = [m for m in candidate_models if m in available_models]
    
    if not available_candidates:
        # Fallback to any available model
        logger.warning(f"No models available for {complexity} task, using fallback")
        available_candidates = available_models[:1] if available_models else ["claude-3-5-sonnet-20241022"]
    
    # Select based on optimization preference
    if optimize_for == "cost":
        # Choose cheapest model
        selected = min(available_candidates, key=lambda m: MODEL_CAPABILITIES.get(m, {}).get("cost_per_1k", 0.1))
    elif optimize_for == "quality":
        # Choose most expensive (usually best) model
        selected = max(available_candidates, key=lambda m: MODEL_CAPABILITIES.get(m, {}).get("cost_per_1k", 0))
    else:
        # Default to first available
        selected = available_candidates[0]
    
    # Calculate cost savings
    if len(available_candidates) > 1:
        most_expensive = max(available_candidates, key=lambda m: MODEL_CAPABILITIES.get(m, {}).get("cost_per_1k", 0))
        if selected != most_expensive:
            selected_cost = MODEL_CAPABILITIES.get(selected, {}).get("cost_per_1k", 0)
            expensive_cost = MODEL_CAPABILITIES.get(most_expensive, {}).get("cost_per_1k", 0)
            estimated_tokens = min(context_size + 1000, 4000)  # Rough estimate
            savings = (expensive_cost - selected_cost) * (estimated_tokens / 1000)
            COST_TRACKER["saved"] += savings
    
    provider = MODEL_CAPABILITIES.get(selected, {}).get("provider", "claude")
    
    # Track model usage
    COST_TRACKER["model_usage"][selected] = COST_TRACKER["model_usage"].get(selected, 0) + 1
    
    logger.info(f"Selected {selected} for {complexity} task (provider: {provider})")
    return selected, provider

def get_provider(provider_name: str, api_key: Optional[str] = None, model: Optional[str] = None) -> AIProvider:
    """Factory function to get the right provider"""
    if provider_name == "claude":
        if not api_key:
            raise ValueError("Claude requires an API key")
        return ClaudeProvider(api_key)
    elif provider_name == "openai":
        if not api_key:
            raise ValueError("OpenAI requires an API key")
        return OpenAIProvider(api_key, model or "gpt-4")
    elif provider_name == "ollama":
        return OllamaProvider(model or "codellama")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

def read_file(filepath):
    """Read a file and return its contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

def read_gitignore(project_path):
    """Read .gitignore patterns from project root"""
    gitignore_path = Path(project_path) / '.gitignore'
    patterns = []
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception:
            pass
    # Always ignore common patterns
    patterns.extend(['.git', '__pycache__', '*.pyc', 'node_modules', '.env'])
    return patterns

def should_skip_file(filepath, gitignore_patterns):
    """Check if file should be skipped based on gitignore patterns"""
    path = Path(filepath)
    name = path.name
    
    # Skip binary and large files
    binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz', 
                         '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite'}
    if path.suffix.lower() in binary_extensions:
        return True
    
    # Check gitignore patterns
    for pattern in gitignore_patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(str(path), pattern):
            return True
    
    return False

def collect_files(paths, recursive=False, gitignore_patterns=None):
    """Collect files from multiple paths (files, directories, patterns)"""
    if gitignore_patterns is None:
        gitignore_patterns = []
    
    files = []
    total_size = 0
    
    for path in paths:
        path = Path(path)
        
        if path.is_file():
            if not should_skip_file(path, gitignore_patterns):
                size = path.stat().st_size
                files.append((str(path), size))
                total_size += size
        elif path.is_dir():
            pattern = '**/*' if recursive else '*'
            for file_path in path.glob(pattern):
                if file_path.is_file() and not should_skip_file(file_path, gitignore_patterns):
                    try:
                        size = file_path.stat().st_size
                        files.append((str(file_path), size))
                        total_size += size
                    except Exception:
                        continue
    
    return files, total_size

def read_multiple_files(file_list, max_context_size=100000):
    """Read multiple files and combine their contents intelligently"""
    contents = []
    total_chars = 0
    files_read = []
    files_skipped = []
    
    # Sort files by size (smaller first) to include more files
    file_list.sort(key=lambda x: x[1])
    
    for filepath, size in file_list:
        if total_chars + size > max_context_size:
            files_skipped.append(filepath)
            continue
        
        content = read_file(filepath)
        if content:
            contents.append(f"=== File: {filepath} ===\n{content}")
            total_chars += len(content)
            files_read.append(filepath)
        else:
            files_skipped.append(filepath)
    
    return "\n\n".join(contents), files_read, files_skipped, total_chars

def write_file(filepath, content):
    """Write content to a file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}", file=sys.stderr)
        return False

def validate_url(url):
    """Validate URL to prevent SSRF attacks"""
    blocked_domains = ['localhost', '127.0.0.1', '0.0.0.0', '192.168', '10.', '172.']
    parsed = urllib.parse.urlparse(url)
    
    for blocked in blocked_domains:
        if blocked in parsed.netloc:
            logger.warning(f"Blocked potentially unsafe URL: {url}")
            return False
    
    if parsed.scheme not in ['http', 'https']:
        logger.warning(f"Blocked non-HTTP URL: {url}")
        return False
        
    return True

def search_duckduckgo(query, max_results=5):
    """Search using DuckDuckGo Instant Answer API (no key needed)"""
    try:
        url = "https://api.duckduckgo.com/"
        if not validate_url(url):
            return [{"title": "Error", "content": "Invalid URL", "url": ""}]
            
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        # Get instant answer if available
        if data.get("AbstractText"):
            results.append({"title": "Summary", "content": data["AbstractText"], "url": data.get("AbstractURL", "")})
        
        # Get related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({"title": topic.get("FirstURL", "").split("/")[-1], "content": topic["Text"], "url": topic.get("FirstURL", "")})
        
        return results
    except Exception as e:
        return [{"title": "Error", "content": f"Search failed: {e}", "url": ""}]

def fetch_github_info(repo_path):
    """Fetch GitHub repository information (no auth needed for public repos)"""
    try:
        # Parse repo path (e.g., "redis/redis-py" or full URL)
        if "github.com" in repo_path:
            parts = repo_path.split("github.com/")[-1].split("/")
            owner, repo = parts[0], parts[1].replace(".git", "")
        else:
            owner, repo = repo_path.split("/")
        
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data["full_name"],
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "open_issues": data["open_issues_count"],
                "last_update": data["updated_at"],
                "description": data["description"],
                "language": data["language"],
                "license": data.get("license", {}).get("name", "Unknown")
            }
        return None
    except Exception as e:
        return {"error": f"Failed to fetch GitHub info: {e}"}

def fetch_pypi_info(package_name):
    """Fetch package info from PyPI"""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            info = data["info"]
            return {
                "name": info["name"],
                "version": info["version"],
                "summary": info["summary"],
                "author": info["author"],
                "license": info["license"],
                "requires_python": info.get("requires_python", "Unknown"),
                "keywords": info.get("keywords", ""),
                "home_page": info.get("home_page", "")
            }
        return None
    except Exception as e:
        return {"error": f"Failed to fetch PyPI info: {e}"}

def research_topic(query, research_type="general"):
    """Perform research based on query and type"""
    results = {
        "query": query,
        "type": research_type,
        "findings": []
    }
    
    if research_type == "api_docs":
        # Search for API documentation
        search_results = search_duckduckgo(f"{query} API documentation reference")
        results["findings"].extend(search_results)
        
    elif research_type == "dependencies":
        # Research package dependencies
        if "python" in query.lower() or "pip" in query.lower():
            # Extract package name
            words = query.split()
            for word in words:
                if word not in ["python", "pip", "install", "package", "library"]:
                    pypi_info = fetch_pypi_info(word)
                    if pypi_info and "error" not in pypi_info:
                        results["findings"].append({"title": "PyPI Info", "content": json.dumps(pypi_info, indent=2)})
                        break
        
        # Also search for comparisons
        search_results = search_duckduckgo(f"{query} comparison alternatives")
        results["findings"].extend(search_results)
        
    elif research_type == "examples":
        # Find code examples
        search_results = search_duckduckgo(f"{query} code example implementation")
        results["findings"].extend(search_results)
        
    elif research_type == "security":
        # Check security advisories
        search_results = search_duckduckgo(f"{query} CVE security vulnerability advisory")
        results["findings"].extend(search_results)
        
    else:
        # General research
        search_results = search_duckduckgo(query)
        results["findings"].extend(search_results)
    
    return results

def extract_code_blocks(text):
    """Extract code blocks from markdown text"""
    # Find all code blocks with optional language specifier
    pattern = r'```(?:\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def filter_output_by_role(text, role):
    """Filter output based on role constraints"""
    if not role or role not in AGENT_ROLES:
        return text
    
    filter_type = AGENT_ROLES[role].get("output_filter")
    
    if filter_type == "no_code":
        # Remove ALL code blocks for non-coding roles
        filtered = re.sub(r'```[\s\S]*?```', '[CODE REMOVED - This role cannot output code]', text)
        # Also remove inline code
        filtered = re.sub(r'`[^`]+`', '[inline code removed]', filtered)
        return filtered
    
    elif filter_type == "code_only":
        # Extract only code blocks
        code_blocks = extract_code_blocks(text)
        if code_blocks:
            return "\n\n".join(code_blocks)
        else:
            # If no code blocks found, assume the whole response is code
            return text
    
    elif filter_type == "tests_only":
        # Keep only test code
        code_blocks = extract_code_blocks(text)
        test_code = []
        for block in code_blocks:
            # Simple heuristic: if it contains "test" or "assert", it's likely test code
            if 'test' in block.lower() or 'assert' in block.lower() or 'expect' in block.lower():
                test_code.append(block)
        if test_code:
            return "\n\n".join(test_code)
        else:
            return "\n".join(code_blocks) if code_blocks else text
    
    return text

def load_context(context_file, max_messages=20):
    """Load conversation context from file with pruning"""
    if not os.path.exists(context_file):
        return []
    try:
        with open(context_file, 'r') as f:
            messages = json.load(f)
            # Prune old messages to prevent context explosion
            if len(messages) > max_messages:
                logger.info(f"Pruning context from {len(messages)} to {max_messages} messages")
                messages = messages[-max_messages:]
            return messages
    except Exception as e:
        logger.warning(f"Could not load context: {e}")
        return []

def save_context(context_file, messages):
    """Save conversation context to file"""
    try:
        with open(context_file, 'w') as f:
            json.dump(messages, f, indent=2)
        return True
    except Exception as e:
        print(f"Warning: Could not save context: {e}", file=sys.stderr)
        return False

class KnowledgeTracker:
    """Tracks learning progress and builds knowledge base"""
    
    def __init__(self, knowledge_file="my_learnings.json"):
        self.knowledge_file = knowledge_file
        self.knowledge_base = self.load_knowledge()
    
    def load_knowledge(self):
        """Load existing knowledge base"""
        default = {"learned_topics": {}, "skill_assessments": [], "learning_goals": []}
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r') as f:
                    loaded = json.load(f)
                    # Ensure all required keys exist
                    for key in default:
                        if key not in loaded:
                            loaded[key] = default[key]
                    return loaded
            except Exception:
                return default
        return default
    
    def track_learning(self, topic, explanation, level="beginner"):
        """Track a new learning topic"""
        self.knowledge_base["learned_topics"][topic] = {
            "learned_on": datetime.now().isoformat(),
            "explanation": explanation,
            "level": level,
            "times_practiced": 1 if topic not in self.knowledge_base["learned_topics"] else 
                             self.knowledge_base["learned_topics"][topic].get("times_practiced", 0) + 1
        }
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)

class CTFKnowledge:
    """Tracks CTF learning progress and builds InfoSec skill profile"""
    
    def __init__(self, ctf_file="ctf_progress.json"):
        self.ctf_file = ctf_file
        self.progress = self.load_progress()
    
    def load_progress(self):
        """Load CTF progress"""
        default = {
            "skills": {"web": {"attempts": 0, "successes": 0, "level": "beginner"},
                      "pwn": {"attempts": 0, "successes": 0, "level": "beginner"},
                      "crypto": {"attempts": 0, "successes": 0, "level": "beginner"},
                      "reversing": {"attempts": 0, "successes": 0, "level": "beginner"},
                      "forensics": {"attempts": 0, "successes": 0, "level": "beginner"}},
            "challenges": [], "curriculum": {}, "learning_path": []
        }
        if os.path.exists(self.ctf_file):
            try:
                with open(self.ctf_file, 'r') as f:
                    loaded = json.load(f)
                    for key in default:
                        if key not in loaded:
                            loaded[key] = default[key]
                    return loaded
            except:
                return default
        return default
    
    def track_challenge(self, category, difficulty, success, challenge_name=""):
        """Track CTF challenge attempt"""
        self.progress["skills"][category]["attempts"] += 1
        if success:
            self.progress["skills"][category]["successes"] += 1
        
        # Calculate level based on success rate and difficulty
        skill = self.progress["skills"][category]
        success_rate = skill["successes"] / skill["attempts"] if skill["attempts"] > 0 else 0
        
        if success_rate > 0.8 and skill["attempts"] > 10:
            skill["level"] = "advanced"
        elif success_rate > 0.6 and skill["attempts"] > 5:
            skill["level"] = "intermediate"
        elif success_rate > 0.3 and skill["attempts"] > 2:
            skill["level"] = "junior"
        
        self.progress["challenges"].append({
            "date": datetime.now().isoformat(), "category": category,
            "difficulty": difficulty, "success": success, "name": challenge_name
        })
        self.save_progress()
    
    def save_progress(self):
        """Save progress to file"""
        with open(self.ctf_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

def analyze_ctf_challenge(file_path):
    """Analyze a CTF challenge file and provide structured assessment"""
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    analysis = {"recon": [], "vulnerabilities": [], "strategy": [], "learning": []}
    
    # Basic file analysis
    try:
        with open(file_path, 'rb') as f:
            content = f.read(1024)  # First 1KB
            
        # File type detection
        if content.startswith(b'\x7fELF'):
            analysis["recon"].append("ELF binary detected - likely pwn/reverse challenge")
            analysis["strategy"].append("Run: file, checksec, strings, objdump -h")
        elif b'<!DOCTYPE html' in content or b'<html' in content:
            analysis["recon"].append("HTML file - likely web challenge")  
            analysis["strategy"].append("Analyze source code for XSS, SQL injection, directory traversal")
        elif content.startswith(b'PK'):
            analysis["recon"].append("ZIP archive - likely contains multiple challenge files")
            analysis["strategy"].append("Extract and analyze contents individually")
        else:
            analysis["recon"].append("Unknown file type - run 'file' command for identification")
    except:
        analysis["recon"].append("Could not read file - check permissions")
    
    return analysis

def analyze_code_patterns(code_content):
    """Analyze code for patterns and missing best practices"""
    patterns_found = []
    missing_patterns = []
    
    if "try:" in code_content and "except" in code_content:
        patterns_found.append("error_handling")
    else:
        missing_patterns.append("error_handling")
    
    if "logging" in code_content or "logger" in code_content:
        patterns_found.append("logging")
    else:
        missing_patterns.append("logging")
    
    if "async def" in code_content or "await" in code_content:
        patterns_found.append("async_programming")
    elif "requests." in code_content:
        missing_patterns.append("async_programming")
    
    if "unittest" in code_content or "pytest" in code_content or "test_" in code_content:
        patterns_found.append("testing")
    else:
        missing_patterns.append("testing")
    
    if 'if __name__ == "__main__"' in code_content:
        patterns_found.append("main_guard")
    
    return {"patterns": patterns_found, "missing": missing_patterns}

def generate_skill_analysis(code_analysis, knowledge_tracker=None):
    """Generate skill analysis and learning recommendations"""
    patterns_found = code_analysis.get("patterns", [])
    missing_patterns = code_analysis.get("missing", [])
    
    # Assess skill level
    score = len(patterns_found) * 10 - len(missing_patterns) * 5
    if score >= 60: level = "intermediate"
    elif score >= 30: level = "junior"  
    else: level = "beginner"
    
    # Generate recommendations
    skill_map = {
        "error_handling": "Learn try-catch patterns and graceful error handling",
        "logging": "Add structured logging for debugging and monitoring", 
        "async_programming": "Learn async/await for better performance",
        "testing": "Write unit tests to ensure code reliability"
    }
    
    recommendations = []
    for pattern in missing_patterns[:3]:  # Top 3 priorities
        if pattern in skill_map:
            recommendations.append({
                "skill": pattern.replace("_", " ").title(),
                "action": skill_map[pattern],
                "priority": "high" if pattern in ["error_handling", "testing"] else "medium"
            })
    
    return {
        "current_level": level,
        "score": score,
        "strengths": patterns_found,
        "recommendations": recommendations
    }

def run_consensus(question, code_content=None, filepath=None, role="reviewer", models=None):
    """Run same prompt through multiple models for consensus"""
    if models is None:
        models = [
            ("claude", "claude-3-5-sonnet-20241022"),
            ("openai", "gpt-4"),
            ("ollama", "codellama")
        ]
    
    results = []
    prompt_parts = []
    
    if role and role in AGENT_ROLES:
        prompt_parts.append(AGENT_ROLES[role]["prompt_prefix"] + "\n\n")
    
    if code_content:
        if filepath:
            prompt_parts.append(f"File: {filepath}\n")
        prompt_parts.append(f"```\n{code_content}\n```\n\n")
    
    prompt_parts.append(question)
    prompt = "".join(prompt_parts)
    
    for provider_name, model_name in models:
        try:
            # Get API key for provider
            api_key = None
            if provider_name == "claude":
                api_key = os.environ.get('ANTHROPIC_API_KEY')
            elif provider_name == "openai":
                api_key = os.environ.get('OPENAI_API_KEY')
            
            if provider_name != "ollama" and not api_key:
                results.append((provider_name, model_name, f"No API key for {provider_name}"))
                continue
            
            provider = get_provider(provider_name, api_key, model_name)
            messages = [{"role": "user", "content": prompt}]
            response = provider.chat(messages)
            
            # Apply role filtering
            filtered = filter_output_by_role(response, role)
            results.append((provider_name, model_name, filtered))
            
        except Exception as e:
            results.append((provider_name, model_name, f"Error: {e}"))
    
    return analyze_consensus(results)

def analyze_consensus(results):
    """Analyze consensus among model responses"""
    output = []
    output.append("=" * 50)
    output.append("MULTI-MODEL CONSENSUS ANALYSIS")
    output.append("=" * 50)
    
    # Count successes
    successful = [r for r in results if not r[2].startswith("Error:") and not r[2].startswith("No API")]
    failed = [r for r in results if r[2].startswith("Error:") or r[2].startswith("No API")]
    
    output.append(f"\n✓ {len(successful)}/{len(results)} models responded successfully")
    
    if failed:
        output.append("\n⚠ Failed models:")
        for provider, model, error in failed:
            output.append(f"  - {provider}/{model}: {error}")
    
    if len(successful) >= 2:
        # Simple consensus detection for security/architecture reviews
        security_keywords = ["security", "vulnerability", "risk", "unsafe", "injection", "exploit"]
        performance_keywords = ["slow", "inefficient", "optimize", "bottleneck", "memory", "cpu"]
        
        security_concerns = []
        performance_concerns = []
        
        for provider, model, response in successful:
            lower_resp = response.lower()
            has_security = any(k in lower_resp for k in security_keywords)
            has_performance = any(k in lower_resp for k in performance_keywords)
            
            if has_security:
                security_concerns.append((provider, model))
            if has_performance:
                performance_concerns.append((provider, model))
        
        if security_concerns:
            output.append(f"\n🔒 SECURITY: {len(security_concerns)}/{len(successful)} models flag security concerns")
        
        if performance_concerns:
            output.append(f"\n⚡ PERFORMANCE: {len(performance_concerns)}/{len(successful)} models flag performance issues")
        
        output.append("\n" + "-" * 50)
        output.append("INDIVIDUAL RESPONSES:")
        output.append("-" * 50)
        
        for provider, model, response in successful:
            output.append(f"\n[{provider.upper()}/{model}]:")
            # Truncate long responses for consensus view
            if len(response) > 500:
                output.append(response[:500] + "... [truncated]")
            else:
                output.append(response)
            output.append("")
    
    return "\n".join(output)

def interactive_clarify(provider, initial_request, code_content=None, filepath=None):
    """Interactive clarification loop that requires user confirmation"""
    
    messages = []
    clarified_intent = None
    max_iterations = 10  # Prevent infinite loops
    
    # Build initial prompt
    prompt_parts = []
    prompt_parts.append(AGENT_ROLES["clarifier"]["prompt_prefix"] + "\n\n")
    
    if code_content:
        if filepath:
            prompt_parts.append(f"File: {filepath}\n")
        prompt_parts.append(f"```\n{code_content}\n```\n\n")
    
    prompt_parts.append(f"User request: {initial_request}")
    initial_prompt = "".join(prompt_parts)
    
    print("\n" + "="*50, file=sys.stderr)
    print("INTENT CLARIFICATION PHASE", file=sys.stderr)
    print("="*50 + "\n", file=sys.stderr)
    
    messages.append({"role": "user", "content": initial_prompt})
    
    for iteration in range(max_iterations):
        try:
            # Get clarifier response
            response = provider.chat(messages)
            print(response)
            
            # Check if this is a confirmation request
            if "Is this correct? (y/n)" in response:
                # Get user confirmation
                user_input = input("\nYour response: ").strip().lower()
                
                if user_input == 'y' or user_input == 'yes':
                    # Extract the understanding summary
                    if "UNDERSTANDING SUMMARY:" in response:
                        summary_start = response.index("UNDERSTANDING SUMMARY:")
                        summary_end = response.index("Is this correct?")
                        clarified_intent = response[summary_start:summary_end].strip()
                        print("\n✓ Intent clarified and confirmed!", file=sys.stderr)
                        break
                    else:
                        clarified_intent = response
                        break
                else:
                    # User said no, continue clarification
                    print("\nLet me clarify further...\n", file=sys.stderr)
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": "No, that's not quite right. Let me explain..."})
                    
                    # Get additional user input
                    user_clarification = input("Please clarify: ")
                    messages.append({"role": "user", "content": user_clarification})
            else:
                # Clarifier is asking questions
                messages.append({"role": "assistant", "content": response})
                
                # Get user answer
                user_answer = input("\nYour response: ")
                messages.append({"role": "user", "content": user_answer})
                
        except KeyboardInterrupt:
            print("\n\nClarification cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nError during clarification: {e}", file=sys.stderr)
            break
    
    if not clarified_intent:
        print("\nWarning: Clarification incomplete, proceeding with original request.", file=sys.stderr)
        clarified_intent = initial_request
    
    return clarified_intent

def collaborate_agents(initial_provider, initial_question, code_content=None, filepath=None, initial_role="reviewer", max_rounds=5):
    """Enable bi-directional agent collaboration with safeguards"""
    
    print("\n" + "="*50, file=sys.stderr)
    print("AGENT COLLABORATION MODE", file=sys.stderr)
    print("="*50 + "\n", file=sys.stderr)
    
    messages = []
    round_num = 0
    issues_resolved = False
    last_severity = "high"
    
    # Define collaboration pairs
    collaborations = {
        "reviewer": "coder",
        "coder": "reviewer",
        "tester": "coder",
        "architect": "coder",
        "documenter": "coder"
    }
    
    current_role = initial_role
    current_provider = initial_provider
    current_question = initial_question
    
    while round_num < max_rounds and not issues_resolved:
        round_num += 1
        print(f"\n--- Round {round_num}/{max_rounds} ---", file=sys.stderr)
        print(f"Agent: {current_role.upper()}", file=sys.stderr)
        
        # Get response from current agent
        response, messages = chat_about_code(
            current_provider, current_question, code_content, filepath, messages, current_role
        )
        
        print(f"\n{current_role.upper()}: {response[:200]}..." if len(response) > 200 else response)
        
        # Check for resolution indicators
        resolution_terms = ["lgtm", "looks good", "resolved", "fixed", "no issues", "approved"]
        if any(term in response.lower() for term in resolution_terms):
            print("\n✓ Issue appears resolved!", file=sys.stderr)
            issues_resolved = True
            break
        
        # Assess severity from response
        if "critical" in response.lower() or "vulnerability" in response.lower():
            last_severity = "critical"
        elif "error" in response.lower() or "bug" in response.lower():
            last_severity = "high"
        elif "warning" in response.lower() or "improvement" in response.lower():
            last_severity = "medium"
        else:
            last_severity = "low"
        
        # User checkpoint after round 2
        if round_num == 2:
            print(f"\n{'='*50}", file=sys.stderr)
            print(f"CHECKPOINT: Round {round_num} complete", file=sys.stderr)
            print(f"Current severity: {last_severity}", file=sys.stderr)
            print(f"{'='*50}", file=sys.stderr)
            
            user_input = input("\nContinue collaboration? (y/n/resolve): ").strip().lower()
            if user_input == 'n':
                print("Collaboration stopped by user.", file=sys.stderr)
                break
            elif user_input == 'resolve':
                print("Marked as resolved by user.", file=sys.stderr)
                issues_resolved = True
                break
        
        # Check for diminishing returns (issues getting trivial)
        if last_severity == "low" and round_num > 2:
            print("\nDiminishing returns detected (low severity issues). Stopping.", file=sys.stderr)
            break
        
        # Switch to collaborating agent
        if current_role in collaborations:
            next_role = collaborations[current_role]
            print(f"\nSwitching to {next_role.upper()} agent...", file=sys.stderr)
            
            # Prepare question for next agent based on response
            if current_role == "reviewer":
                current_question = f"Fix these issues found in review:\n{response}"
                code_content = code_content  # Keep the code for fixing
            elif current_role == "coder":
                current_question = f"Review these fixes:\n{response}"
                # Update code_content with the fixes if response contains code
                code_blocks = extract_code_blocks(response)
                if code_blocks:
                    code_content = "\n\n".join(code_blocks)
            
            current_role = next_role
            # Get appropriate provider for new role
            role_config = AGENT_ROLES.get(next_role, {})
            provider_name = role_config.get('preferred_provider', 'claude')
            
            # Try to get the provider (simplified for this example)
            current_provider = initial_provider  # Keep same provider for simplicity
        else:
            print(f"No collaboration defined for {current_role}", file=sys.stderr)
            break
    
    if round_num >= max_rounds:
        print(f"\n⚠ Maximum rounds ({max_rounds}) reached. Manual intervention required.", file=sys.stderr)
    
    return response, messages

def chat_about_code(provider, question, code_content=None, filepath=None, messages=None, role=None):
    """Send code and question to AI provider, get response"""
    
    # Start with existing context or empty list
    if messages is None:
        messages = []
    
    # Build the prompt for this turn
    prompt_parts = []
    
    # Add role-specific prefix if using a role
    if role and role in AGENT_ROLES:
        prompt_parts.append(AGENT_ROLES[role]["prompt_prefix"] + "\n\n")
    
    # Enforce planning requirement for coder role
    if role == "coder" and not code_content:
        # Check if there's a plan or design in the question
        plan_indicators = ["design", "plan", "architecture", "specification", "requirements"]
        has_plan = any(indicator in question.lower() for indicator in plan_indicators)
        
        if not has_plan and "--skip-planning" not in sys.argv:
            error_msg = """
ERROR: No plan found. Coders require either:
1. An architect's design document (use -f design.md)
2. A clear plan/specification in the request
3. --skip-planning flag (not recommended)

Recommended workflow:
1. ./codechat.py "Design your system" -r architect -o plan.md
2. ./codechat.py -f plan.md "Implement this" -r coder -o implementation.py
"""
            print(error_msg, file=sys.stderr)
            return error_msg, messages
    
    # If researcher role, perform actual research first
    if role == "researcher":
        # Determine research type from question
        research_type = "general"
        if any(word in question.lower() for word in ["api", "documentation", "docs"]):
            research_type = "api_docs"
        elif any(word in question.lower() for word in ["package", "dependency", "library", "compare"]):
            research_type = "dependencies"
        elif any(word in question.lower() for word in ["example", "sample", "how to"]):
            research_type = "examples"
        elif any(word in question.lower() for word in ["security", "vulnerability", "cve", "advisory"]):
            research_type = "security"
        
        # Perform research
        print(f"Researching: {question[:50]}...", file=sys.stderr)
        research_results = research_topic(question, research_type)
        
        # Add research results to prompt
        prompt_parts.append("Research findings:\n")
        prompt_parts.append(json.dumps(research_results, indent=2))
        prompt_parts.append("\n\nBased on these findings, please provide a comprehensive summary addressing: ")
    
    if code_content:
        if filepath:
            prompt_parts.append(f"File: {filepath}\n")
        prompt_parts.append(f"```\n{code_content}\n```\n\n")
    
    prompt_parts.append(question)
    prompt = "".join(prompt_parts)
    
    # Add user message to context
    messages.append({"role": "user", "content": prompt})
    
    try:
        response_text = provider.chat(messages)
        
        # Apply role-based output filtering
        filtered_response = filter_output_by_role(response_text, role)
        
        # Add filtered response to context
        messages.append({"role": "assistant", "content": filtered_response})
        
        return filtered_response, messages
    except Exception as e:
        return f"Error calling AI API: {e}", messages

def main():
    parser = argparse.ArgumentParser(
        description="Chat with AI about code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 🎓 Mentorship & Learning Mode
  codechat -f my_code.py "Elevate to senior level" -r mentor --show-changes
  codechat "Teach me microservices" -r tutor --interactive
  codechat --analyze-skills --project .  # Analyze entire codebase for gaps
  codechat "Design API" -r architect --explain-reasoning
  
  # 🏁 CTF & InfoSec Learning Mode
  codechat -f challenge.bin "Analyze this CTF challenge" -r reverse-engineer --ctf-mode
  codechat "Teach me buffer overflows" -r exploit-dev --ctf-tutorial
  codechat "I'm stuck on this crypto" -r crypto-analyst --hint-mode
  codechat --show-curriculum  # Show CTF learning paths
  codechat -f web_challenge.php "Find web vulns" -r web-hacker --track-progress
  
  # 🧠 Intelligent model selection (saves money!)
  codechat "Fix typo in line 42" --auto              # → Uses local/cheap model
  codechat "Design microservice architecture" --auto # → Uses Claude/GPT-4
  
  # 🤝 Bi-directional collaboration  
  codechat -f payment.py "Review this" -r reviewer --collaborate
  
  # 📋 Planning-first workflow (enforced)
  codechat "Design payment system" -r architect --auto -o plan.md
  codechat -f plan.md "Implement this" -r coder --auto-doc -o payment.py
        """
    )
    
    parser.add_argument('question', nargs='?', help='Your question about the code')
    parser.add_argument('-f', '--files', help='Files to analyze (comma-separated or multiple -f)')
    parser.add_argument('-d', '--dir', action='append', help='Directory to analyze (can use multiple)')
    parser.add_argument('--project', help='Analyze entire project (respects .gitignore)')
    parser.add_argument('-o', '--output', help='Write response to this file')
    parser.add_argument('--code-only', action='store_true', 
                       help='Only write code blocks to output file')
    parser.add_argument('-c', '--context', help='Context file for conversation history')
    parser.add_argument('--new-context', action='store_true',
                       help='Start fresh conversation (clear existing context)')
    parser.add_argument('--save-context', help='Save research/output as context for later use')
    parser.add_argument('--use-context', help='Load previously saved research context')
    parser.add_argument('-p', '--provider', default='claude',
                       choices=['claude', 'openai', 'ollama'],
                       help='AI provider to use (default: claude)')
    parser.add_argument('--model', help='Model to use (for openai/ollama)')
    parser.add_argument('-r', '--role', 
                       choices=list(AGENT_ROLES.keys()),
                       help='Agent role (clarifier, architect, coder, reviewer, tester, documenter, optimizer, researcher, mentor, tutor)')
    parser.add_argument('--clarify', action='store_true',
                       help='Start with interactive intent clarification before processing')
    parser.add_argument('--collaborate', action='store_true',
                       help='Enable bi-directional agent collaboration')
    parser.add_argument('--skip-planning', action='store_true',
                       help='Skip planning requirement for coder (not recommended)')
    parser.add_argument('--auto-doc', action='store_true',
                       help='Automatically generate documentation after coding')
    parser.add_argument('--consensus', action='store_true',
                       help='Run through multiple models for consensus (security/architecture reviews)')
    parser.add_argument('--auto', action='store_true',
                       help='Automatically select optimal model based on task complexity')
    parser.add_argument('--force-model', help='Force specific model (overrides --auto)')
    parser.add_argument('--optimize', choices=['cost', 'quality', 'speed'], default='cost',
                       help='Optimization preference for auto selection')
    parser.add_argument('--explain-reasoning', action='store_true',
                       help='Show detailed reasoning for all decisions (mentorship mode)')
    parser.add_argument('--analyze-skills', action='store_true',
                       help='Analyze code for skill gaps and learning opportunities')
    parser.add_argument('--show-changes', action='store_true',
                       help='Show what was changed and why (learning mode)')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive tutorial mode (for tutor role)')
    
    # CTF-specific arguments
    parser.add_argument('--ctf-mode', action='store_true',
                       help='Enable CTF challenge analysis mode')
    parser.add_argument('--hint-mode', action='store_true',
                       help='Provide hints without spoiling solutions (CTF competition mode)')
    parser.add_argument('--ctf-tutorial', action='store_true',
                       help='Interactive CTF learning with step-by-step guidance')
    parser.add_argument('--track-progress', action='store_true',
                       help='Track CTF challenge attempts and build skill profile')
    parser.add_argument('--show-curriculum', action='store_true',
                       help='Show CTF learning curriculum and recommended next challenges')
    
    parser.add_argument('--api-key', help='API key (or set ANTHROPIC_API_KEY or OPENAI_API_KEY)')
    
    args = parser.parse_args()
    
    # Handle clarification mode
    if args.clarify or args.role == "clarifier":
        # Get API key for clarifier (always uses Claude)
        api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("Error: Clarifier requires ANTHROPIC_API_KEY", file=sys.stderr)
            sys.exit(1)
        
        # Get provider for clarifier
        try:
            clarifier_provider = get_provider("claude", api_key)
        except Exception as e:
            print(f"Error initializing clarifier: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Get code content if provided
        code_content = None
        filepath = None
        
        # Collect all input paths
        input_paths = []
        
        if args.files:
            for f in args.files.split(','):
                input_paths.append(f.strip())
        
        if args.dir:
            input_paths.extend(args.dir)
        
        if args.project:
            input_paths.append(args.project)
            
        if input_paths:
            recursive = bool(args.project)
            gitignore_patterns = []
            if args.project:
                gitignore_patterns = read_gitignore(args.project)
            
            file_list, total_size = collect_files(input_paths, recursive, gitignore_patterns)
            
            if file_list:
                code_content, files_read, files_skipped, total_chars = read_multiple_files(file_list)
                size_kb = total_chars / 1024
                print(f"Reading {len(files_read)} files ({size_kb:.1f}KB total)...", file=sys.stderr)
                filepath = f"{len(files_read)} files"
        elif not sys.stdin.isatty():
            code_content = sys.stdin.read()
            filepath = "stdin"
        
        # Run interactive clarification
        clarified_intent = interactive_clarify(clarifier_provider, args.question, code_content, filepath)
        
        # If user just wanted clarification, stop here
        if args.role == "clarifier":
            if args.output:
                if write_file(args.output, clarified_intent):
                    print(f"Wrote clarified intent to {args.output}")
            sys.exit(0)
        
        # Otherwise, update the question with clarified intent
        print(f"\n{'='*50}", file=sys.stderr)
        print("PROCEEDING WITH CLARIFIED INTENT", file=sys.stderr)
        print(f"{'='*50}\n", file=sys.stderr)
        
        # Replace the original question with clarified intent
        args.question = clarified_intent
    
    # Handle CTF modes
    if args.ctf_mode or args.hint_mode or args.ctf_tutorial or args.show_curriculum:
        ctf_tracker = CTFKnowledge()
        
        # Show curriculum if requested
        if args.show_curriculum:
            curriculum = {
                "beginner": {"web": ["XSS basics", "SQL injection", "Directory traversal"],
                            "crypto": ["Caesar cipher", "Substitution", "XOR"],
                            "forensics": ["File signatures", "Strings analysis", "Metadata"],
                            "pwn": ["Stack overflow basics", "Buffer overflow identification"],
                            "reversing": ["Assembly basics", "Static analysis", "String extraction"]},
                "intermediate": {"web": ["CSRF", "XXE", "SSRF", "File upload bypass"],
                                "crypto": ["RSA attacks", "Hash collisions", "Block cipher modes"],
                                "forensics": ["Memory analysis", "Network forensics", "Steganography"],
                                "pwn": ["Return-to-libc", "ROP chains", "Format strings"],
                                "reversing": ["Dynamic analysis", "Packing detection", "Anti-debugging"]}
            }
            print("📚 CTF LEARNING CURRICULUM")
            print("=" * 50)
            for level, categories in curriculum.items():
                print(f"\n🎯 {level.upper()} LEVEL:")
                for cat, topics in categories.items():
                    current_skill = ctf_tracker.progress["skills"].get(cat, {})
                    skill_level = current_skill.get("level", "beginner")
                    attempts = current_skill.get("attempts", 0)
                    print(f"  {cat.upper()} [{skill_level}] ({attempts} attempts):")
                    for topic in topics:
                        print(f"    • {topic}")
            sys.exit(0)
        
        # CTF challenge analysis mode
        if args.ctf_mode and args.files:
            file_path = args.files.split(',')[0].strip()
            analysis = analyze_ctf_challenge(file_path)
            
            print("🔍 CTF CHALLENGE ANALYSIS")
            print("=" * 50)
            if "error" in analysis:
                print(f"❌ {analysis['error']}")
                sys.exit(1)
            
            for section, items in analysis.items():
                if items:
                    print(f"\n🎯 {section.upper()}:")
                    for item in items:
                        print(f"  • {item}")
            
            # Auto-suggest role based on analysis
            suggested_role = "reverse-engineer"  # Default
            if "web challenge" in str(analysis.get("recon", [])):
                suggested_role = "web-hacker"
            elif "crypto" in args.question.lower():
                suggested_role = "crypto-analyst"
            
            print(f"\n💡 Suggested role: --role {suggested_role}")
            
            # If no role specified, use suggested one
            if not args.role:
                args.role = suggested_role
        
        # Hint mode - provide guidance without spoiling
        if args.hint_mode:
            hint_questions = [
                "What type of challenge do you think this is?",
                "Have you tried basic reconnaissance commands?",
                "What patterns do you notice in the data?", 
                "Are there any obvious weaknesses or entry points?",
                "What tools would be most helpful for this category?"
            ]
            print("\n🔍 GUIDED QUESTIONS (No spoilers!):")
            for i, question in enumerate(hint_questions, 1):
                print(f"{i}. {question}")
            
            # Modify question to be hint-oriented
            args.question = f"Provide hints for: {args.question}. Don't give away solutions, just guide the thinking process with questions and general direction."
        
        # CTF tutorial mode - interactive step-by-step learning
        if args.ctf_tutorial:
            print("🎓 CTF INTERACTIVE TUTORIAL MODE")
            print("=" * 50)
            print("I'll teach you step-by-step. This is hands-on learning!")
            
            # Enhanced question for tutorial mode
            args.question = f"Teach me about: {args.question}. Use interactive tutorial approach with: 1) Explain concept, 2) Show example, 3) Ask me to try, 4) Guide through solution, 5) Explain what I learned."
            
            # Force tutor role if not specified
            if not args.role or args.role not in ["tutor", "reverse-engineer", "crypto-analyst", "web-hacker", "forensics-expert", "exploit-dev"]:
                args.role = "tutor"
    
    # Handle consensus mode
    if args.consensus:
        # Get code content if provided
        code_content = None
        filepath = None
        
        # Collect all input paths
        input_paths = []
        
        if args.files:
            for f in args.files.split(','):
                input_paths.append(f.strip())
        
        if args.dir:
            input_paths.extend(args.dir)
        
        if args.project:
            input_paths.append(args.project)
            
        if input_paths:
            recursive = bool(args.project)
            gitignore_patterns = []
            if args.project:
                gitignore_patterns = read_gitignore(args.project)
            
            file_list, total_size = collect_files(input_paths, recursive, gitignore_patterns)
            
            if file_list:
                code_content, files_read, files_skipped, total_chars = read_multiple_files(file_list)
                size_kb = total_chars / 1024
                print(f"Reading {len(files_read)} files ({size_kb:.1f}KB total)...", file=sys.stderr)
                filepath = f"{len(files_read)} files"
        elif not sys.stdin.isatty():
            code_content = sys.stdin.read()
            filepath = "stdin"
        
        # Run consensus with default reviewer role or specified role
        role = args.role or "reviewer"
        consensus_result = run_consensus(args.question, code_content, filepath, role)
        
        # Handle output
        if args.output:
            if write_file(args.output, consensus_result):
                print(f"Wrote consensus analysis to {args.output}")
        else:
            print(consensus_result)
        
        sys.exit(0)
    
    # Handle skill analysis mode
    if args.analyze_skills:
        print("\n🎯 ANALYZING YOUR SKILLS...", file=sys.stderr)
        
        if not input_paths and not code_content:
            print("Error: Need code to analyze. Use -f, -d, or --project", file=sys.stderr)
            sys.exit(1)
        
        # Get code for analysis (reuse existing logic)
        if not code_content and input_paths:
            recursive = bool(args.project)
            gitignore_patterns = []
            if args.project:
                gitignore_patterns = read_gitignore(args.project)
            
            file_list, total_size = collect_files(input_paths, recursive, gitignore_patterns)
            if file_list:
                code_content, files_read, files_skipped, total_chars = read_multiple_files(file_list)
        
        if code_content:
            # Analyze patterns
            analysis = analyze_code_patterns(code_content)
            skill_analysis = generate_skill_analysis(analysis)
            
            # Display results
            print(f"\n🎯 SKILL ANALYSIS:")
            print(f"Current Level: {skill_analysis['current_level'].title()} (score: {skill_analysis['score']})")
            
            if skill_analysis['strengths']:
                print(f"\n✅ STRENGTHS:")
                for strength in skill_analysis['strengths']:
                    print(f"  • {strength.replace('_', ' ').title()}")
            
            if skill_analysis['recommendations']:
                print(f"\n🎓 LEARNING OPPORTUNITIES:")
                for rec in skill_analysis['recommendations']:
                    priority_icon = "🔥" if rec['priority'] == 'high' else "📚"
                    print(f"  {priority_icon} {rec['skill']}: {rec['action']}")
            
            # Save to output file if specified
            if args.output:
                output_content = f"# Skill Analysis\n\nCurrent Level: {skill_analysis['current_level']}\n\n"
                output_content += "## Recommendations\n"
                for rec in skill_analysis['recommendations']:
                    output_content += f"- {rec['skill']}: {rec['action']}\n"
                
                if write_file(args.output, output_content):
                    print(f"\n💾 Analysis saved to {args.output}")
        
        sys.exit(0)
    
    # Normal single-model mode
    # Intelligent model selection or manual selection
    if args.auto or args.force_model:
        # Calculate context size
        context_size = len(code_content) if code_content else 0
        
        # Select optimal model
        selected_model, provider_name = select_optimal_model(
            args.question, 
            args.role, 
            context_size, 
            args.force_model, 
            args.optimize
        )
        
        model_name = selected_model
        
        # Show selection reasoning
        complexity = analyze_task_complexity(args.question, args.role, context_size)
        estimated_cost = MODEL_CAPABILITIES.get(selected_model, {}).get("cost_per_1k", 0) * 4  # ~4K tokens
        print(f"🤖 Auto-selected {selected_model} for {complexity} task (est. ${estimated_cost:.3f})", file=sys.stderr)
        
    else:
        # Traditional manual selection
        provider_name = args.provider
        model_name = args.model
        
        if args.role and args.role in AGENT_ROLES:
            role_config = AGENT_ROLES[args.role]
            # Use role's preferred provider if not explicitly set
            if args.provider == 'claude' and not args.model:  # Default values
                provider_name = role_config.get('preferred_provider', 'claude')
                model_name = role_config.get('preferred_model')
            print(f"Using {args.role} role with {provider_name}", file=sys.stderr)
    
    # Get API key based on provider
    api_key = args.api_key
    if not api_key:
        if provider_name == 'claude':
            api_key = os.environ.get('ANTHROPIC_API_KEY')
        elif provider_name == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY')
        # Ollama doesn't need an API key
        
    # Get provider
    try:
        provider = get_provider(provider_name, api_key, model_name)
    except Exception as e:
        print(f"Error initializing {provider_name}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Handle context
    messages = []
    if args.context:
        if args.new_context:
            # Start fresh
            messages = []
            print(f"Starting new conversation in {args.context}", file=sys.stderr)
        else:
            # Load existing context
            messages = load_context(args.context)
            if messages:
                print(f"Continuing conversation with {len(messages)//2} previous exchanges", file=sys.stderr)
    
    # Load research context if specified
    if args.use_context:
        try:
            with open(args.use_context, 'r') as f:
                research_context = f.read()
                print(f"Loaded research context from {args.use_context}", file=sys.stderr)
                # Prepend research context to question
                args.question = f"Using this research context:\n{research_context}\n\nTask: {args.question}"
        except Exception as e:
            print(f"Warning: Could not load research context: {e}", file=sys.stderr)
    
    # Get code content from various sources
    code_content = None
    filepath = None
    
    # Collect all input paths
    input_paths = []
    
    if args.files:
        # Handle comma-separated files
        for f in args.files.split(','):
            input_paths.append(f.strip())
    
    if args.dir:
        # Add directories
        input_paths.extend(args.dir)
    
    if args.project:
        # Add project directory
        input_paths.append(args.project)
        
    if input_paths:
        # Determine if recursive based on --project flag
        recursive = bool(args.project)
        
        # Get gitignore patterns if in project mode
        gitignore_patterns = []
        if args.project:
            gitignore_patterns = read_gitignore(args.project)
        
        # Collect all files
        file_list, total_size = collect_files(input_paths, recursive, gitignore_patterns)
        
        if not file_list:
            print("No files found to analyze", file=sys.stderr)
            sys.exit(1)
        
        # Read files with context limit
        code_content, files_read, files_skipped, total_chars = read_multiple_files(file_list)
        
        # Report what we're reading
        size_kb = total_chars / 1024
        print(f"Reading {len(files_read)} files ({size_kb:.1f}KB total)...", file=sys.stderr)
        
        if files_skipped:
            print(f"Skipped {len(files_skipped)} files (exceeds context limit)", file=sys.stderr)
            if len(files_skipped) <= 5:
                for f in files_skipped:
                    print(f"  - {f}", file=sys.stderr)
        
        # For context tracking, list all files
        filepath = f"{len(files_read)} files"
        
    elif not sys.stdin.isatty():
        # Read from stdin if piped
        code_content = sys.stdin.read()
        filepath = "stdin"
    
    # Handle collaboration mode
    if args.collaborate:
        if args.role in ["reviewer", "coder", "tester", "architect", "documenter"]:
            response, updated_messages = collaborate_agents(
                provider, args.question, code_content, filepath, args.role
            )
        else:
            print("Collaboration mode requires reviewer, coder, tester, architect, or documenter role", file=sys.stderr)
            sys.exit(1)
    else:
        # Enhance question for mentorship modes
        enhanced_question = args.question
        
        if args.explain_reasoning:
            enhanced_question += "\n\nIMPORTANT: Explain your reasoning, show alternatives considered, and include learning notes."
        
        if args.show_changes and code_content:
            enhanced_question += "\n\nShow exactly what changes you made and WHY each change improves the code."
        
        if args.interactive and args.role == "tutor":
            enhanced_question = f"Teaching mode: {enhanced_question}\nAsk questions to assess understanding before providing solutions."
        
        # Get response normally
        response, updated_messages = chat_about_code(provider, enhanced_question, code_content, filepath, messages, args.role)
        
        # Auto-generate documentation if flag is set and role was coder
        if args.auto_doc and args.role == "coder":
            print("\n" + "="*50, file=sys.stderr)
            print("AUTO-GENERATING DOCUMENTATION", file=sys.stderr)
            print("="*50 + "\n", file=sys.stderr)
            
            # Extract code from response
            code_blocks = extract_code_blocks(response)
            if code_blocks:
                doc_code = "\n\n".join(code_blocks)
                doc_question = "Generate comprehensive documentation for this code including docstrings, usage examples, and API reference"
                
                # Switch to documenter role
                doc_response, _ = chat_about_code(provider, doc_question, doc_code, "generated_code", None, "documenter")
                
                # Save documentation
                doc_file = args.output.replace('.py', '_docs.md') if args.output else 'documentation.md'
                if write_file(doc_file, doc_response):
                    print(f"✓ Documentation saved to {doc_file}", file=sys.stderr)
    
    # Save updated context if using context file
    if args.context:
        save_context(args.context, updated_messages)
    
    # Save research context if specified (especially useful for researcher role)
    if args.save_context:
        context_to_save = response
        if write_file(args.save_context, context_to_save):
            print(f"Saved research context to {args.save_context}", file=sys.stderr)
    
    # Handle output
    if args.output:
        if args.code_only:
            # Extract and write only code blocks
            code_blocks = extract_code_blocks(response)
            if code_blocks:
                output_content = "\n\n".join(code_blocks)
                if write_file(args.output, output_content):
                    print(f"Wrote {len(code_blocks)} code block(s) to {args.output}")
            else:
                print("No code blocks found in response", file=sys.stderr)
        else:
            # Write full response
            if write_file(args.output, response):
                print(f"Wrote response to {args.output}")
    else:
        # Print to stdout as before
        print(response)

if __name__ == '__main__':
    try:
        main()
    finally:
        # Display intelligent cost tracking on exit
        if COST_TRACKER["requests"] > 0:
            print(f"\n--- Session Summary ---", file=sys.stderr)
            print(f"Tasks: {COST_TRACKER['requests']} completed", file=sys.stderr)
            
            # Model usage breakdown
            if COST_TRACKER["model_usage"]:
                model_list = []
                for model, count in COST_TRACKER["model_usage"].items():
                    short_name = model.split(":")[-1] if ":" in model else model.replace("-20241022", "")
                    model_list.append(f"{short_name} ({count}x)")
                print(f"Models used: {', '.join(model_list)}", file=sys.stderr)
            
            print(f"Total cost: ${COST_TRACKER['total_cost']:.2f}", file=sys.stderr)
            
            if COST_TRACKER["saved"] > 0:
                print(f"💰 Saved ${COST_TRACKER['saved']:.2f} by smart routing", file=sys.stderr)
                efficiency = (1 - COST_TRACKER["total_cost"] / (COST_TRACKER["total_cost"] + COST_TRACKER["saved"])) * 100
                print(f"Optimal routing: {efficiency:.0f}%", file=sys.stderr)
            
            # Show CTF progress if CTF mode was used
            if os.path.exists("ctf_progress.json"):
                try:
                    with open("ctf_progress.json", 'r') as f:
                        progress = json.load(f)
                        skills = progress.get("skills", {})
                        active_skills = [cat for cat, data in skills.items() if data.get("attempts", 0) > 0]
                        if active_skills:
                            print(f"🏁 CTF Skills: {', '.join([f'{cat}[{skills[cat]['level']}]' for cat in active_skills])}", file=sys.stderr)
                except:
                    pass
            
            print(f"Log file: codechat.log", file=sys.stderr)