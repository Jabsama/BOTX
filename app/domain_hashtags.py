"""
Domain hashtag management - ensures at least one AI/GPU/Cloud related hashtag
"""

import re
from typing import List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DomainHashtagManager:
    """Manages domain-specific hashtags for AI/GPU/Cloud computing"""
    
    # Domain keywords for semantic matching (not hardcoded hashtags)
    DOMAIN_KEYWORDS = [
        "ai", "artificial", "intelligence", "gpu", "compute", "computing",
        "cloud", "inference", "training", "latency", "autoscale", "scaling",
        "llm", "model", "serving", "acceleration", "nvidia", "cuda",
        "transformer", "pytorch", "tensorflow", "deployment", "serverless",
        "kubernetes", "docker", "api", "endpoint", "performance", "optimization",
        "machine", "learning", "deep", "neural", "network", "algorithm",
        "data", "processing", "parallel", "distributed", "cluster", "node",
        "instance", "pod", "container", "orchestration", "infrastructure",
        "bandwidth", "throughput", "latency", "uptime", "availability",
        "cost", "pricing", "budget", "enterprise", "startup", "scale"
    ]
    
    def __init__(self, min_relevance: float = 0.65):
        self.min_relevance = min_relevance
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.domain_vector = None
        self._init_domain_vector()
    
    def _init_domain_vector(self):
        """Initialize the domain relevance vector"""
        # Create a weighted domain text
        domain_text = " ".join(self.DOMAIN_KEYWORDS * 3)
        self.domain_vector = self.vectorizer.fit_transform([domain_text])
    
    def calculate_domain_relevance(self, hashtag: str) -> float:
        """Calculate how relevant a hashtag is to the AI/GPU domain"""
        # Clean hashtag
        clean_tag = hashtag.lstrip('#').replace('_', ' ').lower()
        
        # Direct keyword match gets high score
        for keyword in self.DOMAIN_KEYWORDS:
            if keyword in clean_tag:
                return 0.85
        
        # Calculate semantic similarity
        try:
            tag_vector = self.vectorizer.transform([clean_tag])
            similarity = cosine_similarity(tag_vector, self.domain_vector)[0][0]
            return similarity
        except:
            return 0.0
    
    def is_domain_hashtag(self, hashtag: str) -> bool:
        """Check if a hashtag is domain-relevant"""
        return self.calculate_domain_relevance(hashtag) >= self.min_relevance
    
    def pick_best_domain_tag(self, candidates: List[str]) -> Optional[str]:
        """Select the most domain-relevant hashtag from candidates"""
        best_tag = None
        best_score = 0.0
        
        for tag in candidates:
            score = self.calculate_domain_relevance(tag)
            if score > best_score and score >= self.min_relevance:
                best_tag = tag
                best_score = score
        
        return best_tag
    
    def synthesize_domain_tag(self, angle: str, topic: str = "") -> str:
        """Generate a domain hashtag based on angle and topic"""
        # Map angles to domain concepts
        angle_map = {
            "cost": ["CloudCost", "GPUPricing", "ComputeBudget"],
            "latency": ["LowLatency", "EdgeCompute", "FastInference"],
            "autoscale": ["AutoScale", "ElasticGPU", "DynamicCompute"],
            "regions": ["GlobalGPU", "MultiRegion", "EdgeDeploy"],
            "uptime": ["HighAvailability", "GPUUptime", "ReliableCompute"],
            "support": ["GPUSupport", "CloudExperts", "TechSupport"]
        }
        
        # Default domain tags if angle not found
        default_tags = [
            "GPUCompute", "AIInference", "CloudGPU", "MLCompute",
            "DeepLearning", "AITraining", "GPUCloud", "ComputePower"
        ]
        
        # Get tags for angle or use defaults
        options = angle_map.get(angle, default_tags)
        
        # Pick one based on topic relevance or randomly
        import random
        selected = random.choice(options)
        
        return f"#{selected}"
    
    def select_hashtags_with_domain(
        self, 
        trend_hashtags: List[str], 
        semantic_hashtags: List[str],
        angle: str = "general",
        require_domain: bool = True,
        max_hashtags: int = 2
    ) -> List[str]:
        """
        Select hashtags ensuring at least one is domain-relevant
        
        Rules:
        - Maximum 2 hashtags total
        - At least 1 must be domain-relevant (AI/GPU/Cloud)
        - Prefer 1 trend + 1 domain
        """
        selected = []
        
        # First, try to find a domain-relevant trend
        domain_trend = self.pick_best_domain_tag(trend_hashtags)
        
        if domain_trend:
            # We have a domain-relevant trend, use it
            selected.append(domain_trend)
            
            # Add one more non-domain trend if available and different
            for trend in trend_hashtags:
                if trend != domain_trend and len(selected) < max_hashtags:
                    selected.append(trend)
                    break
        else:
            # No domain trend, pick best regular trend
            if trend_hashtags:
                selected.append(trend_hashtags[0])
            
            # Must add a domain hashtag
            if require_domain:
                # Try semantic hashtags first
                domain_semantic = self.pick_best_domain_tag(semantic_hashtags)
                
                if domain_semantic and domain_semantic not in selected:
                    selected.append(domain_semantic)
                else:
                    # Generate one based on angle
                    generated = self.synthesize_domain_tag(angle)
                    if generated not in selected:
                        selected.append(generated)
        
        # Ensure we don't exceed max
        return selected[:max_hashtags]
    
    def validate_hashtags(self, hashtags: List[str], require_domain: bool = True) -> Tuple[bool, str]:
        """
        Validate that hashtags meet requirements
        
        Returns: (is_valid, error_message)
        """
        if len(hashtags) > 2:
            return False, f"Too many hashtags: {len(hashtags)} (max 2)"
        
        if len(hashtags) == 0:
            return False, "No hashtags present"
        
        if require_domain:
            has_domain = any(self.is_domain_hashtag(tag) for tag in hashtags)
            if not has_domain:
                return False, "Missing domain-relevant hashtag (AI/GPU/Cloud)"
        
        return True, "Valid"
    
    def get_hashtag_info(self, hashtag: str) -> dict:
        """Get detailed information about a hashtag"""
        relevance = self.calculate_domain_relevance(hashtag)
        is_domain = relevance >= self.min_relevance
        
        return {
            "hashtag": hashtag,
            "domain_relevance": round(relevance, 3),
            "is_domain": is_domain,
            "category": "domain" if is_domain else "trend"
        }
