"""
Scheduler module for managing A/B account posting cadence.
Ensures strict timing: A posts first, B follows 45 minutes later, both repeat every 90 minutes.
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, Optional, List, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import pytz

from .config import Config
from .store import Store
from .composer import TweetComposer
from .twitter_client import TwitterClient
from .trends import TrendsManager

logger = logging.getLogger(__name__)


class PostScheduler:
    """Manages posting schedule for dual Twitter accounts."""
    
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self.scheduler = AsyncIOScheduler(timezone=config.timezone)
        self.twitter_clients = {}
        self.composer = None
        self.trends_manager = None
        self.posting_lock = asyncio.Lock()
        self.last_post_times = {'A': None, 'B': None}
        self.daily_posts = {'A': 0, 'B': 0}
        self.last_reset_date = None
        
    def initialize(self, twitter_clients: Dict[str, TwitterClient], 
                  composer: TweetComposer, trends_manager: TrendsManager):
        """Initialize scheduler with required components."""
        self.twitter_clients = twitter_clients
        self.composer = composer
        self.trends_manager = trends_manager
        
    async def start(self):
        """Start the scheduler with proper A/B timing."""
        try:
            # Reset daily counters if needed
            await self._reset_daily_counters()
            
            # Schedule trend refresh job (every 20 minutes)
            self.scheduler.add_job(
                self.trends_manager.refresh_trends,
                IntervalTrigger(minutes=20),
                id='refresh_trends',
                name='Refresh Trends',
                replace_existing=True
            )
            
            # Schedule daily counter reset at midnight
            self.scheduler.add_job(
                self._reset_daily_counters,
                'cron',
                hour=0,
                minute=0,
                id='reset_daily',
                name='Reset Daily Counters',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            
            # Initial trend refresh
            await self.trends_manager.refresh_trends()
            
            # Schedule initial posts
            await self._schedule_initial_posts()
            
            logger.info("Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    async def _schedule_initial_posts(self):
        """Schedule initial posts for both accounts."""
        now = datetime.now(self.config.timezone)
        
        # Check if we're within posting window
        if not self._is_within_window(now):
            # Find next valid window start
            next_window = self._get_next_window_start(now)
            logger.info(f"Outside posting window. Next window starts at {next_window}")
            
            # Schedule A for window start
            self.scheduler.add_job(
                self._post_for_account,
                DateTrigger(run_date=next_window),
                args=['A'],
                id='initial_post_A',
                name='Initial Post A',
                replace_existing=True
            )
            
            # Schedule B for 45 minutes after A
            b_time = next_window + timedelta(minutes=self.config.min_gap_between_accounts)
            self.scheduler.add_job(
                self._post_for_account,
                DateTrigger(run_date=b_time),
                args=['B'],
                id='initial_post_B',
                name='Initial Post B',
                replace_existing=True
            )
        else:
            # We're within window, post A immediately
            logger.info("Within posting window. Scheduling immediate post for Account A")
            
            # Post A immediately
            asyncio.create_task(self._post_for_account('A'))
            
            # Schedule B for 45 minutes later
            b_time = now + timedelta(minutes=self.config.min_gap_between_accounts)
            if self._is_within_window(b_time):
                self.scheduler.add_job(
                    self._post_for_account,
                    DateTrigger(run_date=b_time),
                    args=['B'],
                    id='initial_post_B',
                    name='Initial Post B',
                    replace_existing=True
                )
            else:
                # B would be outside window, schedule for next window
                next_window = self._get_next_window_start(b_time)
                self.scheduler.add_job(
                    self._post_for_account,
                    DateTrigger(run_date=next_window),
                    args=['B'],
                    id='initial_post_B',
                    name='Initial Post B',
                    replace_existing=True
                )
        
        # Schedule recurring posts
        self._schedule_recurring_posts()
    
    def _schedule_recurring_posts(self):
        """Schedule recurring posts for both accounts."""
        # Schedule A to post every 90 minutes
        self.scheduler.add_job(
            self._post_for_account,
            IntervalTrigger(minutes=self.config.post_interval_minutes),
            args=['A'],
            id='recurring_post_A',
            name='Recurring Post A',
            replace_existing=True,
            misfire_grace_time=60
        )
        
        # Schedule B to post every 90 minutes (offset by 45 minutes from A)
        self.scheduler.add_job(
            self._post_for_account,
            IntervalTrigger(
                minutes=self.config.post_interval_minutes,
                start_date=datetime.now(self.config.timezone) + timedelta(
                    minutes=self.config.min_gap_between_accounts
                )
            ),
            args=['B'],
            id='recurring_post_B',
            name='Recurring Post B',
            replace_existing=True,
            misfire_grace_time=60
        )
    
    async def _post_for_account(self, account_id: str):
        """Execute a post for the specified account."""
        async with self.posting_lock:
            try:
                now = datetime.now(self.config.timezone)
                
                # Check if within posting window
                if not self._is_within_window(now):
                    logger.info(f"Account {account_id}: Outside posting window, skipping")
                    return
                
                # Check daily limit
                if self.daily_posts[account_id] >= self.config.daily_writes_target:
                    logger.info(f"Account {account_id}: Daily limit reached ({self.daily_posts[account_id]})")
                    return
                
                # Check minimum gap between accounts
                other_account = 'B' if account_id == 'A' else 'A'
                if self.last_post_times.get(other_account):
                    time_since_other = (now - self.last_post_times[other_account]).total_seconds() / 60
                    if time_since_other < self.config.min_gap_between_accounts:
                        wait_time = self.config.min_gap_between_accounts - time_since_other
                        logger.info(f"Account {account_id}: Too soon after {other_account}, waiting {wait_time:.1f} minutes")
                        await asyncio.sleep(wait_time * 60)
                
                # Compose tweet
                logger.info(f"Account {account_id}: Composing tweet")
                tweet_content = await self.composer.compose_tweet(account_id)
                
                if not tweet_content:
                    logger.error(f"Account {account_id}: Failed to compose tweet")
                    return
                
                # Post tweet
                client = self.twitter_clients.get(account_id)
                if not client:
                    logger.error(f"Account {account_id}: No Twitter client available")
                    return
                
                logger.info(f"Account {account_id}: Posting tweet ({len(tweet_content)} chars)")
                tweet_id = await client.post_tweet(tweet_content)
                
                if tweet_id:
                    # Update tracking
                    self.last_post_times[account_id] = now
                    self.daily_posts[account_id] += 1
                    
                    # Store in database
                    await self.store.record_post(
                        account_id=account_id,
                        tweet_id=tweet_id,
                        content=tweet_content,
                        hashtags=self._extract_hashtags(tweet_content)
                    )
                    
                    logger.info(f"Account {account_id}: Successfully posted tweet {tweet_id}")
                    logger.info(f"Account {account_id}: Daily posts: {self.daily_posts[account_id]}/{self.config.daily_writes_target}")
                else:
                    logger.error(f"Account {account_id}: Failed to post tweet")
                    
            except Exception as e:
                logger.error(f"Account {account_id}: Error during posting: {e}")
    
    def _is_within_window(self, dt: datetime) -> bool:
        """Check if datetime is within posting window."""
        current_time = dt.time()
        return self.config.post_window_start <= current_time <= self.config.post_window_end
    
    def _get_next_window_start(self, from_time: datetime) -> datetime:
        """Get the next window start time."""
        next_day = from_time.date() + timedelta(days=1)
        return self.config.timezone.localize(
            datetime.combine(next_day, self.config.post_window_start)
        )
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from tweet content."""
        import re
        return re.findall(r'#\w+', content)
    
    async def _reset_daily_counters(self):
        """Reset daily post counters."""
        today = datetime.now(self.config.timezone).date()
        
        if self.last_reset_date != today:
            self.daily_posts = {'A': 0, 'B': 0}
            self.last_reset_date = today
            logger.info(f"Daily counters reset for {today}")
    
    def get_next_run_times(self) -> Dict[str, Optional[datetime]]:
        """Get next scheduled run times for each account."""
        next_runs = {'A': None, 'B': None}
        
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if 'post_A' in job.id and job.next_run_time:
                if not next_runs['A'] or job.next_run_time < next_runs['A']:
                    next_runs['A'] = job.next_run_time
            elif 'post_B' in job.id and job.next_run_time:
                if not next_runs['B'] or job.next_run_time < next_runs['B']:
                    next_runs['B'] = job.next_run_time
        
        return next_runs
    
    def get_status(self) -> Dict:
        """Get current scheduler status."""
        next_runs = self.get_next_run_times()
        
        return {
            'scheduler_running': self.scheduler.running,
            'account_a': {
                'next_run': next_runs['A'].isoformat() if next_runs['A'] else None,
                'posted_today': self.daily_posts['A'],
                'last_post_time': self.last_post_times['A'].isoformat() if self.last_post_times['A'] else None
            },
            'account_b': {
                'next_run': next_runs['B'].isoformat() if next_runs['B'] else None,
                'posted_today': self.daily_posts['B'],
                'last_post_time': self.last_post_times['B'].isoformat() if self.last_post_times['B'] else None
            },
            'daily_target': self.config.daily_writes_target,
            'posting_window': f"{self.config.post_window_start} - {self.config.post_window_end}"
        }
    
    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
