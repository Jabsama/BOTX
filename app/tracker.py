"""
Status tracker and HTTP API for monitoring bot operations.
Provides real-time status information and metrics.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import Config
from .store import Store
from .scheduler import PostScheduler
from .trends import TrendsManager

logger = logging.getLogger(__name__)


class StatusTracker:
    """Tracks and reports bot status and metrics."""
    
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self.scheduler = None
        self.trends_manager = None
        self.app = FastAPI(title="VoltageGPU Twitter Bot", version="1.0.0")
        self._setup_routes()
        self._setup_middleware()
        
    def set_components(self, scheduler: PostScheduler, trends_manager: TrendsManager):
        """Set references to other components."""
        self.scheduler = scheduler
        self.trends_manager = trends_manager
        
    def _setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "VoltageGPU Twitter Bot",
                "status": "running",
                "endpoints": [
                    "/status",
                    "/metrics",
                    "/posts/{account_id}",
                    "/trends",
                    "/health"
                ]
            }
        
        @self.app.get("/status")
        async def get_status():
            """Get comprehensive bot status."""
            try:
                status = await self._get_full_status()
                return JSONResponse(content=status)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get detailed metrics."""
            try:
                metrics = await self._get_metrics()
                return JSONResponse(content=metrics)
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/posts/{account_id}")
        async def get_account_posts(account_id: str):
            """Get recent posts for specific account."""
            if account_id not in ['A', 'B']:
                raise HTTPException(status_code=400, detail="Invalid account ID")
            
            try:
                posts = await self.store.get_recent_posts(account_id, limit=10)
                return JSONResponse(content={"account": account_id, "posts": posts})
            except Exception as e:
                logger.error(f"Error getting posts for account {account_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/trends")
        async def get_trends():
            """Get current trending hashtags."""
            try:
                if self.trends_manager:
                    samples = self.trends_manager.get_trend_samples()
                    return JSONResponse(content={"trends": samples})
                return JSONResponse(content={"trends": []})
            except Exception as e:
                logger.error(f"Error getting trends: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    async def _get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        now = datetime.now(self.config.timezone)
        
        # Get scheduler status
        scheduler_status = self.scheduler.get_status() if self.scheduler else {}
        
        # Get trend samples
        trend_samples = self.trends_manager.get_trend_samples() if self.trends_manager else []
        
        # Get recent posts for each account
        recent_posts = {}
        for account_id in ['A', 'B']:
            posts = await self.store.get_recent_posts(account_id, limit=1)
            if posts:
                recent_posts[account_id] = {
                    'last_tweet_id': posts[0].get('tweet_id'),
                    'last_post_time': posts[0].get('timestamp'),
                    'content_preview': posts[0].get('content', '')[:100] + '...'
                }
            else:
                recent_posts[account_id] = {
                    'last_tweet_id': None,
                    'last_post_time': None,
                    'content_preview': None
                }
        
        # Build status response
        status = {
            'now': now.isoformat(),
            'timezone': str(self.config.timezone),
            'account_a': {
                'next_run_local': scheduler_status.get('account_a', {}).get('next_run'),
                'posted_today': scheduler_status.get('account_a', {}).get('posted_today', 0),
                'last_tweet_id': recent_posts['A']['last_tweet_id'],
                'last_post_time': recent_posts['A']['last_post_time']
            },
            'account_b': {
                'next_run_local': scheduler_status.get('account_b', {}).get('next_run'),
                'posted_today': scheduler_status.get('account_b', {}).get('posted_today', 0),
                'last_tweet_id': recent_posts['B']['last_tweet_id'],
                'last_post_time': recent_posts['B']['last_post_time']
            },
            'trend_samples': trend_samples,
            'writes_budget_today': {
                'A': scheduler_status.get('account_a', {}).get('posted_today', 0),
                'B': scheduler_status.get('account_b', {}).get('posted_today', 0),
                'target': self.config.daily_writes_target
            },
            'posting_window': scheduler_status.get('posting_window', 'Not configured'),
            'scheduler_running': scheduler_status.get('scheduler_running', False)
        }
        
        return status
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics."""
        # Get post counts
        total_posts_a = await self.store.get_total_posts('A')
        total_posts_b = await self.store.get_total_posts('B')
        
        # Get today's posts
        today_posts_a = await self.store.get_posts_today('A')
        today_posts_b = await self.store.get_posts_today('B')
        
        # Get unique hashtags used
        unique_hashtags = await self.store.get_unique_hashtags(days=7)
        
        metrics = {
            'total_posts': {
                'A': total_posts_a,
                'B': total_posts_b,
                'combined': total_posts_a + total_posts_b
            },
            'posts_today': {
                'A': today_posts_a,
                'B': today_posts_b,
                'combined': today_posts_a + today_posts_b
            },
            'unique_hashtags_7d': len(unique_hashtags),
            'top_hashtags_7d': unique_hashtags[:10] if unique_hashtags else [],
            'uptime_hours': self._calculate_uptime(),
            'database_size_mb': self._get_database_size()
        }
        
        return metrics
    
    def _calculate_uptime(self) -> float:
        """Calculate bot uptime in hours."""
        # This would need to track start time in production
        # For now, return 0
        return 0.0
    
    def _get_database_size(self) -> float:
        """Get database file size in MB."""
        try:
            db_path = Path(self.store.db_path)
            if db_path.exists():
                size_bytes = db_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            pass
        return 0.0
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server."""
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def log_status(self):
        """Log current status to file and console."""
        try:
            status = await self._get_full_status()
            
            # Log to console
            logger.info("=== Bot Status ===")
            logger.info(f"Time: {status['now']}")
            logger.info(f"Account A - Next: {status['account_a']['next_run_local']}, "
                       f"Posted: {status['account_a']['posted_today']}")
            logger.info(f"Account B - Next: {status['account_b']['next_run_local']}, "
                       f"Posted: {status['account_b']['posted_today']}")
            logger.info(f"Trends: {', '.join(status['trend_samples'][:3])}")
            
            # Log to JSON file
            log_path = Path('data/log.jsonl')
            log_path.parent.mkdir(exist_ok=True)
            
            with open(log_path, 'a') as f:
                json.dump({
                    'timestamp': status['now'],
                    'type': 'status',
                    'data': status
                }, f)
                f.write('\n')
                
        except Exception as e:
            logger.error(f"Error logging status: {e}")


class JSONLogger:
    """JSON logger for structured logging."""
    
    def __init__(self, log_file: str = 'data/log.jsonl'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
    def log(self, level: str, message: str, **kwargs):
        """Log a message with additional data."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        
        try:
            with open(self.log_file, 'a') as f:
                json.dump(entry, f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write to JSON log: {e}")
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log('INFO', message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log('ERROR', message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log('WARNING', message, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log('DEBUG', message, **kwargs)


# Global JSON logger instance
json_logger = JSONLogger()
