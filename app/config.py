"""Configuration management for VoltageGPU Twitter Bot."""

import os
import pytz
from typing import Tuple, Dict, Optional
from datetime import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Twitter bot."""
    
    def __init__(self):
        # Twitter API credentials for Account A
        self.X1_API_KEY = os.getenv("X1_API_KEY")
        self.X1_API_SECRET = os.getenv("X1_API_SECRET")
        self.X1_ACCESS_TOKEN = os.getenv("X1_ACCESS_TOKEN")
        self.X1_ACCESS_SECRET = os.getenv("X1_ACCESS_SECRET")
        self.X1_BEARER_TOKEN = os.getenv("X1_BEARER_TOKEN")
        
        # Twitter API credentials for Account B
        self.X2_API_KEY = os.getenv("X2_API_KEY")
        self.X2_API_SECRET = os.getenv("X2_API_SECRET")
        self.X2_ACCESS_TOKEN = os.getenv("X2_ACCESS_TOKEN")
        self.X2_ACCESS_SECRET = os.getenv("X2_ACCESS_SECRET")
        self.X2_BEARER_TOKEN = os.getenv("X2_BEARER_TOKEN")
        
        # Bot configuration
        self.TIMEZONE = os.getenv("TIMEZONE", "Europe/Paris")
        self.timezone = pytz.timezone(self.TIMEZONE)
        self.DAILY_WRITES_TARGET_PER_ACCOUNT = int(os.getenv("DAILY_WRITES_TARGET_PER_ACCOUNT", "10"))
        self.daily_writes_target = self.DAILY_WRITES_TARGET_PER_ACCOUNT
        self.POST_WINDOW_LOCAL = os.getenv("POST_WINDOW_LOCAL", "09:00-23:30")
        self.ACCOUNT_ORDER = os.getenv("ACCOUNT_ORDER", "A_FIRST")
        self.MIN_GAP_BETWEEN_ACCOUNTS_MIN = int(os.getenv("MIN_GAP_BETWEEN_ACCOUNTS_MIN", "45"))
        self.min_gap_between_accounts = self.MIN_GAP_BETWEEN_ACCOUNTS_MIN
        self.INTERVAL_MIN = int(os.getenv("INTERVAL_MIN", "90"))
        self.post_interval_minutes = self.INTERVAL_MIN
        
        # Parse posting window
        start_str, end_str = self.POST_WINDOW_LOCAL.split("-")
        start_hour, start_min = map(int, start_str.split(":"))
        end_hour, end_min = map(int, end_str.split(":"))
        self.post_window_start = time(start_hour, start_min)
        self.post_window_end = time(end_hour, end_min)
        
        # Optional settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DATA_DIR = os.getenv("DATA_DIR", "./data")
        
        # Constants
        self.PROMO_CODE = "SHA-256-C7E8976BBAF2"
        self.BASE_URL = "https://voltagegpu.com"
        self.MAX_TWEET_LENGTH = 260
        self.MAX_HASHTAGS = 3
        
        # API Read Management
        self.X_READS_MODE = os.getenv("X_READS_MODE", "conservative")  # conservative or normal
        self.MAX_READS_PER_DAY = int(os.getenv("MAX_READS_PER_DAY", "3"))  # Free tier: 100/month ≈ 3/day
        self.MAX_READS_PER_MONTH = int(os.getenv("MAX_READS_PER_MONTH", "100"))
        
        # Relevance filtering
        self.MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.55"))
        self.AI_GPU_KEYWORDS = [
            'gpu', 'ai', 'cloud', 'llm', 'inference', 'training', 'rendering',
            'compute', 'ml', 'deep learning', 'neural', 'model', 'latency',
            'autoscale', 'kubernetes', 'docker', 'api', 'performance', 'cost'
        ]
    
    def get_twitter_credentials(self, account_id: str) -> Dict[str, str]:
        """Get Twitter credentials for specified account."""
        if account_id == 'A':
            return {
                'api_key': self.X1_API_KEY,
                'api_secret': self.X1_API_SECRET,
                'access_token': self.X1_ACCESS_TOKEN,
                'access_secret': self.X1_ACCESS_SECRET,
                'bearer_token': self.X1_BEARER_TOKEN
            }
        elif account_id == 'B':
            return {
                'api_key': self.X2_API_KEY,
                'api_secret': self.X2_API_SECRET,
                'access_token': self.X2_ACCESS_TOKEN,
                'access_secret': self.X2_ACCESS_SECRET,
                'bearer_token': self.X2_BEARER_TOKEN
            }
        else:
            raise ValueError(f"Invalid account ID: {account_id}")
    
    def has_account_b(self) -> bool:
        """Check if Account B credentials are configured."""
        return all([
            self.X2_API_KEY,
            self.X2_API_SECRET,
            self.X2_ACCESS_TOKEN,
            self.X2_ACCESS_SECRET,
            self.X2_BEARER_TOKEN
        ])
    
    def get_post_window(self) -> Tuple[time, time]:
        """Parse and return the posting window as time objects."""
        return self.post_window_start, self.post_window_end
    
    def get_utm_url(self, account: str, hashtags: str = "") -> str:
        """Generate UTM-tagged URL for tracking."""
        utm_params = {
            "utm_source": "twitter",
            "utm_medium": "social",
            "utm_campaign": f"promo_{self.PROMO_CODE}",
            "utm_content": account,
            "utm_term": hashtags.replace("#", "").replace(" ", "_")
        }
        
        param_string = "&".join([f"{k}={v}" for k, v in utm_params.items() if v])
        return f"{self.BASE_URL}/?{param_string}"
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        required_vars = [
            self.X1_API_KEY, self.X1_API_SECRET, self.X1_ACCESS_TOKEN, 
            self.X1_ACCESS_SECRET, self.X1_BEARER_TOKEN
        ]
        
        # Account B is optional
        return all(var is not None and var.strip() != "" for var in required_vars)

# Create global config instance
config = Config()
