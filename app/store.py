"""Database store for VoltageGPU Twitter Bot."""

import aiosqlite
import sqlite3
import json
import hashlib
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

from .config import Config

logger = logging.getLogger(__name__)

class Store:
    """SQLite-based storage for bot state and history."""
    
    def __init__(self, config: Config):
        """Initialize the database store."""
        self.config = config
        self.db_path = Path("data/bot.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database tables."""
        await self._init_database()
    
    async def _init_database(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    tweet_id TEXT,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    hashtags TEXT,
                    posted_at TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hashtag TEXT NOT NULL,
                    source TEXT NOT NULL,
                    score REAL NOT NULL DEFAULT 1.0,
                    region TEXT,
                    extracted_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS schedule_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    scheduled_for TIMESTAMP NOT NULL,
                    executed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_posts_account_date ON posts(account, date(posted_at));
                CREATE INDEX IF NOT EXISTS idx_posts_content_hash ON posts(content_hash);
                CREATE INDEX IF NOT EXISTS idx_trends_hashtag ON trends(hashtag);
                CREATE INDEX IF NOT EXISTS idx_trends_extracted_at ON trends(extracted_at);
            """)
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    async def is_duplicate_content(self, content: str, days: int = 30) -> bool:
        """Check if content is a duplicate within the specified days."""
        content_hash = self.get_content_hash(content)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM posts WHERE content_hash = ? AND posted_at >= ?",
                (content_hash, cutoff_date)
            )
            result = await cursor.fetchone()
            return result[0] > 0 if result else False
    
    async def record_post(self, account_id: str, tweet_id: str, content: str, 
                         hashtags: List[str]) -> int:
        """Record a successful post."""
        content_hash = self.get_content_hash(content)
        hashtags_str = " ".join(hashtags) if hashtags else ""
        
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                INSERT INTO posts (account, tweet_id, content, content_hash, hashtags, 
                                 posted_at, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_id, tweet_id, content, content_hash, hashtags_str, 
                  datetime.now(), True, None))
            await conn.commit()
            return cursor.lastrowid
    
    async def get_posts_today(self, account: str) -> int:
        """Get number of posts made today for an account."""
        today = date.today()
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM posts WHERE account = ? AND date(posted_at) = ? AND success = 1",
                (account, today)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    def get_last_tweet_id(self, account: str) -> Optional[str]:
        """Get the last successful tweet ID for an account."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT tweet_id FROM posts WHERE account = ? AND success = 1 AND tweet_id IS NOT NULL ORDER BY posted_at DESC LIMIT 1",
                (account,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    async def update_trends(self, trends: List[Dict[str, Any]]):
        """Save trending hashtags."""
        async with aiosqlite.connect(self.db_path) as conn:
            for trend in trends:
                await conn.execute("""
                    INSERT INTO trends (hashtag, source, score, region, extracted_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    trend['hashtag'],
                    trend.get('source', 'unknown'),
                    trend.get('score', 1.0),
                    trend.get('region'),
                    trend.get('timestamp', datetime.now())
                ))
            await conn.commit()
    
    def get_fresh_trends(self, limit: int = 20, max_age_minutes: int = 60) -> List[str]:
        """Get fresh trending hashtags."""
        cutoff_time = datetime.now().replace(minute=datetime.now().minute - max_age_minutes)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT hashtag, AVG(score) as avg_score
                FROM trends 
                WHERE extracted_at >= ?
                GROUP BY hashtag
                ORDER BY avg_score DESC, MAX(extracted_at) DESC
                LIMIT ?
            """, (cutoff_time, limit))
            return [row[0] for row in cursor.fetchall()]
    
    def clean_old_trends(self, max_age_hours: int = 24):
        """Clean old trend data."""
        cutoff_time = datetime.now().replace(hour=datetime.now().hour - max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM trends WHERE extracted_at < ?", (cutoff_time,))
    
    def set_state(self, key: str, value: Any):
        """Set a state value."""
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO bot_state (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value_str, datetime.now()))
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result is None:
                return default
            
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return result[0]
    
    def log_schedule(self, account: str, scheduled_for: datetime, status: str = "pending"):
        """Log a scheduled post."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO schedule_log (account, scheduled_for, status)
                VALUES (?, ?, ?)
            """, (account, scheduled_for, status))
    
    def update_schedule_status(self, account: str, scheduled_for: datetime, 
                             status: str, executed_at: Optional[datetime] = None):
        """Update schedule status."""
        if executed_at is None:
            executed_at = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE schedule_log 
                SET status = ?, executed_at = ?
                WHERE account = ? AND scheduled_for = ?
            """, (status, executed_at, account, scheduled_for))
    
    def get_account_stats(self, account: str) -> Dict[str, Any]:
        """Get comprehensive stats for an account."""
        today = date.today()
        
        with sqlite3.connect(self.db_path) as conn:
            # Posts today
            cursor = conn.execute(
                "SELECT COUNT(*) FROM posts WHERE account = ? AND date(posted_at) = ? AND success = 1",
                (account, today)
            )
            posts_today = cursor.fetchone()[0]
            
            # Last tweet ID
            cursor = conn.execute(
                "SELECT tweet_id FROM posts WHERE account = ? AND success = 1 AND tweet_id IS NOT NULL ORDER BY posted_at DESC LIMIT 1",
                (account,)
            )
            result = cursor.fetchone()
            last_tweet_id = result[0] if result else None
            
            # Next scheduled run
            next_run = self.get_state(f"next_run_{account}")
            
            return {
                "posts_today": posts_today,
                "last_tweet_id": last_tweet_id,
                "next_run": next_run
            }

    async def get_last_post(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get the last post for an account."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT content, posted_at FROM posts WHERE account = ? AND success = 1 ORDER BY posted_at DESC LIMIT 1",
                (account_id,)
            )
            result = await cursor.fetchone()
            if result:
                return {
                    'content': result[0],
                    'timestamp': result[1]
                }
            return None
    
    async def get_recent_posts(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts for an account."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT tweet_id, content, posted_at FROM posts WHERE account = ? AND success = 1 ORDER BY posted_at DESC LIMIT ?",
                (account_id, limit)
            )
            results = await cursor.fetchall()
            return [
                {
                    'tweet_id': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                }
                for row in results
            ]
    
    async def get_total_posts(self, account_id: str) -> int:
        """Get total number of posts for an account."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM posts WHERE account = ? AND success = 1",
                (account_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_unique_hashtags(self, days: int = 7) -> List[str]:
        """Get unique hashtags used in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT DISTINCT hashtags FROM posts WHERE posted_at >= ? AND hashtags != ''",
                (cutoff_date,)
            )
            results = await cursor.fetchall()
            hashtags = set()
            for row in results:
                if row[0]:
                    hashtags.update(row[0].split())
            return sorted(list(hashtags))
    
    async def close(self):
        """Close database connections."""
        # Nothing to close for now as we use context managers
        pass
    
    async def get_reads_today(self) -> int:
        """Get number of API reads made today."""
        today = date.today()
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM api_reads WHERE date(created_at) = ? AND success = 1",
                (today,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def record_api_read(self, endpoint: str):
        """Record an API read operation."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_reads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    success BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute(
                "INSERT INTO api_reads (endpoint, success) VALUES (?, ?)",
                (endpoint, True)
            )
            await conn.commit()
