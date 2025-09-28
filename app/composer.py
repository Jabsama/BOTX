"""
Tweet composition module for dynamic content generation.
Creates engaging, trend-aware promotional content for VoltageGPU.
"""

import random
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from langdetect import detect, LangDetectException

from .config import Config
from .store import Store
from .trends import TrendsManager

# Import realtime trends extractor and viral composer
try:
    from .trends_realtime import RealtimeTrendsExtractor
    from .composer_viral import ViralTweetComposer, SmartTweetOptimizer
except ImportError:
    RealtimeTrendsExtractor = None
    ViralTweetComposer = None
    SmartTweetOptimizer = None

logger = logging.getLogger(__name__)


class TweetComposer:
    """Composes dynamic, trend-aware tweets for VoltageGPU promotion."""
    
    PROMO_CODE = "SHA-256-C7E8976BBAF2"
    BASE_URL = "https://voltagegpu.com"
    
    # Dynamic promotional angles (no hardcoded content)
    PROMO_ANGLES = [
        {
            'focus': 'performance',
            'keywords': ['blazing fast', 'ultra-low latency', 'high-performance', 'instant deployment'],
            'benefits': ['10x faster inference', 'sub-second spin-up', 'zero queue time']
        },
        {
            'focus': 'cost',
            'keywords': ['affordable', 'cost-effective', 'save money', 'budget-friendly'],
            'benefits': ['70% cheaper than competitors', 'pay only for what you use', 'no hidden fees']
        },
        {
            'focus': 'scalability',
            'keywords': ['auto-scaling', 'elastic compute', 'grow seamlessly', 'infinite scale'],
            'benefits': ['scale from 1 to 1000 GPUs', 'automatic load balancing', 'global availability']
        },
        {
            'focus': 'reliability',
            'keywords': ['99.99% uptime', 'enterprise-grade', 'always available', 'rock-solid'],
            'benefits': ['redundant infrastructure', '24/7 monitoring', 'instant failover']
        },
        {
            'focus': 'innovation',
            'keywords': ['cutting-edge', 'next-gen', 'revolutionary', 'game-changing'],
            'benefits': ['latest GPU models', 'AI-optimized infrastructure', 'future-proof platform']
        },
        {
            'focus': 'support',
            'keywords': ['24/7 support', 'expert assistance', 'dedicated team', 'white-glove service'],
            'benefits': ['instant chat support', 'dedicated account manager', 'free onboarding']
        }
    ]
    
    def __init__(self, config: Config, store: Store, trends_manager: TrendsManager):
        self.config = config
        self.store = store
        self.trends_manager = trends_manager
        self.last_angles = {'A': None, 'B': None}
        # Initialize realtime trends extractor
        self.realtime_trends = RealtimeTrendsExtractor() if RealtimeTrendsExtractor else None
        # Initialize viral composer
        self.viral_composer = ViralTweetComposer() if ViralTweetComposer else None
        self.optimizer = SmartTweetOptimizer() if SmartTweetOptimizer else None
        
    async def compose_tweet(self, account_id: str) -> Optional[str]:
        """
        Compose a unique, trend-aware tweet for the specified account.
        Returns None if unable to compose or if duplicate detected.
        """
        try:
            # Get REAL worldwide trending hashtags
            hashtags = []
            
            # Try to get realtime trends first
            if self.realtime_trends:
                try:
                    worldwide_trends = await self.realtime_trends.get_worldwide_trends()
                    if worldwide_trends:
                        # Pick 2-3 random trending hashtags
                        hashtags = random.sample(worldwide_trends, min(3, len(worldwide_trends)))
                        logger.info(f"Using realtime trends for {account_id}: {', '.join(hashtags)}")
                except Exception as e:
                    logger.warning(f"Could not get realtime trends: {e}")
            
            # Fallback to original trends manager if needed
            if not hashtags:
                hashtags = await self.trends_manager.get_trending_hashtags(count=2)
            
            # Use viral composer if available
            if self.viral_composer and hashtags:
                try:
                    viral_tweet = await self.viral_composer.compose_viral_tweet(hashtags)
                    if self.optimizer:
                        viral_tweet = self.optimizer.optimize_for_engagement(viral_tweet)
                    
                    # Validate the viral tweet
                    if self._validate_tweet(viral_tweet):
                        logger.info(f"Using viral tweet for account {account_id}: {len(viral_tweet)} chars")
                        return viral_tweet
                except Exception as e:
                    logger.warning(f"Viral composer failed, falling back to standard: {e}")
            
            # Fallback to standard composition
            # Select promotional angle (different from last used)
            angle = self._select_angle(account_id)
            
            # Generate hook based on trends
            hook = self._generate_hook(hashtags, angle)
            
            # Generate promise/benefit
            promise = self._generate_promise(angle)
            
            # Generate CTA
            cta = self._generate_cta()
            
            # Build UTM parameters
            utm_params = self._build_utm_params(account_id, hashtags)
            
            # Construct full URL
            full_url = f"{self.BASE_URL}/?{utm_params}"
            
            # Required components
            promo_line = f"EXCLUSIVE PROMO CODE {self.PROMO_CODE}"
            
            # Assemble tweet with character limit consideration
            tweet_parts = [
                hook,
                promise,
                cta,
                promo_line,
                full_url
            ]
            
            # Add hashtags if space allows
            hashtag_str = ' '.join(hashtags) if hashtags else ''
            
            # Build tweet
            tweet = self._assemble_tweet(tweet_parts, hashtag_str)
            
            # Validate tweet
            if not self._validate_tweet(tweet):
                logger.warning(f"Tweet validation failed for account {account_id}")
                return None
            
            # Check for duplicates
            if await self.store.is_duplicate_content(tweet):
                logger.info(f"Duplicate content detected for account {account_id}, regenerating")
                # Try once more with different angle
                return await self._regenerate_tweet(account_id)
            
            # Ensure sufficient difference between accounts
            if not await self._ensure_account_diversity(account_id, tweet):
                logger.info(f"Insufficient diversity for account {account_id}, regenerating")
                return await self._regenerate_tweet(account_id)
            
            logger.info(f"Composed tweet for account {account_id}: {len(tweet)} chars")
            return tweet
            
        except Exception as e:
            logger.error(f"Error composing tweet for account {account_id}: {e}")
            return None
    
    def _select_angle(self, account_id: str) -> Dict:
        """Select a promotional angle different from the last used."""
        available_angles = [a for a in self.PROMO_ANGLES 
                           if a != self.last_angles.get(account_id)]
        
        if not available_angles:
            available_angles = self.PROMO_ANGLES
        
        angle = random.choice(available_angles)
        self.last_angles[account_id] = angle
        return angle
    
    def _generate_hook(self, hashtags: List[str], angle: Dict) -> str:
        """Generate an engaging hook that ties to current trends."""
        hooks = []
        
        # Trend-aware hooks
        if hashtags:
            trend_word = hashtags[0].replace('#', '') if hashtags else 'Tech'
            hooks.extend([
                f"Riding the {trend_word} wave?",
                f"{trend_word} professionals are switching to VoltageGPU",
                f"The {trend_word} community's GPU secret",
                f"Why {trend_word} leaders choose VoltageGPU"
            ])
        
        # Angle-specific hooks
        if angle['focus'] == 'performance':
            hooks.extend([
                "Need GPUs that actually deliver?",
                "Tired of waiting for GPU allocation?",
                "Your models deserve better performance"
            ])
        elif angle['focus'] == 'cost':
            hooks.extend([
                "GPU costs eating your budget?",
                "Premium GPUs without premium prices",
                "Smart teams save on compute"
            ])
        elif angle['focus'] == 'scalability':
            hooks.extend([
                "Scale your AI without limits",
                "From prototype to production instantly",
                "Growing fast? We scale faster"
            ])
        elif angle['focus'] == 'reliability':
            hooks.extend([
                "When downtime isn't an option",
                "Enterprise reliability for everyone",
                "Your models run 24/7/365"
            ])
        elif angle['focus'] == 'innovation':
            hooks.extend([
                "The future of GPU compute is here",
                "Next-gen infrastructure today",
                "Innovate faster with VoltageGPU"
            ])
        elif angle['focus'] == 'support':
            hooks.extend([
                "Never debug alone again",
                "Expert support when you need it",
                "Your success is our mission"
            ])
        
        return random.choice(hooks)
    
    def _generate_promise(self, angle: Dict) -> str:
        """Generate a compelling promise based on the angle."""
        benefit = random.choice(angle['benefits'])
        keyword = random.choice(angle['keywords'])
        
        templates = [
            f"Get {benefit} with our {keyword} platform.",
            f"Experience {benefit} - {keyword} guaranteed.",
            f"{benefit.capitalize()}. That's the VoltageGPU difference.",
            f"Join thousands enjoying {benefit}.",
            f"Why settle for less? {benefit.capitalize()} with VoltageGPU."
        ]
        
        return random.choice(templates)
    
    def _generate_cta(self) -> str:
        """Generate a call-to-action."""
        ctas = [
            "Start free today!",
            "Try it now!",
            "Get started →",
            "Launch in seconds!",
            "Claim your GPUs!",
            "Deploy instantly!",
            "Scale up now!",
            "Join us today!"
        ]
        return random.choice(ctas)
    
    def _build_utm_params(self, account_id: str, hashtags: List[str]) -> str:
        """Build UTM parameters for tracking."""
        account_name = 'account_a' if account_id == 'A' else 'account_b'
        hashtag_str = '_'.join(h.replace('#', '') for h in hashtags[:2]) if hashtags else 'organic'
        
        params = {
            'utm_source': 'twitter',
            'utm_medium': 'social',
            'utm_campaign': f'promo_{self.PROMO_CODE}',
            'utm_content': account_name,
            'utm_term': hashtag_str
        }
        
        return '&'.join(f"{k}={v}" for k, v in params.items())
    
    def _assemble_tweet(self, parts: List[str], hashtags: str) -> str:
        """Assemble tweet parts while respecting character limit."""
        # ALWAYS include hashtags - they are essential!
        # Build tweet with hashtags FIRST
        if hashtags:
            # Put hashtags at the beginning or end
            base_parts = parts[:-1]  # Everything except URL
            url = parts[-1]  # URL should be last
            
            # Try hashtags at the beginning
            tweet_with_tags_start = f"{hashtags} {' '.join(base_parts)} {url}"
            
            # Try hashtags at the end  
            tweet_with_tags_end = f"{' '.join(base_parts)} {hashtags} {url}"
            
            # Choose the shorter one
            if len(tweet_with_tags_start) <= 280:
                tweet = tweet_with_tags_start
            elif len(tweet_with_tags_end) <= 280:
                tweet = tweet_with_tags_end
            else:
                # Need to shorten content to fit hashtags
                # Reduce the promise/hook to make room
                shortened_parts = [
                    parts[0][:50],  # Shorten hook
                    parts[1][:40],  # Shorten promise  
                    parts[2],       # Keep CTA
                    parts[3],       # Keep promo code
                ]
                tweet = f"{hashtags} {' '.join(shortened_parts)} {url}"
                
                # Final check
                if len(tweet) > 280:
                    # Emergency shortening - keep hashtags no matter what
                    tweet = f"{hashtags} GPU power on demand! {parts[3]} {url}"[:280]
        else:
            # No hashtags (shouldn't happen)
            tweet = ' '.join(parts)
        
        # Final safety check
        if len(tweet) > 280:
            # Preserve hashtags and URL at minimum
            if hashtags in tweet:
                # Keep hashtags intact
                tweet = tweet[:277] + "..."
            else:
                tweet = tweet[:277] + "..."
        
        return tweet
    
    def _validate_tweet(self, tweet: str) -> bool:
        """Validate tweet meets all requirements."""
        if not tweet:
            return False
        
        # Check length
        if len(tweet) > 280 or len(tweet) < 50:
            return False
        
        # Check for required elements
        if self.PROMO_CODE not in tweet:
            return False
        
        if self.BASE_URL not in tweet:
            return False
        
        # Check language (must be English)
        try:
            if detect(tweet) != 'en':
                return False
        except LangDetectException:
            # If detection fails, assume it's okay
            pass
        
        # Check for excessive caps (spam indicator)
        caps_ratio = sum(1 for c in tweet if c.isupper()) / len(tweet)
        if caps_ratio > 0.3:
            return False
        
        # Check hashtag count (max 3)
        hashtag_count = tweet.count('#')
        if hashtag_count > 3:
            return False
        
        return True
    
    async def _ensure_account_diversity(self, account_id: str, tweet: str) -> bool:
        """Ensure sufficient difference between account A and B posts."""
        # Get recent post from other account
        other_account = 'B' if account_id == 'A' else 'A'
        recent_other = await self.store.get_last_post(other_account)
        
        if not recent_other or not recent_other.get('content'):
            return True
        
        # Calculate similarity (simple word overlap)
        words1 = set(re.findall(r'\w+', tweet.lower()))
        words2 = set(re.findall(r'\w+', recent_other['content'].lower()))
        
        # Remove common words and URLs
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                       'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 
                       'was', 'were', 'been', 'be', 'have', 'has', 'had',
                       'exclusive', 'promo', 'code', 'sha', '256', 'c7e8976bbaf2',
                       'voltagegpu', 'com', 'https', 'utm'}
        
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return True
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        similarity = intersection / union if union > 0 else 0
        
        # Require less than 20% similarity
        return similarity < 0.2
    
    async def _regenerate_tweet(self, account_id: str) -> Optional[str]:
        """Regenerate tweet with different parameters."""
        # Reset angle to force different selection
        self.last_angles[account_id] = None
        
        # Try up to 3 times
        for _ in range(3):
            tweet = await self.compose_tweet(account_id)
            if tweet:
                return tweet
        
        return None
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash of content for duplicate detection."""
        # Normalize content (remove URLs and promo code for comparison)
        normalized = re.sub(r'https?://\S+', '', content)
        normalized = normalized.replace(self.PROMO_CODE, '')
        normalized = re.sub(r'\s+', ' ', normalized.lower().strip())
        
        return hashlib.sha256(normalized.encode()).hexdigest()
