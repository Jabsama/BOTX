"""
Twitter client wrapper for posting and searching tweets.
Handles both account A and B with proper rate limiting and error handling.
"""

import asyncio
import logging
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
import tweepy
from tweepy import TooManyRequests, Forbidden, BadRequest

from .config import Config

logger = logging.getLogger(__name__)


class TwitterClient:
    """Wrapper for Twitter API operations."""
    
    def __init__(self, config: Config, account_id: str):
        self.config = config
        self.account_id = account_id
        self.api = None
        self.client = None
        self.bearer_client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Twitter API client."""
        try:
            # Get credentials for this account
            creds = self.config.get_twitter_credentials(self.account_id)
            
            # Initialize v1.1 API (for some operations)
            auth = tweepy.OAuthHandler(creds['api_key'], creds['api_secret'])
            auth.set_access_token(creds['access_token'], creds['access_secret'])
            # IMPORTANT: wait_on_rate_limit=False to keep accounts independent
            self.api = tweepy.API(auth, wait_on_rate_limit=False)
            
            # Initialize v2 client (for posting)
            # IMPORTANT: wait_on_rate_limit=False to avoid blocking other accounts
            self.client = tweepy.Client(
                bearer_token=creds['bearer_token'],
                consumer_key=creds['api_key'],
                consumer_secret=creds['api_secret'],
                access_token=creds['access_token'],
                access_token_secret=creds['access_secret'],
                wait_on_rate_limit=False  # Don't block the entire bot!
            )
            
            # Bearer-only client for search operations
            self.bearer_client = tweepy.Client(
                bearer_token=creds['bearer_token'],
                wait_on_rate_limit=False  # Don't block for searches either
            )
            
            logger.info(f"Twitter client initialized for account {self.account_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client for account {self.account_id}: {e}")
            raise
    
    async def verify_credentials(self) -> bool:
        """Verify that the API credentials are valid."""
        try:
            user = self.api.verify_credentials()
            if user:
                logger.info(f"Account {self.account_id} verified: @{user.screen_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify credentials for account {self.account_id}: {e}")
            return False
    
    async def post_tweet(self, text: str, media_url: Optional[str] = None) -> Optional[str]:
        """Post a tweet with optional media (GIF) and return the tweet ID."""
        try:
            # Add some randomization to avoid detection
            await asyncio.sleep(random.uniform(1, 3))
            
            media_ids = []
            
            # Upload media if provided
            if media_url:
                try:
                    import requests
                    import tempfile
                    import os
                    
                    # Download the GIF
                    response = requests.get(media_url, timeout=10)
                    if response.status_code == 200:
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp_file:
                            tmp_file.write(response.content)
                            tmp_path = tmp_file.name
                        
                        try:
                            # Upload media using v1.1 API
                            media = self.api.media_upload(tmp_path)
                            media_ids.append(media.media_id)
                            logger.info(f"Uploaded GIF for account {self.account_id}: {media.media_id}")
                        finally:
                            # Clean up temp file
                            os.unlink(tmp_path)
                    
                except Exception as e:
                    logger.warning(f"Failed to upload GIF for account {self.account_id}: {e}")
                    # Continue without media
            
            # Post tweet with or without media
            if media_ids:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.client.create_tweet(text=text, media_ids=media_ids)
                )
            else:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.client.create_tweet(text=text)
                )
            
            if response and response.data:
                tweet_id = response.data['id']
                logger.info(f"Account {self.account_id} posted tweet {tweet_id}: {text[:50]}...")
                return tweet_id
            
            return None
            
        except TooManyRequests:
            logger.error(f"Rate limit exceeded for account {self.account_id}")
            return None
        except Forbidden as e:
            logger.error(f"Forbidden error for account {self.account_id}: {e}")
            return None
        except BadRequest as e:
            logger.error(f"Bad request for account {self.account_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting tweet for account {self.account_id}: {e}")
            return None
    
    def search_recent_tweets(self, query: str, max_results: int = 60, 
                           tweet_fields: List[str] = None) -> Any:
        """
        Search for recent tweets matching the query.
        Uses bearer token for higher rate limits.
        """
        try:
            if tweet_fields is None:
                tweet_fields = ['created_at', 'entities', 'lang', 'public_metrics']
            
            # Use bearer client for search (higher rate limits)
            tweets = self.bearer_client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=tweet_fields
            )
            
            logger.info(f"Search completed for query: {query[:50]}...")
            return tweets
            
        except TooManyRequests:
            logger.warning(f"Rate limit exceeded for search on account {self.account_id}")
            return None
        except Exception as e:
            logger.error(f"Error searching tweets on account {self.account_id}: {e}")
            return None
    
    async def get_user_timeline(self, user_id: str = None, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a user's timeline."""
        try:
            if not user_id:
                # Get own user ID
                me = self.client.get_me()
                if me and me.data:
                    user_id = me.data.id
                else:
                    return []
            
            tweets = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.get_users_tweets,
                user_id,
                None,  # exclude
                None,  # expansions
                max_results,
                None,  # media_fields
                None,  # pagination_token
                None,  # place_fields
                None,  # poll_fields
                None,  # since_id
                None,  # start_time
                ['created_at', 'entities'],  # tweet_fields
                None,  # until_id
                None   # user_fields
            )
            
            if not tweets or not tweets.data:
                return []
            
            results = []
            for tweet in tweets.data:
                results.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting timeline for account {self.account_id}: {e}")
            return []
    
    async def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet by ID."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.delete_tweet,
                tweet_id
            )
            
            if response and response.data and response.data.get('deleted'):
                logger.info(f"Account {self.account_id} deleted tweet {tweet_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting tweet {tweet_id} for account {self.account_id}: {e}")
            return False


class TwitterClientManager:
    """Manager for multiple Twitter clients."""
    
    def __init__(self, config: Config):
        """Initialize the client manager."""
        self.config = config
        self.clients = {}
        
    async def initialize(self):
        """Initialize all Twitter clients."""
        try:
            # Initialize Account A
            self.clients['A'] = TwitterClient(self.config, 'A')
            if not await self.clients['A'].verify_credentials():
                logger.warning("Account A credentials could not be verified")
            
            # Initialize Account B if credentials exist
            if self.config.has_account_b():
                self.clients['B'] = TwitterClient(self.config, 'B')
                if not await self.clients['B'].verify_credentials():
                    logger.warning("Account B credentials could not be verified")
            else:
                logger.info("Account B credentials not configured")
            
            logger.info(f"Initialized {len(self.clients)} Twitter client(s)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter clients: {e}")
            raise
    
    def get_client(self, account_id: str) -> Optional[TwitterClient]:
        """Get client for specified account."""
        return self.clients.get(account_id)
    
    def get_all_clients(self) -> Dict[str, TwitterClient]:
        """Get all initialized clients."""
        return self.clients
    
    def get_search_client(self) -> Optional[TwitterClient]:
        """Get a client suitable for search operations (prefers account with bearer token)."""
        # Prefer Account A for search operations
        if 'A' in self.clients:
            return self.clients['A']
        elif 'B' in self.clients:
            return self.clients['B']
        return None
    
    async def post_tweet(self, account_id: str, text: str, media_url: Optional[str] = None) -> Optional[str]:
        """Post tweet with optional media using specified account."""
        client = self.get_client(account_id)
        if not client:
            logger.error(f"No client available for account {account_id}")
            return None
        
        return await client.post_tweet(text, media_url)
    
    def search_recent_tweets(self, query: str, max_results: int = 60) -> Any:
        """Search for recent tweets using the best available client."""
        client = self.get_search_client()
        if not client:
            logger.error("No client available for search operations")
            return None
        
        return client.search_recent_tweets(query, max_results)
