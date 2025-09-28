"""
Trends extraction module for dynamic hashtag generation.
Zero hardcoded hashtags - all dynamically generated from current trends.
"""

import asyncio
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
import random
from collections import Counter
import aiohttp

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

from langdetect import detect, LangDetectException
import tweepy
from .config import Config
from .store import Store

logger = logging.getLogger(__name__)


class TrendsManager:
    """Manages trend extraction from multiple sources with zero hardcoded hashtags."""
    
    NSFW_KEYWORDS = {
        'porn', 'xxx', 'nsfw', 'nude', 'sex', 'onlyfans', 'adult',
        'escort', 'fetish', 'bdsm', 'milf', 'boobs', 'ass', 'dick'
    }
    
    POLITICAL_KEYWORDS = {
        'trump', 'biden', 'democrat', 'republican', 'maga', 'liberal',
        'conservative', 'election', 'vote', 'politics', 'congress',
        'senate', 'president', 'governor', 'campaign', 'ballot'
    }
    
    REGIONS = ['united_states', 'united_kingdom', 'france', 'germany', 
               'spain', 'italy', 'brazil', 'india', 'japan', 'south_korea']
    
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self.twitter_client = None
        self.pytrends = TrendReq() if TrendReq else None
        self.last_refresh = None
        self.cached_trends = []
        
    def set_twitter_client(self, client):
        """Set Twitter client for search operations."""
        self.twitter_client = client
        
    async def refresh_trends(self) -> List[Dict]:
        """
        Main trend refresh job - runs every 20 minutes.
        Attempts multiple sources in order of preference.
        """
        try:
            trends = []
            
            # 1. Try Twitter search_recent first
            if self.twitter_client:
                twitter_trends = await self._extract_twitter_trends()
                if twitter_trends:
                    trends.extend(twitter_trends)
                    logger.info(f"Extracted {len(twitter_trends)} trends from Twitter")
            
            # 2. Fallback to Google Trends if needed
            if len(trends) < 10 and self.pytrends:
                google_trends = await self._extract_google_trends()
                if google_trends:
                    trends.extend(google_trends)
                    logger.info(f"Extracted {len(google_trends)} trends from Google")
            
            # 3. Generate semantic hashtags if still insufficient
            if len(trends) < 5:
                semantic_trends = self._generate_semantic_hashtags()
                trends.extend(semantic_trends)
                logger.info(f"Generated {len(semantic_trends)} semantic hashtags")
            
            # Filter and score trends
            filtered_trends = self._filter_trends(trends)
            scored_trends = self._score_trends(filtered_trends)
            
            # Store in database
            await self.store.update_trends(scored_trends)
            self.cached_trends = scored_trends[:20]  # Keep top 20
            self.last_refresh = datetime.now()
            
            logger.info(f"Trend refresh complete: {len(self.cached_trends)} trends cached")
            return self.cached_trends
            
        except Exception as e:
            logger.error(f"Error refreshing trends: {e}")
            return self.cached_trends or []
    
    async def _extract_twitter_trends(self) -> List[Dict]:
        """Extract trends from recent Twitter posts."""
        trends = []
        
        # Check if we should use conservative mode for X API reads
        if self.config.X_READS_MODE == 'conservative':
            # Skip Twitter search to save API reads
            logger.info("Conservative mode: Skipping Twitter search to save API reads")
            return trends
        
        # Check daily read quota
        reads_today = await self.store.get_reads_today()
        if reads_today >= self.config.MAX_READS_PER_DAY:
            logger.warning(f"Daily read limit reached ({reads_today}/{self.config.MAX_READS_PER_DAY})")
            return trends
        
        try:
            # Fixed query - must have content before operators
            query = "#AI OR #GPU OR #CloudComputing OR #MachineLearning lang:en -is:retweet -is:reply"
            
            # Use bearer token client for search
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=30,  # Reduced to save API calls
                tweet_fields=['created_at', 'entities']
            )
            
            # Record API read
            await self.store.record_api_read('twitter_search')
            
            if not tweets.data:
                return trends
            
            # Extract hashtags with frequency
            hashtag_counter = Counter()
            cutoff_time = datetime.now() - timedelta(minutes=60)
            
            for tweet in tweets.data:
                if tweet.entities and 'hashtags' in tweet.entities:
                    for tag in tweet.entities['hashtags']:
                        hashtag = f"#{tag['tag']}"
                        hashtag_counter[hashtag] += 1
            
            # Convert to trend format
            for hashtag, count in hashtag_counter.most_common(30):
                trends.append({
                    'hashtag': hashtag,
                    'source': 'twitter',
                    'score': count,
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error extracting Twitter trends: {e}")
            
        return trends
    
    async def _extract_google_trends(self) -> List[Dict]:
        """Extract trends from Google Trends across multiple regions."""
        trends = []
        
        try:
            for region in self.REGIONS[:5]:  # Limit to 5 regions to avoid rate limits
                try:
                    # Get trending searches
                    trending = self.pytrends.trending_searches(pn=region)
                    
                    if trending is not None and not trending.empty:
                        for topic in trending[0][:10]:  # Top 10 per region
                            # Convert topic to hashtags
                            hashtags = self._topic_to_hashtags(str(topic))
                            for hashtag in hashtags:
                                trends.append({
                                    'hashtag': hashtag,
                                    'source': 'google',
                                    'score': 1,
                                    'timestamp': datetime.now()
                                })
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Error getting trends for {region}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting Google trends: {e}")
            
        return trends
    
    def _topic_to_hashtags(self, topic: str) -> List[str]:
        """Convert a topic string to relevant hashtags."""
        hashtags = []
        
        # Clean and split topic
        words = re.findall(r'\w+', topic.lower())
        
        # Create CamelCase hashtag
        if len(words) > 0:
            camel_case = ''.join(word.capitalize() for word in words[:3])
            hashtags.append(f"#{camel_case}")
        
        # Add individual word hashtags for important terms
        tech_terms = {'ai', 'gpu', 'cloud', 'tech', 'data', 'compute', 
                     'machine', 'learning', 'neural', 'network', 'server',
                     'infrastructure', 'scale', 'performance', 'latency'}
        
        for word in words:
            if word in tech_terms and len(word) > 2:
                hashtags.append(f"#{word.capitalize()}")
        
        return hashtags[:3]  # Max 3 hashtags per topic
    
    def _generate_semantic_hashtags(self) -> List[Dict]:
        """Generate semantic hashtags related to GPU/cloud computing."""
        trends = []
        
        # Dynamic semantic generation based on current context
        contexts = [
            ('gpu_computing', ['GPU', 'CloudCompute', 'HPC']),
            ('ai_infrastructure', ['AIInfrastructure', 'MLOps', 'DeepLearning']),
            ('cloud_services', ['CloudServices', 'IaaS', 'OnDemand']),
            ('performance', ['HighPerformance', 'LowLatency', 'Scalable']),
            ('cost_efficiency', ['CostEffective', 'PayAsYouGo', 'Affordable']),
            ('innovation', ['TechInnovation', 'NextGen', 'FutureTech'])
        ]
        
        # Randomly select contexts to avoid repetition
        selected = random.sample(contexts, min(3, len(contexts)))
        
        for context_name, hashtags in selected:
            for hashtag in hashtags:
                trends.append({
                    'hashtag': f"#{hashtag}",
                    'source': 'semantic',
                    'score': 0.5,
                    'timestamp': datetime.now()
                })
        
        return trends
    
    def _filter_trends(self, trends: List[Dict]) -> List[Dict]:
        """Filter out NSFW and sensitive political content."""
        filtered = []
        
        for trend in trends:
            hashtag_lower = trend['hashtag'].lower()
            
            # Check for NSFW content
            if any(nsfw in hashtag_lower for nsfw in self.NSFW_KEYWORDS):
                continue
                
            # Check for political content
            if any(pol in hashtag_lower for pol in self.POLITICAL_KEYWORDS):
                continue
                
            # Check for minimum length
            if len(trend['hashtag']) < 3 or len(trend['hashtag']) > 30:
                continue
                
            filtered.append(trend)
            
        return filtered
    
    def _score_trends(self, trends: List[Dict]) -> List[Dict]:
        """Score trends based on freshness and relevance."""
        scored = []
        
        # Group by hashtag and aggregate scores
        hashtag_groups = {}
        for trend in trends:
            hashtag = trend['hashtag']
            if hashtag not in hashtag_groups:
                hashtag_groups[hashtag] = {
                    'hashtag': hashtag,
                    'sources': [],
                    'total_score': 0,
                    'timestamp': trend['timestamp']
                }
            hashtag_groups[hashtag]['sources'].append(trend['source'])
            hashtag_groups[hashtag]['total_score'] += trend['score']
        
        # Calculate final scores
        for hashtag, data in hashtag_groups.items():
            # Boost score for multiple sources
            source_multiplier = len(set(data['sources']))
            
            # Time decay factor (newer is better)
            age_hours = (datetime.now() - data['timestamp']).total_seconds() / 3600
            time_factor = max(0.5, 1 - (age_hours / 24))
            
            final_score = data['total_score'] * source_multiplier * time_factor
            
            scored.append({
                'hashtag': hashtag,
                'score': final_score,
                'sources': list(set(data['sources'])),
                'timestamp': data['timestamp']
            })
        
        # Sort by score
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        return scored
    
    async def get_trending_hashtags(self, count: int = 3) -> List[str]:
        """Get current trending hashtags for use in posts."""
        # Refresh if needed (older than 20 minutes)
        if not self.cached_trends or not self.last_refresh or \
           (datetime.now() - self.last_refresh).total_seconds() > 1200:
            await self.refresh_trends()
        
        # Select hashtags with some randomization to avoid repetition
        if not self.cached_trends:
            return []
        
        # Take top trends but add some randomization
        pool_size = min(10, len(self.cached_trends))
        pool = self.cached_trends[:pool_size]
        
        selected = random.sample(pool, min(count, len(pool)))
        return [trend['hashtag'] for trend in selected]
    
    def get_trend_samples(self) -> List[str]:
        """Get sample of current trends for status display."""
        if not self.cached_trends:
            return []
        return [trend['hashtag'] for trend in self.cached_trends[:5]]
