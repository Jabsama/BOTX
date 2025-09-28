"""
Optimized Tweet Composer with Micro-Templates and Angle Rotation
"""

import random
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import re

class OptimizedComposer:
    """High-performance tweet composer with strict templates"""
    
    # Rotation angles for messaging
    ANGLES = ["cost", "latency", "autoscale", "regions", "uptime", "support"]
    
    # Micro-templates for each angle (≤260 chars)
    TEMPLATES = {
        "cost": {
            "template": "#{trend} is peaking—don't let GPU costs spike too. Spin up on-demand GPUs, pay only for usage, scale back after traffic. Try it now — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} Don't overpay for idle compute. Try it now — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        },
        "latency": {
            "template": "#{trend} demos flop when latency bites. Get low-latency GPU inference in minutes and keep P95 tight. Ship today — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} Keep latency low with instant GPU deployment. Ship today — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        },
        "autoscale": {
            "template": "Traffic from #{trend}? Burst compute when you need it, then scale down. On-demand GPUs in minutes — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} Autoscale seamlessly. Start now — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        },
        "regions": {
            "template": "Going live during #{trend}? Launch GPU pods in multiple regions to cut RTT and speed up users — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} Deploy globally in minutes — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        },
        "uptime": {
            "template": "#{trend} surges aren't a problem with pods you can redeploy in seconds. Stay online — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} 99.9% uptime guaranteed — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        },
        "support": {
            "template": "Shipping during #{trend}? We'll help you size GPUs and deploy faster — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
            "bridge": "{bridge} Expert support 24/7 — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
        }
    }
    
    # Price-aware templates (when fresh data available)
    PRICE_TEMPLATES = {
        "budget": "Need compute for #{trend}? 2× RTX 3090 from $0.46/hr. Start in minutes — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
        "value": "#{trend} workloads? 8× A100-80GB from $6.02/hr. Deploy now — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}",
        "premium": "Enterprise #{trend}? 8× H200 at $26.60/hr. Scale instantly — EXCLUSIVE PROMO CODE SHA-256-C7E8976BBAF2 {url}"
    }
    
    def __init__(self):
        self.angle_index = 0
        self.last_angles = []
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
    
    def get_fresh_prices(self) -> Optional[Dict]:
        """Get fresh price data if available"""
        if not self.prices_file.exists():
            return None
        
        try:
            with open(self.prices_file) as f:
                data = json.load(f)
                # Check if data is fresh (< 24 hours)
                timestamp = datetime.fromisoformat(data.get('timestamp', '2020-01-01'))
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                
                if age_hours < 24:
                    return data.get('offers', {})
                return None
        except:
            return None
    
    def build_utm_url(self, account: str, hashtags: List[str]) -> str:
        """Build URL with full UTM parameters"""
        base_url = "https://voltagegpu.com/"
        utm_params = [
            "utm_source=twitter",
            "utm_medium=social",
            "utm_campaign=promo_SHA-256-C7E8976BBAF2",
            f"utm_content={account}",
            f"utm_term={'+'.join([h.replace('#', '') for h in hashtags[:2]])}",
            f"utm_id={str(uuid.uuid4())[:8]}"
        ]
        return f"{base_url}?{'&'.join(utm_params)}"
    
    def compose_with_template(
        self,
        trend_data: Dict,
        account: str = "account_a",
        use_price: bool = False
    ) -> str:
        """Compose tweet using strict templates"""
        
        # Extract trend info
        hashtag = trend_data['hashtag']
        needs_bridge = trend_data.get('needs_bridge', False)
        bridge_text = trend_data.get('bridge_text', '')
        
        # Get current angle
        angle = self.rotate_angle()
        
        # Build URL with UTM
        url = self.build_utm_url(account, [hashtag])
        
        # Check for fresh prices
        prices = self.get_fresh_prices() if use_price else None
        
        # Use price template if available and 1/3 chance
        if prices and random.random() < 0.33:
            tier = random.choice(['budget', 'value', 'premium'])
            template = self.PRICE_TEMPLATES[tier]
            tweet = template.format(
                trend=hashtag.replace('#', ''),
                url=url
            )
        else:
            # Use angle template
            templates = self.TEMPLATES[angle]
            
            if needs_bridge and bridge_text:
                # Use bridge template
                tweet = templates['bridge'].format(
                    bridge=bridge_text,
                    url=url
                )
            else:
                # Use standard template
                tweet = templates['template'].format(
                    trend=hashtag.replace('#', ''),
                    url=url
                )
        
        # Add semantic hashtag if room (max 2 hashtags total)
        semantic_tags = self._get_semantic_hashtags(hashtag, angle)
        if semantic_tags and len(tweet) < 250:
            # Only add if we have room
            tweet = tweet.replace(url, f"{semantic_tags[0]} {url}")
        
        # Ensure we're under 260 chars
        if len(tweet) > 260:
            # Trim URL parameters if needed
            short_url = "https://vtgpu.ai/promo"
            tweet = tweet.replace(url, short_url)
        
        return tweet
    
    def _get_semantic_hashtags(self, trend: str, angle: str) -> List[str]:
        """Generate semantic hashtags based on trend and angle"""
        semantic_map = {
            "cost": ["#CloudCost", "#PayAsYouGo"],
            "latency": ["#LowLatency", "#EdgeCompute"],
            "autoscale": ["#AutoScale", "#ElasticCompute"],
            "regions": ["#GlobalDeploy", "#MultiRegion"],
            "uptime": ["#HighAvailability", "#ZeroDowntime"],
            "support": ["#DevSupport", "#24x7Support"]
        }
        
        # Return relevant semantic tag for the angle
        tags = semantic_map.get(angle, [])
        return [random.choice(tags)] if tags else []
    
    def validate_tweet(self, tweet: str) -> Dict[str, bool]:
        """Validate tweet meets all requirements"""
        validations = {
            "has_promo": "SHA-256-C7E8976BBAF2" in tweet,
            "has_url": "voltagegpu.com" in tweet or "vtgpu.ai" in tweet,
            "length_ok": len(tweet) <= 260,
            "has_hashtag": "#" in tweet,
            "max_2_hashtags": tweet.count("#") <= 2,
            "english": not re.search(r'[^\x00-\x7F]+', tweet),  # ASCII only
            "no_excessive_caps": sum(1 for c in tweet if c.isupper()) / len(tweet) < 0.3
        }
        
        validations["all_valid"] = all(validations.values())
        return validations
    
    def get_angle_distribution(self) -> Dict[str, int]:
        """Get distribution of angles used today"""
        return self.angle_stats
    
    def compose_reply(self, trend: str, parent_tweet_id: str) -> Optional[str]:
        """Compose a light engagement reply"""
        replies = [
            "Quick benchmark: our GPUs cut inference time by 73% vs traditional cloud. Try it free with code SHA-256-C7E8976BBAF2 vtgpu.ai/promo",
            "Pro tip: autoscale GPU pods based on queue depth, not just CPU. Details + 5% off with SHA-256-C7E8976BBAF2 vtgpu.ai/promo",
            "We helped a startup handle 10M requests during launch with instant GPU scaling. Get 5% off: SHA-256-C7E8976BBAF2 vtgpu.ai/promo"
        ]
        
        reply = random.choice(replies)
        # Add the trend hashtag
        reply = f"{reply} #{trend.replace('#', '')}"
        
        # Ensure under 260 chars
        if len(reply) > 260:
            reply = reply[:257] + "..."
        
        return reply


class PriceManager:
    """Manage dynamic pricing data"""
    
    def __init__(self):
        self.prices_file = Path("data/offers.json")
        self.default_prices = {
            "gpu_compute": [
                {"name": "8x NVIDIA B200", "price": "$41.86/hr", "tier": "premium"},
                {"name": "8x NVIDIA H200", "price": "$26.60/hr", "tier": "performance"},
                {"name": "8x A100-80GB", "price": "$6.02/hr", "tier": "value"},
                {"name": "5x RTX A6000", "price": "$2.10/hr", "tier": "professional"},
                {"name": "2x RTX 3090", "price": "$0.46/hr", "tier": "budget"}
            ],
            "ai_models": [
                {"name": "gemma-3-12b", "stats": "54.89M runs", "price": "$0.07/M input"},
                {"name": "DeepSeek-R1", "stats": "37.46M runs", "price": "$0.46/M input"},
                {"name": "GLM-4.5-Air", "stats": "2.48M runs", "price": "FREE"},
                {"name": "Llama-3.2-3B", "stats": "1.89M runs", "price": "$0.02/M input"}
            ]
        }
    
    def refresh_prices(self) -> bool:
        """Refresh price data (would connect to API in production)"""
        try:
            # In production, this would fetch from VoltageGPU API
            # For now, use default prices
            data = {
                "offers": self.default_prices,
                "timestamp": datetime.now().isoformat()
            }
            
            self.prices_file.parent.mkdir(exist_ok=True)
            with open(self.prices_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to refresh prices: {e}")
            return False
    
    def get_price_age_hours(self) -> Optional[float]:
        """Get age of price data in hours"""
        if not self.prices_file.exists():
            return None
        
        try:
            with open(self.prices_file) as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data['timestamp'])
                return (datetime.now() - timestamp).total_seconds() / 3600
        except:
            return None
