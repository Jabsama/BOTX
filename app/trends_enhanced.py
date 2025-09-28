"""
Enhanced trends extraction with multiple sources, caching, and relevance scoring.
"""

import asyncio
import re
import logging
import json
import hashlib
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
import random
from collections import Counter
import aiohttp
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langdetect import detect, LangDetectException
import tweepy
from .config import Config
from .store import Store

logger = logging.getLogger(__name__)


class EnhancedTrendsManager:
    """Advanced trend extraction with relevance scoring and caching."""
    
    NSFW_KEYWORDS = {
        'porn', 'xxx', 'nsfw', 'nude', 'sex', 'onlyfans', 'adult',
        'escort', 'fetish', 'bdsm', 'milf', 'boobs', 'ass', 'dick'
    }
    
    POLITICAL_KEYWORDS = {
        'trump', 'biden', 'democrat', 'republican', 'maga', 'liberal',
        'conservative', 'election', 'vote', 'politics', 'congress',
        'senate', 'president', 'governor', 'campaign', 'ballot'
    }
    
    # AI/GPU/Cloud computing reference corpus for relevance scoring
    RELEVANCE_CORPUS = [
        "GPU computing cloud infrastructure AI machine learning",
        "deep learning neural networks training inference",
        "CUDA tensor cores RTX A100 H100 compute",
        "kubernetes docker containers orchestration deployment",
        "API REST GraphQL microservices serverless",
        "latency throughput performance optimization scaling",
        "cost effective pricing pay as you go on demand",
        "data science analytics big data processing",
        "LLM transformer models GPT BERT diffusion",
        "rendering graphics visualization simulation",
        "high performance computing HPC cluster",
        "autoscaling elastic compute resources",
        "cloud native infrastructure as a service",
        "machine learning operations MLOps DevOps"
    ]
    
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self.twitter_client = None
        self.cache_file = Path("data/trends_cache.json")
        self.cache_duration = timedelta(hours=2)
        self.last_refresh = None
        self.cached_trends = []
        
        # Initialize TF-IDF vectorizer for relevance scoring
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.relevance_vectors = self.vectorizer.fit_transform(self.RELEVANCE_CORPUS)
        
    def set_twitter_client(self, client):
        """Set Twitter client for search operations."""
        self.twitter_client = client
        
    async def refresh_trends(self) -> List[Dict]:
        """
        Main trend refresh with caching and multiple sources.
        """
        try:
            # Check cache first
            cached = self._load_cache()
            if cached:
                logger.info(f"Using cached trends ({len(cached)} items)")
                self.cached_trends = cached
                return cached
            
            trends = []
            
            # 1. Try NewsAPI for tech news
            news_trends = await self._extract_news_trends()
            if news_trends:
                trends.extend(news_trends)
                logger.info(f"Extracted {len(news_trends)} trends from NewsAPI")
            
            # 2. Try Reddit tech subreddits
            reddit_trends = await self._extract_reddit_trends()
            if reddit_trends:
                trends.extend(reddit_trends)
                logger.info(f"Extracted {len(reddit_trends)} trends from Reddit")
            
            # 3. Try GitHub trending
            github_trends = await self._extract_github_trends()
            if github_trends:
                trends.extend(github_trends)
                logger.info(f"Extracted {len(github_trends)} trends from GitHub")
            
            # 4. Twitter search (if not in conservative mode)
            if self.twitter_client and self.config.X_READS_MODE != 'conservative':
                twitter_trends = await self._extract_twitter_trends()
                if twitter_trends:
                    trends.extend(twitter_trends)
                    logger.info(f"Extracted {len(twitter_trends)} trends from Twitter")
            
            # 5. Generate semantic hashtags as fallback
            if len(trends) < 5:
                semantic_trends = self._generate_semantic_hashtags()
                trends.extend(semantic_trends)
                logger.info(f"Generated {len(semantic_trends)} semantic hashtags")
            
            # Filter and score trends
            filtered_trends = self._filter_trends(trends)
            scored_trends = self._score_trends_with_relevance(filtered_trends)
            
            # Only keep trends with sufficient relevance
            relevant_trends = [
                t for t in scored_trends 
                if t.get('relevance_score', 0) >= self.config.MIN_RELEVANCE_SCORE
            ]
            
            if len(relevant_trends) < 3:
                # Create bridge content for off-topic trends
                bridged_trends = self._create_bridge_trends(scored_trends[:5])
                relevant_trends.extend(bridged_trends)
            
            # Store in cache
            self._save_cache(relevant_trends[:20])
            
            # Store in database
            await self.store.update_trends(relevant_trends)
            self.cached_trends = relevant_trends[:20]
            self.last_refresh = datetime.now()
            
            logger.info(f"Trend refresh complete: {len(relevant_trends)} relevant trends")
            return self.cached_trends
            
        except Exception as e:
            logger.error(f"Error refreshing trends: {e}")
            return self.cached_trends or self._generate_semantic_hashtags()
    
    async def _extract_news_trends(self) -> List[Dict]:
        """Extract trends from tech news sources."""
        trends = []
        
        try:
            # Using NewsAPI (you'd need an API key in production)
            # For now, simulating with tech RSS feeds
            tech_topics = [
                "artificial intelligence", "machine learning", "cloud computing",
                "GPU shortage", "NVIDIA earnings", "OpenAI", "Google Gemini",
                "AWS updates", "Kubernetes", "serverless", "edge computing"
            ]
            
            for topic in random.sample(tech_topics, min(5, len(tech_topics))):
                hashtag = "#" + "".join(word.capitalize() for word in topic.split()[:2])
                trends.append({
                    'hashtag': hashtag,
                    'source': 'news',
                    'score': random.uniform(0.7, 1.0),
                    'timestamp': datetime.now(),
                    'topic': topic
                })
                
        except Exception as e:
            logger.warning(f"Error extracting news trends: {e}")
            
        return trends
    
    async def _extract_reddit_trends(self) -> List[Dict]:
        """Extract trends from Reddit tech subreddits."""
        trends = []
        
        try:
            # Simulating Reddit API (would use PRAW in production)
            subreddit_topics = [
                ("MachineLearning", ["#DeepLearning", "#NeuralNetworks"]),
                ("LocalLLaMA", ["#LLM", "#AIModels"]),
                ("selfhosted", ["#SelfHosted", "#CloudAlternative"]),
                ("kubernetes", ["#K8s", "#ContainerOrchestration"]),
                ("nvidia", ["#NVIDIA", "#GPUComputing"])
            ]
            
            for subreddit, hashtags in random.sample(subreddit_topics, 3):
                for hashtag in hashtags:
                    trends.append({
                        'hashtag': hashtag,
                        'source': 'reddit',
                        'score': random.uniform(0.6, 0.9),
                        'timestamp': datetime.now(),
                        'subreddit': subreddit
                    })
                    
        except Exception as e:
            logger.warning(f"Error extracting Reddit trends: {e}")
            
        return trends
    
    async def _extract_github_trends(self) -> List[Dict]:
        """Extract trends from GitHub trending repositories."""
        trends = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # GitHub trending API endpoint (unofficial)
                url = "https://api.github.com/search/repositories"
                params = {
                    'q': 'language:python machine-learning OR ai OR gpu',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 10
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for repo in data.get('items', [])[:5]:
                            topics = repo.get('topics', [])
                            for topic in topics[:2]:
                                if topic and len(topic) > 2:
                                    hashtag = f"#{topic.replace('-', '').capitalize()}"
                                    trends.append({
                                        'hashtag': hashtag,
                                        'source': 'github',
                                        'score': 0.8,
                                        'timestamp': datetime.now()
                                    })
                                    
        except Exception as e:
            logger.warning(f"Error extracting GitHub trends: {e}")
            
        return trends
    
    async def _extract_twitter_trends(self) -> List[Dict]:
        """Extract trends from Twitter with fixed query."""
        trends = []
        
        # Check daily read quota
        reads_today = await self.store.get_reads_today()
        if reads_today >= self.config.MAX_READS_PER_DAY:
            logger.warning(f"Daily read limit reached ({reads_today}/{self.config.MAX_READS_PER_DAY})")
            return trends
        
        try:
            # Fixed query with proper content
            query = "#AI OR #GPU OR #CloudComputing OR #MachineLearning lang:en -is:retweet -is:reply"
            
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=20,
                tweet_fields=['created_at', 'entities']
            )
            
            # Record API read
            await self.store.record_api_read('twitter_search')
            
            if tweets and tweets.data:
                hashtag_counter = Counter()
                
                for tweet in tweets.data:
                    if tweet.entities and 'hashtags' in tweet.entities:
                        for tag in tweet.entities['hashtags']:
                            hashtag = f"#{tag['tag']}"
                            hashtag_counter[hashtag] += 1
                
                for hashtag, count in hashtag_counter.most_common(10):
                    trends.append({
                        'hashtag': hashtag,
                        'source': 'twitter',
                        'score': count,
                        'timestamp': datetime.now()
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting Twitter trends: {e}")
            
        return trends
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate relevance score using keyword matching and semantic similarity."""
        try:
            # Clean the text
            clean_text = text.lower().replace('#', '').replace('_', ' ')
            
            # Direct keyword matching (high confidence)
            keywords = ['gpu', 'ai', 'cloud', 'compute', 'ml', 'deep', 'learning', 
                       'neural', 'kubernetes', 'docker', 'server', 'latency', 
                       'performance', 'scale', 'infrastructure', 'llm', 'model']
            
            keyword_score = 0
            for keyword in keywords:
                if keyword in clean_text:
                    keyword_score += 0.3
            
            # Cap keyword score at 1.0
            keyword_score = min(1.0, keyword_score)
            
            # If we have a good keyword match, use it
            if keyword_score >= 0.6:
                return keyword_score
            
            # Otherwise try vectorization
            try:
                text_vector = self.vectorizer.transform([clean_text])
                similarities = cosine_similarity(text_vector, self.relevance_vectors)
                vector_score = float(np.max(similarities))
                
                # Combine scores with weight on keyword matching
                return max(keyword_score, vector_score * 0.7 + keyword_score * 0.3)
            except:
                # Fallback to keyword score only
                return keyword_score
                
        except Exception as e:
            logger.warning(f"Error calculating relevance: {e}")
            # Default score for tech-related hashtags
            if any(kw in text.lower() for kw in ['gpu', 'ai', 'cloud', 'ml']):
                return 0.7
            return 0.3
    
    def _score_trends_with_relevance(self, trends: List[Dict]) -> List[Dict]:
        """Score trends with relevance to AI/GPU/Cloud computing."""
        scored = []
        
        for trend in trends:
            hashtag = trend['hashtag']
            
            # Calculate relevance score
            relevance = self._calculate_relevance_score(hashtag)
            
            # Boost score for certain sources
            source_boost = {
                'twitter': 1.2,
                'github': 1.1,
                'reddit': 1.0,
                'news': 1.15,
                'semantic': 0.8
            }.get(trend.get('source', 'unknown'), 1.0)
            
            # Time decay factor
            age_hours = (datetime.now() - trend.get('timestamp', datetime.now())).total_seconds() / 3600
            time_factor = max(0.5, 1 - (age_hours / 24))
            
            # Combined score
            base_score = trend.get('score', 1.0)
            final_score = base_score * source_boost * time_factor * (1 + relevance)
            
            scored.append({
                **trend,
                'relevance_score': relevance,
                'final_score': final_score
            })
        
        # Sort by final score
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored
    
    def _create_bridge_trends(self, off_topic_trends: List[Dict]) -> List[Dict]:
        """Create bridge content connecting off-topic trends to GPU computing."""
        bridged = []
        
        bridge_templates = [
            "How {topic} benefits from GPU acceleration",
            "Scaling {topic} with cloud computing",
            "{topic} meets high-performance computing",
            "The GPU revolution in {topic}",
            "Why {topic} needs elastic compute"
        ]
        
        for trend in off_topic_trends:
            if trend.get('relevance_score', 0) < self.config.MIN_RELEVANCE_SCORE:
                # Extract topic from hashtag
                topic = trend['hashtag'].replace('#', '').lower()
                
                # Create bridged hashtags
                bridge_text = random.choice(bridge_templates).format(topic=topic)
                
                bridged.append({
                    'hashtag': f"#{topic.capitalize()}GPU",
                    'source': 'bridge',
                    'score': 0.7,
                    'timestamp': datetime.now(),
                    'relevance_score': 0.6,
                    'bridge_text': bridge_text
                })
        
        return bridged
    
    def _generate_semantic_hashtags(self) -> List[Dict]:
        """Generate semantic hashtags related to GPU/cloud computing."""
        trends = []
        
        contexts = [
            ('gpu_computing', ['GPUComputing', 'CloudGPU', 'HPCCloud']),
            ('ai_infrastructure', ['AIInfra', 'MLOps', 'DeepLearning']),
            ('cloud_native', ['CloudNative', 'Serverless', 'K8s']),
            ('performance', ['HighPerformance', 'LowLatency', 'FastCompute']),
            ('cost_optimization', ['CostOptimized', 'PayPerUse', 'ElasticScale']),
            ('innovation', ['TechInnovation', 'NextGenCompute', 'FutureCloud'])
        ]
        
        selected = random.sample(contexts, min(4, len(contexts)))
        
        for context_name, hashtags in selected:
            for hashtag in hashtags:
                trends.append({
                    'hashtag': f"#{hashtag}",
                    'source': 'semantic',
                    'score': 0.5,
                    'timestamp': datetime.now(),
                    'relevance_score': 0.8
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
    
    def _load_cache(self) -> Optional[List[Dict]]:
        """Load trends from cache if still valid."""
        try:
            if not self.cache_file.exists():
                return None
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            
            # Check if cache is still valid
            if datetime.now() - cache_time < self.cache_duration:
                return cache_data['trends']
                
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            
        return None
    
    def _save_cache(self, trends: List[Dict]):
        """Save trends to cache file."""
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            
            # Convert datetime objects to strings
            serializable_trends = []
            for trend in trends:
                trend_copy = trend.copy()
                if 'timestamp' in trend_copy and isinstance(trend_copy['timestamp'], datetime):
                    trend_copy['timestamp'] = trend_copy['timestamp'].isoformat()
                serializable_trends.append(trend_copy)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'trends': serializable_trends
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    async def get_trending_hashtags(self, count: int = 3) -> List[str]:
        """Get current trending hashtags for use in posts."""
        # Refresh if needed (older than cache duration)
        if not self.cached_trends or not self.last_refresh or \
           (datetime.now() - self.last_refresh) > self.cache_duration:
            await self.refresh_trends()
        
        # Filter for high relevance only
        relevant = [
            t for t in self.cached_trends 
            if t.get('relevance_score', 0) >= self.config.MIN_RELEVANCE_SCORE
        ]
        
        if not relevant:
            relevant = self.cached_trends[:count] if self.cached_trends else []
        
        # Select with some randomization
        pool_size = min(10, len(relevant))
        pool = relevant[:pool_size]
        
        selected = random.sample(pool, min(count, len(pool)))
        return [trend['hashtag'] for trend in selected]
    
    def get_trend_samples(self) -> List[str]:
        """Get sample of current trends for status display."""
        if not self.cached_trends:
            return []
        
        # Show only relevant trends
        relevant = [
            t for t in self.cached_trends[:10]
            if t.get('relevance_score', 0) >= self.config.MIN_RELEVANCE_SCORE
        ]
        
        return [f"{t['hashtag']} ({t.get('relevance_score', 0):.2f})" for t in relevant[:5]]
