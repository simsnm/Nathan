"""Persistent rate limiter using SQLite for production safety"""
import os
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class PersistentRateLimiter:
    """Rate limiter with SQLite persistence to survive restarts"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("RATE_LIMIT_DB", "/var/nathan/rate_limits.db")
        self.lock = Lock()
        
        # Configuration from environment with safe defaults
        self.MAX_REQUESTS_PER_IP_HOUR = int(os.getenv("MAX_REQUESTS_PER_IP_HOUR", "10"))
        self.MAX_REQUESTS_PER_IP_DAY = int(os.getenv("MAX_REQUESTS_PER_IP_DAY", "50"))
        self.MAX_DAILY_COST = float(os.getenv("MAX_DAILY_COST", "1.00"))
        self.MAX_DAILY_REQUESTS = int(os.getenv("MAX_DAILY_REQUESTS", "200"))
        
        # Initialize database
        self._init_db()
        
        # Clean old data on startup
        self._cleanup_old_data()
    
    def _init_db(self):
        """Initialize SQLite database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/speed
            
            # Table for tracking requests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_ip_time (ip_address, timestamp)
                )
            """)
            
            # Table for daily statistics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_requests INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    unique_ips INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_ip ON requests(ip_address)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_time ON requests(timestamp)")
            
            conn.commit()
    
    def check_limits(self, client_ip: str) -> tuple[bool, str]:
        """Check if request from IP is allowed"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    now = datetime.now()
                    today = now.date()
                    hour_ago = now - timedelta(hours=1)
                    day_ago = now - timedelta(days=1)
                    
                    # Get or create today's stats
                    stats = conn.execute(
                        "SELECT total_requests, total_cost FROM daily_stats WHERE date = ?",
                        (today,)
                    ).fetchone()
                    
                    if not stats:
                        conn.execute(
                            "INSERT INTO daily_stats (date) VALUES (?)",
                            (today,)
                        )
                        conn.commit()
                        daily_requests = 0
                        daily_cost = 0.0
                    else:
                        daily_requests, daily_cost = stats
                    
                    # Check daily limits
                    if daily_cost >= self.MAX_DAILY_COST:
                        logger.warning(f"Daily cost limit hit: ${daily_cost:.2f}")
                        return False, f"Daily cost limit reached (${self.MAX_DAILY_COST:.2f}). Nathan needs rest!"
                    
                    if daily_requests >= self.MAX_DAILY_REQUESTS:
                        logger.warning(f"Daily request limit hit: {daily_requests}")
                        return False, f"Daily request limit reached ({self.MAX_DAILY_REQUESTS}). Try tomorrow!"
                    
                    # Count IP-specific requests
                    hourly_count = conn.execute(
                        "SELECT COUNT(*) FROM requests WHERE ip_address = ? AND timestamp > ?",
                        (client_ip, hour_ago)
                    ).fetchone()[0]
                    
                    daily_count = conn.execute(
                        "SELECT COUNT(*) FROM requests WHERE ip_address = ? AND timestamp > ?",
                        (client_ip, day_ago)
                    ).fetchone()[0]
                    
                    # Check IP limits
                    if hourly_count >= self.MAX_REQUESTS_PER_IP_HOUR:
                        return False, f"Too many requests ({self.MAX_REQUESTS_PER_IP_HOUR}/hour limit). Try again later!"
                    
                    if daily_count >= self.MAX_REQUESTS_PER_IP_DAY:
                        return False, f"Daily limit reached ({self.MAX_REQUESTS_PER_IP_DAY}/day). Try tomorrow!"
                    
                    # Request allowed - record it
                    conn.execute(
                        "INSERT INTO requests (ip_address, timestamp) VALUES (?, ?)",
                        (client_ip, now)
                    )
                    
                    # Update daily stats
                    conn.execute(
                        "UPDATE daily_stats SET total_requests = total_requests + 1, last_updated = ? WHERE date = ?",
                        (now, today)
                    )
                    
                    conn.commit()
                    
                    # Calculate remaining requests
                    remaining_hourly = self.MAX_REQUESTS_PER_IP_HOUR - hourly_count - 1
                    remaining_daily = self.MAX_REQUESTS_PER_IP_DAY - daily_count - 1
                    
                    return True, f"OK (Remaining: {remaining_hourly}/hour, {remaining_daily}/day)"
                    
            except Exception as e:
                logger.error(f"Rate limiter error: {e}")
                # Fail open in case of database issues (be lenient)
                return True, "OK (rate limiter error, allowing request)"
    
    def add_cost(self, cost: float):
        """Track API costs"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    today = datetime.now().date()
                    conn.execute(
                        "UPDATE daily_stats SET total_cost = total_cost + ?, last_updated = ? WHERE date = ?",
                        (cost, datetime.now(), today)
                    )
                    conn.commit()
                    
                    # Get updated total
                    total = conn.execute(
                        "SELECT total_cost FROM daily_stats WHERE date = ?",
                        (today,)
                    ).fetchone()[0]
                    
                    logger.info(f"Cost added: ${cost:.4f}, Daily total: ${total:.4f}")
                    
                    # Warning if approaching limit
                    if total > self.MAX_DAILY_COST * 0.8:
                        logger.warning(f"⚠️ COST WARNING: ${total:.2f} of ${self.MAX_DAILY_COST:.2f} daily limit")
                        
            except Exception as e:
                logger.error(f"Failed to track cost: {e}")
    
    def get_status(self) -> dict:
        """Get current rate limiter status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                today = datetime.now().date()
                stats = conn.execute(
                    "SELECT total_requests, total_cost, unique_ips FROM daily_stats WHERE date = ?",
                    (today,)
                ).fetchone()
                
                if stats:
                    requests, cost, unique_ips = stats
                else:
                    requests = cost = unique_ips = 0
                
                # Count unique IPs today
                unique_ips = conn.execute(
                    "SELECT COUNT(DISTINCT ip_address) FROM requests WHERE DATE(timestamp) = ?",
                    (today,)
                ).fetchone()[0]
                
                return {
                    "daily_requests": requests,
                    "daily_cost": round(cost, 4),
                    "unique_visitors": unique_ips,
                    "requests_remaining": max(0, self.MAX_DAILY_REQUESTS - requests),
                    "cost_remaining": round(max(0, self.MAX_DAILY_COST - cost), 2),
                    "limits": {
                        "per_ip_hour": self.MAX_REQUESTS_PER_IP_HOUR,
                        "per_ip_day": self.MAX_REQUESTS_PER_IP_DAY,
                        "daily_requests": self.MAX_DAILY_REQUESTS,
                        "daily_cost": self.MAX_DAILY_COST
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e)}
    
    def reset_daily(self):
        """Reset daily counters (for manual reset or cron job)"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    today = datetime.now().date()
                    
                    # Log before reset
                    stats = conn.execute(
                        "SELECT total_requests, total_cost FROM daily_stats WHERE date = ?",
                        (today,)
                    ).fetchone()
                    
                    if stats:
                        logger.info(f"Daily reset - Requests: {stats[0]}, Cost: ${stats[1]:.4f}")
                    
                    # Create new day entry
                    conn.execute(
                        "INSERT OR REPLACE INTO daily_stats (date, total_requests, total_cost) VALUES (?, 0, 0)",
                        (today,)
                    )
                    
                    # Clean old request records (keep 7 days)
                    week_ago = datetime.now() - timedelta(days=7)
                    conn.execute("DELETE FROM requests WHERE timestamp < ?", (week_ago,))
                    
                    conn.commit()
                    logger.info("Daily limits reset successfully")
                    
            except Exception as e:
                logger.error(f"Failed to reset daily limits: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data on startup"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove requests older than 7 days
                week_ago = datetime.now() - timedelta(days=7)
                deleted = conn.execute(
                    "DELETE FROM requests WHERE timestamp < ?",
                    (week_ago,)
                ).rowcount
                
                # Remove stats older than 30 days
                month_ago = datetime.now().date() - timedelta(days=30)
                conn.execute("DELETE FROM daily_stats WHERE date < ?", (month_ago,))
                
                # VACUUM to reclaim space
                conn.execute("VACUUM")
                conn.commit()
                
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old request records")
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global instance
rate_limiter = PersistentRateLimiter()