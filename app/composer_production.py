"""
Production-Ready Composer with Strict Validation
"""

import re
import uuid
import random
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

class ProductionComposer:
    """Production-ready composer with strict Twitter compliance"""
    
    # Rotation angles
    ANGLES = ["cost", "latency", "autoscale", "regions", "uptime", "support"]
    
    # Strict templates (will be trimmed to fit with promo block)
    TEMPLATES = {
        "cost": {
            "template": "#{trend} is peaking—don't let GPU costs spike. Pay-per-use compute, scale back after.",
            "bridge": "{bridge} Don't overpay for idle compute."
        },
        "latency": {
            "template": "#{trend} demos flop when latency bites. Get low-latency GPU inference in minutes.",
            "bridge": "{bridge} Keep latency low with instant GPUs."
        },
        "autoscale": {
            "template": "Traffic from #{trend}? Burst compute when you need it, then scale down.",
            "bridge": "{bridge} Autoscale seamlessly."
        },
        "regions": {
            "template": "Going live during #{trend}? Launch GPU pods in multiple regions to cut RTT.",
            "bridge": "{bridge} Deploy globally in minutes."
        },
        "uptime": {
            "template": "#{trend} surges aren't a problem with pods you can redeploy in seconds.",
            "bridge": "{bridge} 99.9% uptime guaranteed."
        },
        "support": {
            "template": "Shipping during #{trend}? We'll help you size GPUs and deploy faster.",
            "bridge": "{bridge} Expert support 24/7."
        }
    }
    
    # Price templates (compact)
    PRICE_TEMPLATES = {
        "budget": "Need compute for #{trend}? 2× RTX 3090 from $0.46/hr.",
        "value": "#{trend} workloads? 8× A100-80GB from $6.02/hr.",
        "premium": "Enterprise #{trend}? 8× H200 at $26.60/hr."
    }
    
    # Common English words for validation (expanded for tech/marketing)
    ENGLISH_WORDS = set([
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their",
        "what", "so", "up", "out", "if", "about", "who", "get", "which", "go",
        "gpu", "gpus", "compute", "scale", "deploy", "traffic", "surge", "demo", "ship",
        "launch", "pod", "pods", "inference", "latency", "cost", "minute", "second",
        "need", "burst", "down", "help", "size", "faster", "online", "live",
        "is", "are", "was", "were", "been", "being", "has", "had", "does", "did",
        "can", "could", "may", "might", "must", "shall", "should", "will", "would",
        "let", "make", "made", "take", "took", "give", "gave", "come", "came",
        "know", "think", "see", "look", "want", "use", "find", "tell", "ask",
        "work", "seem", "feel", "try", "leave", "call", "good", "new", "first",
        "last", "long", "great", "little", "own", "other", "old", "right", "big",
        "high", "different", "small", "large", "next", "early", "young", "important",
        "few", "public", "bad", "same", "able", "data", "system", "program", "question",
        "during", "until", "always", "service", "away", "report", "something", "nothing",
        "hr", "per", "hour", "hours", "day", "days", "week", "month", "year",
        "server", "servers", "cloud", "api", "apis", "model", "models", "run", "runs",
        "load", "spike", "spikes", "handle", "instant", "instantly", "globally",
        "uptime", "guaranteed", "flop", "bites", "tight", "problem", "redeploy",
        "seconds", "minutes", "regions", "region", "cut", "rtt", "speed", "users",
        "shipping", "faster", "expert", "support", "seamlessly", "autoscale",
        "workloads", "workload", "enterprise", "premium", "budget", "value",
        "pay", "usage", "back", "after", "when", "then", "keep", "low"
    ])
    
    def __init__(self):
        self.angle_index = 0
        self.prices_file = Path("data/offers.json")
        self.angle_stats_file = Path("data/angle_stats.json")
        self._load_angle_stats()
    
    def _load_angle_stats(self):
        """Load angle usage statistics"""
        if self.angle_stats_file.exists():
            try:
                with open(self.angle_stats_file) as f:
                    self.angle_stats = json.load(f)
            except:
                self.angle_stats = {angle: 0 for angle in self.ANGLES}
        else:
            self.angle_stats = {angle: 0 for angle in self.ANGLES}
    
    def _save_angle_stats(self):
        """Save angle usage statistics"""
        self.angle_stats_file.parent.mkdir(exist_ok=True)
        with open(self.angle_stats_file, 'w') as f:
            json.dump(self.angle_stats, f)
    
    def rotate_angle(self) -> str:
        """Rotate through angles in strict order"""
        angle = self.ANGLES[self.angle_index]
        self.angle_index = (self.angle_index + 1) % len(self.ANGLES)
        self.angle_stats[angle] += 1
        self._save_angle_stats()
        return angle
    
    def build_promo_block(self, account: str, terms: List[str]) -> Tuple[str, str]:
        """Build standardized promo block with UTM tracking"""
        # Clean terms for URL
        clean_terms = [t.replace('#', '').replace(' ', '') for t in terms[:2]]
        term_str = '+'.join(clean_terms)
        uuid8 = str(uuid.uuid4())[:8]
        
        # Build full URL with UTM
        full_url = (
            f"https://voltagegpu.com/"
            f"?utm_source=twitter"
            f"&utm_medium=social"
            f"&utm_campaign=promo_SHA-256-C7E8976BBAF2"
            f"&utm_content={account}"
            f"&utm_term={term_str}"
            f"&utm_id={uuid8}"
        )
        
        # Standard promo block
        promo = f"EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {full_url}"
        
        return promo, full_url
    
    def calculate_twitter_length(self, text: str) -> int:
        """Calculate actual Twitter length (URLs = 23 chars)"""
        # Replace all URLs with 23-char placeholder
        url_pattern = r'https?://[^\s]+'
        normalized = re.sub(url_pattern, 'x' * 23, text)
        
        # Count actual length
        return len(normalized)
    
    def is_english_loose(self, text: str) -> bool:
        """Loose English validation for short marketing texts"""
        # Strip URLs, hashtags, numbers, and promo block
        core_text = re.sub(r'https?://[^\s]+', '', text)
        core_text = re.sub(r'#\w+', '', core_text)
        core_text = re.sub(r'SHA-256-C7E8976BBAF2', '', core_text)
        core_text = re.sub(r'EXCLUSIVE PROMO CODE', '', core_text)
        core_text = re.sub(r'\d+', '', core_text)
        core_text = re.sub(r'[×$%/@\-—–]', '', core_text)  # Also remove special chars
        core_text = re.sub(r'\s+', ' ', core_text).strip()  # Normalize whitespace
        
        # If very short after stripping, assume OK
        if len(core_text) < 20:
            return True
        
        # Tokenize and check English ratio
        words = re.findall(r'\b[a-zA-Z]+\b', core_text.lower())
        if not words or len(words) < 3:
            return True
        
        # Count English words
        english_count = sum(1 for w in words if w.lower() in self.ENGLISH_WORDS)
        ratio = english_count / len(words)
        
        # 50% threshold for marketing copy (more permissive)
        # Or if we have at least 5 English words in a short text
        return ratio >= 0.5 or (english_count >= 5 and len(words) <= 15)
    
    def count_hashtags(self, text: str) -> int:
        """Count hashtags in text"""
        return len(re.findall(r'#\w+', text))
    
    def check_caps_ratio(self, text: str) -> float:
        """Check uppercase ratio (excluding hashtags, URLs, promo)"""
        # Strip elements that can have caps
        core = re.sub(r'https?://[^\s]+', '', text)
        core = re.sub(r'#\w+', '', core)
        core = re.sub(r'EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2', '', core)
        core = re.sub(r'[^a-zA-Z]', '', core)
        
        if not core:
            return 0.0
        
        upper_count = sum(1 for c in core if c.isupper())
        return upper_count / len(core)
    
    def get_fresh_prices(self) -> Optional[Dict]:
        """Get fresh price data if available"""
        if not self.prices_file.exists():
            return None
        
        try:
            with open(self.prices_file) as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data.get('timestamp', '2020-01-01'))
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                
                if age_hours < 24:
                    return data.get('offers', {})
                return None
        except:
            return None
    
    def compose_production_tweet(
        self,
        trend_data: Dict,
        account: str = "account_a"
    ) -> str:
        """Compose production-ready tweet with strict validation"""
        
        # Extract trend info
        hashtag = trend_data['hashtag']
        needs_bridge = trend_data.get('needs_bridge', False)
        bridge_text = trend_data.get('bridge_text', '')
        
        # Get current angle
        angle = self.rotate_angle()
        
        # Build promo block first (to know its length)
        promo_block, full_url = self.build_promo_block(account, [hashtag])
        
        # Calculate available space (260 - promo block - spacing)
        # Twitter counts URLs as 23 chars
        promo_length = len("EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 ") + 23
        available_space = 260 - promo_length - 10  # 10 for spacing/newlines
        
        # Check for fresh prices (33% chance)
        prices = self.get_fresh_prices()
        use_price = prices and random.random() < 0.33
        
        # Build main content
        if use_price:
            # Use price template
            tier = random.choice(['budget', 'value', 'premium'])
            template = self.PRICE_TEMPLATES[tier]
            main_content = template.format(trend=hashtag.replace('#', ''))
        else:
            # Use angle template
            templates = self.TEMPLATES[angle]
            
            if needs_bridge and bridge_text:
                main_content = templates['bridge'].format(bridge=bridge_text)
            else:
                main_content = templates['template'].format(
                    trend=hashtag.replace('#', '')
                )
        
        # Add ONE semantic hashtag if space allows
        semantic_tag = self._get_semantic_hashtag(angle)
        if len(main_content) + len(semantic_tag) < available_space - 5:
            main_content = f"{main_content} {semantic_tag}"
        
        # Ensure we don't exceed available space
        if len(main_content) > available_space:
            # Trim content if needed
            main_content = main_content[:available_space-3] + "..."
        
        # Compose final tweet with proper spacing
        tweet = f"{main_content}\n\n{promo_block}"
        
        # Final validation
        if self.calculate_twitter_length(tweet) > 260:
            # Emergency trim - use short URL
            short_promo = "EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 https://vtgpu.ai/promo"
            tweet = f"{main_content[:180]}\n\n{short_promo}"
        
        return tweet
    
    def _get_semantic_hashtag(self, angle: str) -> str:
        """Get ONE semantic hashtag for the angle"""
        semantic_map = {
            "cost": "#CloudCost",
            "latency": "#LowLatency",
            "autoscale": "#AutoScale",
            "regions": "#GlobalDeploy",
            "uptime": "#HighAvailability",
            "support": "#DevSupport"
        }
        return semantic_map.get(angle, "")
    
    def validate_production_tweet(self, tweet: str) -> Dict[str, any]:
        """Strict production validation"""
        
        # Calculate actual Twitter length
        twitter_length = self.calculate_twitter_length(tweet)
        
        # Count hashtags
        hashtag_count = self.count_hashtags(tweet)
        
        # Check caps ratio
        caps_ratio = self.check_caps_ratio(tweet)
        
        # Check English
        is_english = self.is_english_loose(tweet)
        
        # Check promo code presence (exact match)
        has_promo = "EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2" in tweet
        
        # Check URL presence
        has_url = "voltagegpu.com" in tweet or "vtgpu.ai" in tweet
        
        validations = {
            "has_promo": has_promo,
            "has_url": has_url,
            "length_ok": twitter_length <= 260,
            "twitter_length": twitter_length,
            "has_hashtag": hashtag_count >= 1,
            "max_2_hashtags": hashtag_count <= 2,
            "hashtag_count": hashtag_count,
            "english": is_english,
            "no_excessive_caps": caps_ratio < 0.3,
            "caps_ratio": round(caps_ratio, 2)
        }
        
        validations["all_valid"] = all([
            validations["has_promo"],
            validations["has_url"],
            validations["length_ok"],
            validations["has_hashtag"],
            validations["max_2_hashtags"],
            validations["english"],
            validations["no_excessive_caps"]
        ])
        
        return validations
