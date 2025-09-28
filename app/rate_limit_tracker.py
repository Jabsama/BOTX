"""
Rate limit tracker for Twitter API
Tracks rate limits per account and provides visibility
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)


class RateLimitTracker:
    """Track and report rate limits for each Twitter account"""
    
    def __init__(self):
        self.limits = {
            'A': {
                'posts_today': 0,
                'posts_this_hour': 0,
                'last_post': None,
                'last_error': None,
                'rate_limit_reset': None,
                'status': 'ready'
            },
            'B': {
                'posts_today': 0,
                'posts_this_hour': 0,
                'last_post': None,
                'last_error': None,
                'rate_limit_reset': None,
                'status': 'ready'
            }
        }
        self.last_hour_reset = datetime.now()
        
    def record_post_attempt(self, account_id: str, success: bool, error_type: Optional[str] = None):
        """Record a post attempt and its result"""
        now = datetime.now()
        
        # Reset hourly counter if needed
        if now - self.last_hour_reset > timedelta(hours=1):
            for acc in self.limits:
                self.limits[acc]['posts_this_hour'] = 0
            self.last_hour_reset = now
        
        if success:
            self.limits[account_id]['posts_today'] += 1
            self.limits[account_id]['posts_this_hour'] += 1
            self.limits[account_id]['last_post'] = now
            self.limits[account_id]['status'] = 'ready'
            logger.info(f"✅ Account {account_id}: Post successful (Hour: {self.limits[account_id]['posts_this_hour']}/50, Day: {self.limits[account_id]['posts_today']}/300)")
        else:
            self.limits[account_id]['last_error'] = now
            
            if error_type == 'rate_limit':
                # Twitter rate limit is usually 15 minutes for posts
                reset_time = now + timedelta(minutes=15)
                self.limits[account_id]['rate_limit_reset'] = reset_time
                self.limits[account_id]['status'] = 'rate_limited'
                
                logger.warning(f"⚠️ Account {account_id}: RATE LIMITED until {reset_time.strftime('%H:%M:%S')}")
                logger.info(f"   Posts this hour: {self.limits[account_id]['posts_this_hour']}")
                logger.info(f"   Posts today: {self.limits[account_id]['posts_today']}")
            else:
                self.limits[account_id]['status'] = 'error'
                logger.error(f"❌ Account {account_id}: Post failed ({error_type})")
    
    def can_post(self, account_id: str) -> tuple[bool, str]:
        """Check if account can post and return reason if not"""
        now = datetime.now()
        account = self.limits[account_id]
        
        # Check rate limit reset
        if account['rate_limit_reset'] and now < account['rate_limit_reset']:
            time_left = (account['rate_limit_reset'] - now).total_seconds() / 60
            return False, f"Rate limited for {time_left:.1f} more minutes"
        
        # Check hourly limit (Twitter Free: ~50 posts/hour)
        if account['posts_this_hour'] >= 50:
            return False, f"Hourly limit reached ({account['posts_this_hour']}/50)"
        
        # Check daily limit (Twitter Free: ~300 posts/day)
        if account['posts_today'] >= 300:
            return False, f"Daily limit reached ({account['posts_today']}/300)"
        
        return True, "Ready to post"
    
    def get_status(self) -> Dict:
        """Get current status of all accounts"""
        now = datetime.now()
        status = {
            'timestamp': now.isoformat(),
            'accounts': {}
        }
        
        for account_id, data in self.limits.items():
            can_post, reason = self.can_post(account_id)
            
            account_status = {
                'can_post': can_post,
                'reason': reason,
                'posts_today': data['posts_today'],
                'posts_this_hour': data['posts_this_hour'],
                'status': data['status'],
                'last_post': data['last_post'].isoformat() if data['last_post'] else None,
                'last_error': data['last_error'].isoformat() if data['last_error'] else None
            }
            
            if data['rate_limit_reset'] and now < data['rate_limit_reset']:
                minutes_left = (data['rate_limit_reset'] - now).total_seconds() / 60
                account_status['rate_limit_reset'] = data['rate_limit_reset'].isoformat()
                account_status['minutes_until_reset'] = round(minutes_left, 1)
            
            status['accounts'][account_id] = account_status
        
        return status
    
    def print_status(self):
        """Print a formatted status report"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print(f"📊 RATE LIMIT STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        for account_id, data in status['accounts'].items():
            emoji = "✅" if data['can_post'] else "🚫"
            print(f"\n{emoji} Account {account_id}:")
            print(f"   Status: {data['status']}")
            print(f"   Can post: {data['reason']}")
            print(f"   Posts (hour/day): {data['posts_this_hour']}/50, {data['posts_today']}/300")
            
            if 'minutes_until_reset' in data:
                print(f"   ⏰ Rate limit resets in: {data['minutes_until_reset']} minutes")
            
            if data['last_post']:
                print(f"   Last successful post: {data['last_post']}")
            if data['last_error']:
                print(f"   Last error: {data['last_error']}")
        
        print("\n" + "="*60 + "\n")


# Global instance
rate_limit_tracker = RateLimitTracker()
