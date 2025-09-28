"""
Posting timer - Shows countdown to next posts for each account
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PostingTimer:
    """Displays countdown timers for next posts"""
    
    def __init__(self, scheduler, rate_limit_tracker=None):
        self.scheduler = scheduler
        self.rate_limit_tracker = rate_limit_tracker
        self.running = False
        
    async def start_timer_display(self, interval: int = 60):
        """Start displaying timer every interval seconds"""
        self.running = True
        
        while self.running:
            self.display_timers()
            await asyncio.sleep(interval)
    
    def display_timers(self):
        """Display current timers for both accounts"""
        now = datetime.now(self.scheduler.config.timezone)
        
        print("\n" + "="*70)
        print(f"⏰ POSTING SCHEDULE - {now.strftime('%H:%M:%S')}")
        print("="*70)
        
        # Get next run times
        next_runs = self.scheduler.get_next_run_times()
        
        # Display Account A
        self._display_account_timer('A', next_runs.get('A'), now)
        
        print()  # Separator
        
        # Display Account B
        self._display_account_timer('B', next_runs.get('B'), now)
        
        # Display rate limit info if available
        if self.rate_limit_tracker:
            self._display_rate_limit_info()
        
        print("="*70 + "\n")
    
    def _display_account_timer(self, account_id: str, next_run: Optional[datetime], now: datetime):
        """Display timer for a specific account"""
        
        # Check rate limit status first
        is_rate_limited = False
        rate_limit_reset = None
        
        if self.rate_limit_tracker:
            status = self.rate_limit_tracker.get_status()
            account_status = status['accounts'][account_id]
            
            if account_status['status'] == 'rate_limited':
                is_rate_limited = True
                if 'rate_limit_reset' in account_status:
                    rate_limit_reset = datetime.fromisoformat(account_status['rate_limit_reset'])
        
        # Display account header
        emoji = "🚫" if is_rate_limited else "✅"
        print(f"\n{emoji} ACCOUNT {account_id}:")
        
        # Display rate limit info if applicable
        if is_rate_limited and rate_limit_reset:
            time_until_reset = rate_limit_reset - now
            minutes_left = int(time_until_reset.total_seconds() / 60)
            seconds_left = int(time_until_reset.total_seconds() % 60)
            
            print(f"   ⚠️ RATE LIMITED - Reset in: {minutes_left}m {seconds_left}s")
            print(f"   📅 Reset time: {rate_limit_reset.strftime('%H:%M:%S')}")
            
            # Check if there's a retry scheduled
            jobs = self.scheduler.scheduler.get_jobs()
            retry_job = None
            for job in jobs:
                if f'rate_limit_retry_{account_id}' in job.id:
                    retry_job = job
                    break
            
            if retry_job and retry_job.next_run_time:
                print(f"   🔄 Auto-retry scheduled at: {retry_job.next_run_time.strftime('%H:%M:%S')}")
        
        # Display next regular post time
        if next_run:
            time_until_next = next_run - now
            
            if time_until_next.total_seconds() > 0:
                hours = int(time_until_next.total_seconds() // 3600)
                minutes = int((time_until_next.total_seconds() % 3600) // 60)
                seconds = int(time_until_next.total_seconds() % 60)
                
                # Format countdown
                if hours > 0:
                    countdown = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    countdown = f"{minutes}m {seconds}s"
                else:
                    countdown = f"{seconds}s"
                
                print(f"   ⏱️ Next post in: {countdown}")
                print(f"   📅 Scheduled for: {next_run.strftime('%H:%M:%S')}")
            else:
                print(f"   ⏱️ Post imminent!")
        else:
            print(f"   ❌ No posts scheduled")
        
        # Display daily stats
        daily_posts = self.scheduler.daily_posts.get(account_id, 0)
        daily_target = self.scheduler.config.daily_writes_target
        
        print(f"   📊 Today's posts: {daily_posts}/{daily_target}")
        
        # Display last post time
        last_post = self.scheduler.last_post_times.get(account_id)
        if last_post:
            time_since = now - last_post
            hours_ago = int(time_since.total_seconds() // 3600)
            minutes_ago = int((time_since.total_seconds() % 3600) // 60)
            
            if hours_ago > 0:
                ago_str = f"{hours_ago}h {minutes_ago}m ago"
            else:
                ago_str = f"{minutes_ago}m ago"
            
            print(f"   ✉️ Last post: {ago_str} ({last_post.strftime('%H:%M')})")
    
    def _display_rate_limit_info(self):
        """Display rate limit summary"""
        status = self.rate_limit_tracker.get_status()
        
        print("\n" + "-"*70)
        print("📊 RATE LIMIT STATUS:")
        
        for account_id in ['A', 'B']:
            account = status['accounts'][account_id]
            if account['status'] == 'rate_limited':
                print(f"   Account {account_id}: ⚠️ RATE LIMITED (resets in {account.get('minutes_until_reset', '?')} min)")
            else:
                print(f"   Account {account_id}: ✅ Ready ({account['posts_this_hour']}/50 this hour)")
    
    def stop(self):
        """Stop the timer display"""
        self.running = False


async def start_posting_timer(scheduler, rate_limit_tracker=None, interval: int = 60):
    """Start the posting timer in the background"""
    timer = PostingTimer(scheduler, rate_limit_tracker)
    
    # Run in background
    asyncio.create_task(timer.start_timer_display(interval))
    
    logger.info(f"Posting timer started (updates every {interval} seconds)")
    
    return timer
