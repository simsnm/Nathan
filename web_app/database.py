"""Simple SQLite database operations for user accounts and sessions"""
import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Optional, List, Dict
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "codechat.db")

@contextmanager
def get_db():
    """Get database connection with proper cleanup"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Create tables if they don't exist"""
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                skill_levels TEXT DEFAULT '{}',
                total_questions INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                subscription_tier TEXT DEFAULT 'free'
            )
        """)
        
        # Sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_cost REAL DEFAULT 0.0,
                title TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        print("✅ Database initialized")

def create_user(email: str) -> str:
    """Create new user and return user_id"""
    import uuid
    user_id = str(uuid.uuid4())
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, email) VALUES (?, ?)",
            (user_id, email)
        )
        conn.commit()
    
    return user_id

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", 
            (email,)
        ).fetchone()
        
        if user:
            return dict(user)
        return None

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        ).fetchone()
        
        if user:
            return dict(user)
        return None

def update_user_stats(user_id: str, additional_cost: float = 0.0):
    """Update user statistics"""
    with get_db() as conn:
        conn.execute("""
            UPDATE users 
            SET total_questions = total_questions + 1,
                total_cost = total_cost + ?
            WHERE id = ?
        """, (additional_cost, user_id))
        conn.commit()

def create_session(user_id: str, title: Optional[str] = None) -> str:
    """Create new session and return session_id"""
    import uuid
    session_id = str(uuid.uuid4())
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO sessions (id, user_id, title) 
            VALUES (?, ?, ?)
        """, (session_id, user_id, title))
        conn.commit()
    
    return session_id

def get_user_sessions(user_id: str, limit: int = 50) -> List[Dict]:
    """Get user's sessions"""
    with get_db() as conn:
        sessions = conn.execute("""
            SELECT id, title, created_at, last_updated, total_cost 
            FROM sessions 
            WHERE user_id = ? 
            ORDER BY last_updated DESC 
            LIMIT ?
        """, (user_id, limit)).fetchall()
        
        return [dict(s) for s in sessions]

def get_session(session_id: str, user_id: str) -> Optional[Dict]:
    """Get specific session"""
    with get_db() as conn:
        session = conn.execute("""
            SELECT * FROM sessions 
            WHERE id = ? AND user_id = ?
        """, (session_id, user_id)).fetchone()
        
        if session:
            session_dict = dict(session)
            # Parse JSON conversation
            session_dict['conversation'] = json.loads(session_dict.get('conversation', '[]'))
            return session_dict
        return None

def add_to_conversation(session_id: str, user_message: str, ai_response: str, cost: float = 0.0):
    """Add conversation turn to session"""
    with get_db() as conn:
        # Get current conversation
        result = conn.execute(
            "SELECT conversation FROM sessions WHERE id = ?", 
            (session_id,)
        ).fetchone()
        
        if result:
            conversation = json.loads(result['conversation'] or '[]')
            conversation.append({
                'timestamp': datetime.now().isoformat(),
                'user_message': user_message,
                'ai_response': ai_response,
                'cost': cost
            })
            
            # Update session
            conn.execute("""
                UPDATE sessions 
                SET conversation = ?, 
                    last_updated = CURRENT_TIMESTAMP,
                    total_cost = total_cost + ?
                WHERE id = ?
            """, (json.dumps(conversation), cost, session_id))
            
            conn.commit()

# Initialize database on import
if __name__ != "__main__":
    init_db()