"""
Enhanced Tracker with Advanced Metrics and Controls
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import asyncio
from pathlib import Path
import sqlite3
import random
import uuid

class EnhancedTracker:
    """Advanced tracking and monitoring system"""
    
    def __init__(self, store, scheduler):
        self.app = FastAPI(title="VoltageGPU Bot Tracker")
        self.store = store
        self.scheduler = scheduler
        self.paused_accounts = set()
        self.cooldown_until = None
        self.setup_routes()
        
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/status")
        async def get_status():
            """Get comprehensive bot status"""
            return await self._get_full_status()
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get detailed metrics"""
            return await self._get_metrics()
        
        @self.app.get("/trends")
        async def get_trends():
            """Get current trend information"""
            return await self._get_trend_info()
        
        @self.app.get("/dry-run")
        async def dry_run(account: str = Query(..., regex="^(A|B|account_a|account_b)$")):
            """Preview next tweet without posting"""
            return await self._dry_run_tweet(account)
        
        @self.app.post("/pause")
        async def pause_account(account: str = Query(..., regex="^(A|B|all)$")):
            """Pause posting for specific account"""
            return await self._pause_account(account)
        
        @self.app.post("/resume")
        async def resume_account(account: str = Query(..., regex="^(A|B|all)$")):
            """Resume posting for specific account"""
            return await self._resume_account(account)
        
        @self.app.post("/cooldown")
        async def set_cooldown(minutes: int = Query(..., ge=1, le=1440)):
            """Set emergency cooldown period"""
            return await self._set_cooldown(minutes)
        
        @self.app.post("/next-run")
        async def advance_schedule(n: int = Query(1, ge=1, le=10)):
            """Advance schedule without posting (testing)"""
            return await self._advance_schedule(n)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    async def _get_full_status(self) -> Dict:
        """Get comprehensive status information"""
        
        # Get trend information
        trend_info = await self._get_trend_source_info()
        
        # Get account status
        account_a_status = await self._get_account_status("account_a")
        account_b_status = await self._get_account_status("account_b")
        
        # Get angle distribution
        angle_dist = self._get_angle_distribution()
        
        # Get CTR estimates (would need real data in production)
        ctr_by_angle = self._get_ctr_by_angle()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "mode": "PRODUCTION",
            "cooldown_active": self.cooldown_until is not None,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None,
            
            "accounts": {
                "A": account_a_status,
                "B": account_b_status
            },
            
            "trends": {
                "source": trend_info["source"],
                "age_minutes": trend_info["age_minutes"],
                "has_real_trend": trend_info["has_real_trend"],
                "top_trends": trend_info["top_trends"][:5],
                "relevance_scores": trend_info["relevance_scores"]
            },
            
            "angles": {
                "distribution_today": angle_dist,
                "ctr_last_7d": ctr_by_angle,
                "next_angle": self._get_next_angle()
            },
            
            "pricing": {
                "data_age_hours": self._get_price_age(),
                "using_fresh_prices": self._get_price_age() < 24 if self._get_price_age() else False
            },
            
            "performance": {
                "posts_today": self._get_posts_today(),
                "posts_this_week": self._get_posts_this_week(),
                "error_rate_24h": self._get_error_rate(),
                "avg_response_time_ms": self._get_avg_response_time()
            }
        }
    
    async def _get_metrics(self) -> Dict:
        """Get detailed performance metrics"""
        
        # Database metrics
        db_stats = self._get_database_stats()
        
        # Posting metrics
        posting_stats = self._get_posting_stats()
        
        # Engagement metrics (would need real data)
        engagement = self._get_engagement_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            
            "database": db_stats,
            "posting": posting_stats,
            "engagement": engagement,
            
            "system": {
                "uptime_hours": self._get_uptime(),
                "memory_usage_mb": self._get_memory_usage(),
                "cpu_percent": self._get_cpu_usage()
            }
        }
    
    async def _get_trend_info(self) -> Dict:
        """Get current trend information"""
        trend_data = await self._get_trend_source_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current_trends": trend_data["top_trends"],
            "source": trend_data["source"],
            "age_minutes": trend_data["age_minutes"],
            "relevance_scores": trend_data["relevance_scores"],
            "filters_applied": [
                "relevance_gating",
                "deduplication",
                "blacklist",
                "bridge_generation"
            ],
            "next_refresh": (datetime.now() + timedelta(minutes=20)).isoformat()
        }
    
    async def _dry_run_tweet(self, account: str) -> Dict:
        """Generate preview of next tweet without posting"""
        
        # Import necessary components
        from app.composer_optimized import OptimizedComposer
        from app.trends_filter import TrendFilter, PulsedTrendExtractor
        
        composer = OptimizedComposer()
        filter = TrendFilter()
        
        # Get current trends
        trends = await self._get_current_trends()
        
        # Filter and score
        filtered = await filter.filter_and_score(trends)
        
        if not filtered:
            return {
                "error": "No suitable trends available",
                "suggestion": "Wait for trend refresh or lower relevance threshold"
            }
        
        # Select best trend
        trend_data = filtered[0]
        
        # Compose tweet
        tweet = composer.compose_with_template(
            trend_data,
            account=account,
            use_price=True
        )
        
        # Validate
        validation = composer.validate_tweet(tweet)
        
        return {
            "preview": tweet,
            "length": len(tweet),
            "trend_used": trend_data["hashtag"],
            "relevance": trend_data["relevance"],
            "needs_bridge": trend_data.get("needs_bridge", False),
            "angle": composer.ANGLES[composer.angle_index],
            "validation": validation,
            "would_post": validation["all_valid"]
        }
    
    async def _pause_account(self, account: str) -> Dict:
        """Pause posting for account"""
        if account == "all":
            self.paused_accounts.update(["A", "B"])
            message = "All accounts paused"
        else:
            self.paused_accounts.add(account)
            message = f"Account {account} paused"
        
        return {
            "status": "success",
            "message": message,
            "paused_accounts": list(self.paused_accounts)
        }
    
    async def _resume_account(self, account: str) -> Dict:
        """Resume posting for account"""
        if account == "all":
            self.paused_accounts.clear()
            message = "All accounts resumed"
        else:
            self.paused_accounts.discard(account)
            message = f"Account {account} resumed"
        
        return {
            "status": "success",
            "message": message,
            "paused_accounts": list(self.paused_accounts)
        }
    
    async def _set_cooldown(self, minutes: int) -> Dict:
        """Set emergency cooldown"""
        self.cooldown_until = datetime.now() + timedelta(minutes=minutes)
        
        return {
            "status": "success",
            "message": f"Cooldown set for {minutes} minutes",
            "cooldown_until": self.cooldown_until.isoformat()
        }
    
    async def _advance_schedule(self, n: int) -> Dict:
        """Advance schedule for testing"""
        # This would interact with the scheduler
        # For now, return mock response
        return {
            "status": "success",
            "message": f"Advanced schedule by {n} slot(s)",
            "note": "Test mode - no tweets posted"
        }
    
    # Helper methods
    
    async def _get_trend_source_info(self) -> Dict:
        """Get information about trend sources"""
        # Check various trend cache files
        sources = []
        ages = []
        
        files = [
            ("data/pulsed_trends.json", "X_SEARCH"),
            ("data/realtime_trends.json", "PYTRENDS"),
            ("data/trends_cache.json", "SEMANTIC")
        ]
        
        for file_path, source_name in files:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                        if "timestamp" in data:
                            ts = datetime.fromisoformat(data["timestamp"])
                            age = (datetime.now() - ts).total_seconds() / 60
                            sources.append((source_name, age))
                            ages.append(age)
                except:
                    pass
        
        # Determine primary source
        if sources:
            sources.sort(key=lambda x: x[1])  # Sort by age
            primary_source = sources[0][0]
            min_age = sources[0][1]
        else:
            primary_source = "NONE"
            min_age = 999999
        
        # Load actual trends
        trends = []
        relevance_scores = {}
        
        try:
            # Try to load most recent trends
            for file_path, _ in files:
                path = Path(file_path)
                if path.exists():
                    with open(path) as f:
                        data = json.load(f)
                        if "trends" in data:
                            trends = data["trends"][:10]
                            break
        except:
            pass
        
        return {
            "source": primary_source,
            "age_minutes": int(min_age),
            "has_real_trend": min_age < 360,  # Less than 6 hours old
            "top_trends": trends,
            "relevance_scores": relevance_scores
        }
    
    async def _get_account_status(self, account: str) -> Dict:
        """Get status for specific account"""
        # Get from database
        posts_today = self._get_account_posts_today(account)
        last_post = self._get_last_post_time(account)
        
        # Calculate next run
        if last_post:
            next_run = last_post + timedelta(minutes=90)
        else:
            next_run = datetime.now()
        
        return {
            "paused": account in self.paused_accounts,
            "posts_today": posts_today,
            "posts_remaining": 10 - posts_today,
            "last_post": last_post.isoformat() if last_post else None,
            "next_run": next_run.isoformat(),
            "within_window": self._is_within_window()
        }
    
    def _get_angle_distribution(self) -> Dict[str, int]:
        """Get angle usage distribution"""
        try:
            path = Path("data/angle_stats.json")
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "cost": 0,
            "latency": 0,
            "autoscale": 0,
            "regions": 0,
            "uptime": 0,
            "support": 0
        }
    
    def _get_ctr_by_angle(self) -> Dict[str, float]:
        """Get CTR by angle (mock data for now)"""
        # In production, this would analyze UTM parameters
        return {
            "cost": 2.3,
            "latency": 2.8,
            "autoscale": 3.1,
            "regions": 2.5,
            "uptime": 2.2,
            "support": 2.6
        }
    
    def _get_next_angle(self) -> str:
        """Get next angle in rotation"""
        angles = ["cost", "latency", "autoscale", "regions", "uptime", "support"]
        dist = self._get_angle_distribution()
        
        # Find least used
        min_count = min(dist.values()) if dist else 0
        for angle in angles:
            if dist.get(angle, 0) == min_count:
                return angle
        
        return angles[0]
    
    def _get_price_age(self) -> Optional[float]:
        """Get age of price data in hours"""
        try:
            path = Path("data/offers.json")
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    ts = datetime.fromisoformat(data["timestamp"])
                    return (datetime.now() - ts).total_seconds() / 3600
        except:
            pass
        return None
    
    def _get_posts_today(self) -> int:
        """Get total posts today"""
        # Query database
        return self.store.get_daily_post_count()
    
    def _get_posts_this_week(self) -> int:
        """Get total posts this week"""
        # Query database for last 7 days
        return self.store.get_weekly_post_count()
    
    def _get_error_rate(self) -> float:
        """Get error rate in last 24 hours"""
        # Would analyze logs in production
        return 0.02  # 2% mock error rate
    
    def _get_avg_response_time(self) -> float:
        """Get average API response time"""
        # Would track actual response times
        return 245.6  # Mock 245ms
    
    def _get_database_stats(self) -> Dict:
        """Get database statistics"""
        return {
            "total_posts": self.store.get_total_posts(),
            "unique_tweets": self.store.get_unique_tweets(),
            "database_size_mb": self._get_db_size(),
            "last_cleanup": self.store.get_last_cleanup()
        }
    
    def _get_posting_stats(self) -> Dict:
        """Get posting statistics"""
        return {
            "total_posts_30d": self.store.get_posts_30d(),
            "avg_posts_per_day": self.store.get_avg_posts_per_day(),
            "peak_hour": self.store.get_peak_posting_hour(),
            "success_rate": 0.98  # 98% success rate
        }
    
    def _get_engagement_metrics(self) -> Dict:
        """Get engagement metrics (mock for now)"""
        return {
            "avg_impressions": 1250,
            "avg_engagements": 45,
            "avg_ctr": 2.4,
            "top_performing_angle": "autoscale",
            "top_performing_time": "14:00"
        }
    
    def _get_uptime(self) -> float:
        """Get system uptime in hours"""
        # Would track actual uptime
        return 168.5  # Mock 1 week uptime
    
    def _get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        import psutil
        return psutil.cpu_percent(interval=1)
    
    def _get_db_size(self) -> float:
        """Get database size in MB"""
        db_path = Path("data/bot.db")
        if db_path.exists():
            return db_path.stat().st_size / 1024 / 1024
        return 0
    
    def _is_within_window(self) -> bool:
        """Check if within posting window"""
        now = datetime.now()
        hour = now.hour + now.minute / 60
        return 9.0 <= hour <= 23.5
    
    def _get_account_posts_today(self, account: str) -> int:
        """Get posts today for specific account"""
        # Would query database
        return random.randint(3, 7)  # Mock data
    
    def _get_last_post_time(self, account: str) -> Optional[datetime]:
        """Get last post time for account"""
        # Would query database
        return datetime.now() - timedelta(minutes=random.randint(30, 120))
    
    async def _get_current_trends(self) -> List[str]:
        """Get current trends from cache"""
        trends = []
        
        files = [
            "data/pulsed_trends.json",
            "data/realtime_trends.json",
            "data/trends_cache.json"
        ]
        
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                        if "trends" in data:
                            trends = data["trends"]
                            break
                except:
                    pass
        
        return trends if trends else ["#AI", "#GPU", "#CloudCompute"]
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the tracker API"""
        import uvicorn
        await uvicorn.run(self.app, host=host, port=port)
