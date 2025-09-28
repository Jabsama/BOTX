"""
Viral tweet composer for VoltageGPU with intelligent hashtag adaptation.
Creates engaging, viral content that naturally promotes GPU services.
"""

import random
import re
import hashlib
import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime

try:
    from .domain_hashtags import DomainHashtagManager
except ImportError:
    DomainHashtagManager = None

logger = logging.getLogger(__name__)


class ViralTweetComposer:
    """Creates viral tweets adapted to trending hashtags."""
    
    PROMO_CODE = "SHA-256-C7E8976BBAF2"
    BASE_URL = "https://voltagegpu.com"
    
    # Concrete GPU offerings - REAL PRICES
    GPU_OFFERINGS = [
        "8x NVIDIA B200 at $41.86/hr",
        "8x NVIDIA H200 at $26.60/hr",
        "8x A100-80GB at $6.02/hr",
        "5x RTX A6000 at $2.10/hr",
        "2x RTX 3090 at $0.46/hr",
        "256-core CPU + 2TB RAM",
        "Instant GPU rental, no queue"
    ]
    
    # AI Model examples - REAL PRICES & STATS
    AI_MODELS = [
        "gemma-3-12b: 54.89M runs • $0.07/M input",
        "DeepSeek-R1: 37.46M runs • $0.46/M input",
        "Hermes-4-405B: 13.23M runs • $0.46/M",
        "GLM-4.5-Air: FREE to use! 🎁",
        "Llama-3.2-3B: $0.02/M input",
        "Qwen3-32B: $0.06/M input • $0.24/M output",
        "DeepSeek-V3: $0.46/M • $1.85/M output"
    ]
    
    # VoltageGPU core value propositions
    CORE_VALUES = {
        'compute': {
            'problem': 'GPU access is expensive & slow',
            'solution': 'Spin up GPUs in seconds, pay-per-use',
            'benefit': 'Lower costs via decentralized network'
        },
        'inference': {
            'problem': 'LLM deployment needs heavy Ops',
            'solution': 'Serverless AI endpoints with autoscaling',
            'benefit': 'Production-ready in minutes, not weeks'
        },
        'decentralized': {
            'problem': 'Vendor lock-in & unpredictable billing',
            'solution': 'Global decentralized GPU network',
            'benefit': 'No lock-in, transparent pricing'
        }
    }
    
    # Hashtag category patterns
    HASHTAG_PATTERNS = {
        'sports': ['UFC', 'NFL', 'NBA', 'Soccer', 'Cricket', 'Tennis', 'Golf', 'Racing'],
        'entertainment': ['Music', 'Movie', 'TV', 'Netflix', 'Gaming', 'Anime'],
        'tech': ['AI', 'Crypto', 'Web3', 'Tech', 'Cloud', 'Data', 'Dev'],
        'culture': ['Fashion', 'Food', 'Travel', 'Art', 'Photo'],
        'news': ['Breaking', 'News', 'Politics', 'Economy'],
        'events': ['Conference', 'Summit', 'Fest', 'Show', 'Expo']
    }
    
    def __init__(self):
        self.last_angle = None
        self.domain_manager = DomainHashtagManager() if DomainHashtagManager else None
        
    async def shorten_url(self, long_url: str) -> str:
        """Shorten URL using a service or custom shortener."""
        try:
            # For production, use bit.ly or custom domain
            # For now, return a shorter version
            if len(long_url) > 50:
                # Use a placeholder short URL (in production, use real shortener)
                return "vtgpu.ai/promo"
            return long_url
        except:
            return long_url
    
    def categorize_hashtag(self, hashtag: str) -> str:
        """Categorize hashtag to understand context."""
        hashtag_clean = hashtag.replace('#', '').lower()
        
        for category, patterns in self.HASHTAG_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in hashtag_clean:
                    return category
        
        return 'general'
    
    def create_viral_hook(self, hashtags: List[str]) -> Dict[str, str]:
        """Create a viral hook based on trending hashtags."""
        if not hashtags:
            hashtags = ['#Tech']
        
        main_hashtag = hashtags[0]
        category = self.categorize_hashtag(main_hashtag)
        topic = main_hashtag.replace('#', '')
        
        hooks = {
            'sports': [
                f"Just like {topic} athletes need peak performance, your AI models need peak GPU power 🚀",
                f"{topic} fans know: timing is everything. Get GPUs in seconds with VoltageGPU ⚡",
                f"Breaking: {topic} meets AI revolution. Train your models faster than a knockout 🥊",
                f"{topic} strategy: Never settle for slow. GPU compute that matches your pace 💪"
            ],
            'entertainment': [
                f"While you're watching {topic}, AI is creating the next big thing. Power it with VoltageGPU 🎬",
                f"{topic} fans: Imagine AI that creates content as fast as you consume it 🎮",
                f"Plot twist: {topic} + AI = Mind-blowing possibilities. Start with instant GPUs 🎭",
                f"Streaming {topic}? Stream GPU power too. On-demand, no buffering 📺"
            ],
            'tech': [
                f"{topic} breakthrough: Decentralized GPUs changing the game. Join the revolution 🔥",
                f"Hot take: {topic} without proper compute is just hype. Get real GPU power now 💻",
                f"{topic} developers: Stop waiting for GPUs. Start building instantly ⚡",
                f"The {topic} community knows: Infrastructure matters. Decentralized > Centralized 🌐"
            ],
            'culture': [
                f"{topic} meets AI: Create, innovate, accelerate with instant GPU access 🎨",
                f"Trending in {topic}: AI-powered everything. Power yours with VoltageGPU ✨",
                f"{topic} creators: Your next masterpiece needs GPU power. Get it in seconds 🚀",
                f"From {topic} to AI: The future is computational. Are you ready? 💫"
            ],
            'news': [
                f"Breaking: While {topic} dominates headlines, AI silently revolutionizes everything 📰",
                f"{topic} update: The real story is AI infrastructure. Decentralized GPUs win 📊",
                f"Today's {topic}, tomorrow's AI. Power your future with instant GPUs 🔮",
                f"Beyond {topic}: The GPU revolution nobody's talking about (yet) 💡"
            ],
            'events': [
                f"At {topic}: Everyone's talking AI. We're delivering the GPUs to power it 🎯",
                f"{topic} spotlight: Decentralized compute is the future. Join us 🌟",
                f"Live from {topic}: GPU access in seconds, not days. Game changer! 🎪",
                f"{topic} exclusive: The GPU platform that's disrupting everything 🚀"
            ],
            'general': [
                f"While {topic} trends, smart builders choose decentralized GPU power 💡",
                f"{topic} + AI = Unlimited potential. Unlock it with instant GPUs ⚡",
                f"The {topic} community is discovering: VoltageGPU changes everything 🔥",
                f"Beyond {topic}: The GPU revolution is here. Don't miss out 🚀"
            ]
        }
        
        hook_options = hooks.get(category, hooks['general'])
        selected_hook = random.choice(hook_options)
        
        return {
            'hook': selected_hook,
            'category': category,
            'topic': topic
        }
    
    def create_value_prop(self, category: str) -> str:
        """Create value proposition with concrete examples."""
        
        # Include concrete GPU/AI examples
        use_gpu_example = random.random() > 0.5
        
        if use_gpu_example:
            gpu_example = random.choice(self.GPU_OFFERINGS)
            if category == 'tech':
                return f"🔧 {gpu_example} • Instant deployment"
            elif category == 'sports':
                return f"⚡ Power like champions: {gpu_example}"
            else:
                return f"✨ {gpu_example} • No setup needed"
        else:
            ai_example = random.choice(self.AI_MODELS)
            value_key = random.choice(list(self.CORE_VALUES.keys()))
            value = self.CORE_VALUES[value_key]
            
            if category == 'tech':
                return f"🚀 {ai_example} • {value['benefit']}"
            elif category == 'entertainment':
                return f"🎬 {ai_example} • Production-ready"
            else:
                return f"💡 {ai_example} • {value['solution']}"
    
    def create_cta_with_promo(self) -> str:
        """Create compelling CTA with promo code."""
        ctas = [
            f"🎁 Code {self.PROMO_CODE} = 5% OFF",
            f"💰 Save 5% with {self.PROMO_CODE}",
            f"🚀 {self.PROMO_CODE} = instant 5% discount",
            f"⚡ 5% OFF: {self.PROMO_CODE}",
            f"🔓 Promo: {self.PROMO_CODE} (5% OFF)"
        ]
        return random.choice(ctas)
    
    async def compose_viral_tweet(self, hashtags: List[str]) -> str:
        """Compose a viral tweet that naturally integrates VoltageGPU promotion."""
        
        # Get viral hook based on hashtags
        hook_data = self.create_viral_hook(hashtags)
        hook = hook_data['hook']
        category = hook_data['category']
        
        # Get value proposition
        value_prop = self.create_value_prop(category)
        
        # Get CTA with promo
        cta = self.create_cta_with_promo()
        
        # Shorten URL
        short_url = await self.shorten_url(self.BASE_URL)
        
        # Select hashtags with domain requirement
        if self.domain_manager:
            # Generate semantic domain hashtags based on category
            semantic_options = self._get_semantic_hashtags_for_category(category)
            
            # Use domain manager to ensure at least one domain hashtag
            selected_tags = self.domain_manager.select_hashtags_with_domain(
                trend_hashtags=hashtags[:3],  # Top 3 trends
                semantic_hashtags=semantic_options,
                angle=category,
                require_domain=True,
                max_hashtags=2
            )
            
            # Log hashtag selection for monitoring
            for tag in selected_tags:
                info = self.domain_manager.get_hashtag_info(tag)
                logger.info(f"Selected hashtag: {tag} - Domain: {info['is_domain']} - Relevance: {info['domain_relevance']}")
        else:
            # Fallback to simple selection
            selected_tags = hashtags[:2] if len(hashtags) > 2 else hashtags
        
        # Build tweet variations
        templates = [
            # Template 1: Hook + Value + CTA + Tags
            f"{hook}\n\n{value_prop}\n\n{cta}\n{short_url}\n\n{' '.join(selected_tags)}",
            
            # Template 2: Tags first for visibility
            f"{' '.join(selected_tags)}\n\n{hook}\n\n{value_prop}\n\n{cta} → {short_url}",
            
            # Template 3: Story format
            f"{hook}\n\nThe solution? {value_prop}\n\n{cta}\n\n{short_url} {' '.join(selected_tags)}",
            
            # Template 4: Direct and punchy
            f"{' '.join(selected_tags)} 🔥\n\n{hook[:-2]}.\n{value_prop}\n\n{cta} {short_url}",
            
            # Template 5: Question format
            f"{hook}\n\nAnswer: {value_prop} 💡\n\n{cta}\n{short_url}\n\n{' '.join(selected_tags)}"
        ]
        
        # Choose template and ensure it fits
        for template in templates:
            if len(template) <= 280:
                return template
        
        # Fallback: Shorter version
        short_hook = hook[:100] if len(hook) > 100 else hook
        fallback = f"{' '.join(selected_tags)} {short_hook} {cta} {short_url}"
        
        if len(fallback) > 280:
            # Emergency short version
            fallback = f"{selected_tags[0]} GPU power on-demand! {self.PROMO_CODE} → {short_url}"
        
        return fallback[:280]
    
    def _get_semantic_hashtags_for_category(self, category: str) -> List[str]:
        """Generate semantic hashtags based on category."""
        semantic_map = {
            'tech': ['#AICompute', '#GPUCloud', '#MLInference', '#DeepLearning'],
            'sports': ['#AITraining', '#GPUPower', '#ComputeSpeed', '#FastInference'],
            'entertainment': ['#AICreative', '#GPURendering', '#CloudCompute', '#MediaAI'],
            'culture': ['#CreativeAI', '#GPUArt', '#AIInnovation', '#ComputePower'],
            'news': ['#AIAnalytics', '#DataProcessing', '#GPUCompute', '#CloudScale'],
            'events': ['#TechInfra', '#GPUDeploy', '#AIScale', '#CloudGPU'],
            'general': ['#GPUCompute', '#AIInference', '#CloudGPU', '#MLCompute']
        }
        
        return semantic_map.get(category, semantic_map['general'])


class SmartTweetOptimizer:
    """Optimizes tweets for maximum engagement."""
    
    VIRAL_ELEMENTS = {
        'emojis': ['🚀', '⚡', '🔥', '💡', '✨', '🎯', '💪', '🌟', '🔧', '💰'],
        'power_words': ['Breaking', 'Exclusive', 'Revolutionary', 'Game-changing', 
                       'Instant', 'Unlimited', 'Free', 'Now', 'Today', 'New'],
        'social_proof': ['Join thousands', 'Industry leaders choose', 'Trusted by',
                        'Community favorite', 'Top choice', '#1 platform'],
        'urgency': ['Limited time', 'Today only', 'Don\'t miss', 'Act now',
                   'While it lasts', 'Exclusive access'],
        'curiosity': ['The secret', 'Nobody talks about', 'Hidden advantage',
                     'What they don\'t tell you', 'The truth about']
    }
    
    @staticmethod
    def add_viral_elements(tweet: str) -> str:
        """Add viral elements while keeping natural."""
        
        # Don't over-optimize
        if random.random() > 0.7:  # 30% chance to add extra elements
            return tweet
        
        # Add power word if not present
        has_power_word = any(word.lower() in tweet.lower() 
                            for word in SmartTweetOptimizer.VIRAL_ELEMENTS['power_words'])
        
        if not has_power_word and random.random() > 0.5:
            power_word = random.choice(SmartTweetOptimizer.VIRAL_ELEMENTS['power_words'])
            # Insert at beginning if possible
            if len(f"{power_word}: {tweet}") <= 280:
                tweet = f"{power_word}: {tweet}"
        
        return tweet
    
    @staticmethod
    def optimize_for_engagement(tweet: str) -> str:
        """Final optimization pass."""
        
        # Ensure good emoji distribution (not too many)
        emoji_count = sum(1 for char in tweet if char in SmartTweetOptimizer.VIRAL_ELEMENTS['emojis'])
        
        if emoji_count > 5:
            # Too many emojis, remove some
            for emoji in SmartTweetOptimizer.VIRAL_ELEMENTS['emojis']:
                if emoji_count > 3:
                    tweet = tweet.replace(emoji, '', 1)
                    emoji_count -= 1
        
        # Ensure readability with line breaks
        if '\n' not in tweet and len(tweet) > 200:
            # Add strategic line break
            mid = len(tweet) // 2
            space_idx = tweet.find(' ', mid)
            if space_idx > 0:
                tweet = tweet[:space_idx] + '\n\n' + tweet[space_idx+1:]
        
        return tweet.strip()
