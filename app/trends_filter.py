"""
Advanced Trend Filtering with Relevance Scoring
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein

class TrendFilter:
    """Filter and score trends for relevance to GPU/AI domain"""
    
    # Domain keywords for relevance scoring
    DOMAIN_KEYWORDS = [
        "AI", "GPU", "LLM", "cloud", "inference", "training", "rendering",
        "compute", "latency", "autoscale", "ML", "deep learning", "neural",
        "model", "deployment", "serverless", "kubernetes", "docker", "API",
        "performance", "optimization", "CUDA", "tensor", "pytorch", "tensorflow",
        "huggingface", "openai", "anthropic", "gemini", "llama", "mistral"
    ]
    
    # Blacklist for NSFW/political content
    BLACKLIST_PATTERNS = [
        r'\b(nsfw|porn|xxx|adult|18\+)\b',
        r'\b(trump|biden|election|vote|democrat|republican|politics)\b',
        r'\b(war|conflict|attack|bomb|terror)\b',
        r'\b(death|died|killed|murder)\b'
    ]
    
    def __init__(self, min_relevance: float = 0.55, max_similarity: float = 0.88):
        self.min_relevance = min_relevance
        self.max_similarity = max_similarity
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.domain_vector = None
        self._init_domain_vector()
        
    def _init_domain_vector(self):
        """Initialize the domain relevance vector"""
        domain_text = " ".join(self.DOMAIN_KEYWORDS * 3)  # Weight domain terms
        self.domain_vector = self.vectorizer.fit_transform([domain_text])
    
    def calculate_relevance(self, trend: str) -> float:
        """Calculate relevance score for a trend"""
        try:
            # Clean the trend
            clean_trend = re.sub(r'[#@]', '', trend).lower()
            
            # Check for exact domain keyword matches (high relevance)
            for keyword in self.DOMAIN_KEYWORDS:
                if keyword.lower() in clean_trend.lower():
                    return 0.85  # High relevance for exact matches
            
            # Calculate cosine similarity with domain vector
            trend_vector = self.vectorizer.transform([clean_trend])
            similarity = cosine_similarity(trend_vector, self.domain_vector)[0][0]
            
            # Boost score for tech-related patterns
            if re.search(r'\b(tech|code|dev|data|api|cloud)\b', clean_trend, re.I):
                similarity = min(1.0, similarity + 0.2)
            
            return similarity
            
        except Exception:
            return 0.0
    
    def is_blacklisted(self, trend: str) -> bool:
        """Check if trend contains blacklisted content"""
        trend_lower = trend.lower()
        for pattern in self.BLACKLIST_PATTERNS:
            if re.search(pattern, trend_lower, re.I):
                return True
        return False
    
    def remove_duplicates(self, trends: List[str]) -> List[str]:
        """Remove near-duplicate trends using Levenshtein distance"""
        if not trends:
            return []
        
        unique_trends = []
        for trend in trends:
            is_duplicate = False
            for unique in unique_trends:
                # Calculate similarity
                similarity = 1 - (Levenshtein.distance(trend.lower(), unique.lower()) / 
                                max(len(trend), len(unique)))
                if similarity > self.max_similarity:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_trends.append(trend)
        
        return unique_trends
    
    def bridge_to_gpu_context(self, trend: str) -> Optional[str]:
        """Create intelligent bridge from off-topic trend to GPU context"""
        trend_lower = trend.lower().replace('#', '')
        
        bridges = {
            # Sports
            'ufc|mma|boxing|fight': "Fight night traffic spikes? Handle the load with instant GPU scaling",
            'nfl|nba|soccer|football|baseball': "Game day traffic surge? Autoscale your AI with on-demand GPUs",
            'olympics|worldcup|championship': "Global event streaming? Deploy GPUs worldwide in minutes",
            
            # Entertainment
            'music|concert|festival': "Streaming to millions? GPU-powered transcoding at any scale",
            'movie|film|netflix|disney': "Content delivery at scale needs serious GPU compute",
            'gaming|xbox|playstation|nintendo': "Gaming + AI = next-gen experiences. Start with instant GPUs",
            
            # News/Events
            'breaking|news|alert': "Breaking news analysis? Process data faster with GPU acceleration",
            'launch|release|announcement': "Product launch traffic? Scale compute instantly, pay per use",
            
            # Generic
            'trend|viral|hot': "Going viral? Don't let your servers crash. Scale GPUs on-demand"
        }
        
        for pattern, bridge in bridges.items():
            if re.search(pattern, trend_lower):
                return bridge
        
        # Default bridge for any trend
        return f"While #{trend.replace('#', '')} trends, smart teams choose scalable GPU compute"
    
    async def filter_and_score(self, trends: List[str]) -> List[Dict[str, any]]:
        """Filter and score trends for quality and relevance"""
        filtered = []
        
        # Remove duplicates first
        unique_trends = self.remove_duplicates(trends)
        
        for trend in unique_trends:
            # Skip if blacklisted
            if self.is_blacklisted(trend):
                continue
            
            # Calculate relevance
            relevance = self.calculate_relevance(trend)
            
            # Determine if we need a bridge
            needs_bridge = relevance < self.min_relevance
            bridge_text = None
            
            if needs_bridge:
                bridge_text = self.bridge_to_gpu_context(trend)
                # If we have a good bridge, boost relevance slightly
                if bridge_text:
                    relevance = min(self.min_relevance, relevance + 0.15)
            
            # Only include if meets minimum relevance (with or without bridge)
            if relevance >= self.min_relevance or bridge_text:
                filtered.append({
                    'hashtag': trend,
                    'relevance': relevance,
                    'needs_bridge': needs_bridge,
                    'bridge_text': bridge_text,
                    'source': 'filtered'
                })
        
        # Sort by relevance
        filtered.sort(key=lambda x: x['relevance'], reverse=True)
        
        return filtered


class PulsedTrendExtractor:
    """Extract trends using pulsed X Search API calls"""
    
    def __init__(self, pulse_hours: int = 8, max_results: int = 100):
        self.pulse_hours = pulse_hours
        self.max_results = max_results
        self.cache_file = Path("data/pulsed_trends.json")
        self.last_pulse_file = Path("data/last_pulse.json")
        
    def _should_pulse(self) -> bool:
        """Check if we should make a new pulse"""
        if not self.last_pulse_file.exists():
            return True
        
        try:
            with open(self.last_pulse_file) as f:
                data = json.load(f)
                last_pulse = datetime.fromisoformat(data['timestamp'])
                return (datetime.now() - last_pulse).total_seconds() > (self.pulse_hours * 3600)
        except:
            return True
    
    async def pulse_search(self, client) -> List[str]:
        """Perform a pulsed search on X"""
        if not self._should_pulse():
            return self._load_cached_trends()
        
        try:
            # Search for recent English tweets with hashtags
            query = "lang:en has:hashtags -is:retweet -is:reply"
            tweets = await client.search_recent_tweets(
                query=query,
                max_results=self.max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            # Extract hashtags with frequency scoring
            hashtag_freq = {}
            for tweet in tweets.data or []:
                if tweet.entities and tweet.entities.get('hashtags'):
                    for tag in tweet.entities['hashtags']:
                        hashtag = f"#{tag['tag']}"
                        hashtag_freq[hashtag] = hashtag_freq.get(hashtag, 0) + 1
            
            # Score by frequency × freshness
            scored_trends = []
            for hashtag, freq in hashtag_freq.items():
                score = freq * 1.0  # Can add time decay here
                scored_trends.append((hashtag, score))
            
            # Sort by score and take top 20
            scored_trends.sort(key=lambda x: x[1], reverse=True)
            top_trends = [trend[0] for trend in scored_trends[:20]]
            
            # Cache the results
            self._cache_trends(top_trends)
            
            # Update last pulse timestamp
            with open(self.last_pulse_file, 'w') as f:
                json.dump({'timestamp': datetime.now().isoformat()}, f)
            
            return top_trends
            
        except Exception as e:
            print(f"Pulse search failed: {e}")
            return self._load_cached_trends()
    
    def _cache_trends(self, trends: List[str]):
        """Cache trends to file"""
        self.cache_file.parent.mkdir(exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump({
                'trends': trends,
                'timestamp': datetime.now().isoformat()
            }, f)
    
    def _load_cached_trends(self) -> List[str]:
        """Load cached trends"""
        if not self.cache_file.exists():
            return []
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
                return data.get('trends', [])
        except:
            return []
    
    def get_trend_age_minutes(self) -> Optional[int]:
        """Get age of cached trends in minutes"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data['timestamp'])
                return int((datetime.now() - timestamp).total_seconds() / 60)
        except:
            return None
