"""
Unit tests for the tweet composer module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.composer import TweetComposer
from app.config import Config
from app.store import Store
from app.trends import TrendsManager


class TestTweetComposer:
    """Test suite for TweetComposer."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.timezone = 'Europe/Paris'
        return config
    
    @pytest.fixture
    def mock_store(self):
        """Create mock store."""
        store = Mock(spec=Store)
        store.is_duplicate_content = AsyncMock(return_value=False)
        store.get_last_post = AsyncMock(return_value=None)
        return store
    
    @pytest.fixture
    def mock_trends_manager(self):
        """Create mock trends manager."""
        trends = Mock(spec=TrendsManager)
        trends.get_trending_hashtags = AsyncMock(return_value=['#AI', '#GPU'])
        return trends
    
    @pytest.fixture
    def composer(self, mock_config, mock_store, mock_trends_manager):
        """Create composer instance."""
        return TweetComposer(mock_config, mock_store, mock_trends_manager)
    
    @pytest.mark.asyncio
    async def test_compose_tweet_success(self, composer):
        """Test successful tweet composition."""
        tweet = await composer.compose_tweet('A')
        
        assert tweet is not None
        assert len(tweet) <= 280
        assert composer.PROMO_CODE in tweet
        assert composer.BASE_URL in tweet
    
    @pytest.mark.asyncio
    async def test_compose_tweet_includes_hashtags(self, composer, mock_trends_manager):
        """Test that composed tweets include trending hashtags."""
        tweet = await composer.compose_tweet('A')
        
        assert tweet is not None
        # Check if at least one hashtag is present
        assert '#' in tweet
    
    @pytest.mark.asyncio
    async def test_compose_tweet_different_angles(self, composer):
        """Test that different promotional angles are used."""
        tweets = []
        for _ in range(3):
            tweet = await composer.compose_tweet('A')
            if tweet:
                tweets.append(tweet)
        
        # Check that tweets are different
        assert len(set(tweets)) > 1
    
    @pytest.mark.asyncio
    async def test_compose_tweet_account_diversity(self, composer, mock_store):
        """Test that accounts A and B generate different content."""
        # Mock a previous post from account B
        mock_store.get_last_post = AsyncMock(return_value={
            'content': 'Previous tweet content with some words',
            'timestamp': datetime.now().isoformat()
        })
        
        tweet_a = await composer.compose_tweet('A')
        
        # Reset mock for account B
        mock_store.get_last_post = AsyncMock(return_value=None)
        tweet_b = await composer.compose_tweet('B')
        
        assert tweet_a != tweet_b
    
    @pytest.mark.asyncio
    async def test_compose_tweet_duplicate_detection(self, composer, mock_store):
        """Test that duplicate content is regenerated."""
        # First call returns duplicate, second doesn't
        mock_store.is_duplicate_content = AsyncMock(side_effect=[True, False])
        
        tweet = await composer.compose_tweet('A')
        
        assert tweet is not None
        # Should have been called at least twice due to regeneration
        assert mock_store.is_duplicate_content.call_count >= 2
    
    def test_validate_tweet_length(self, composer):
        """Test tweet validation for length."""
        # Too short
        assert not composer._validate_tweet("Hi")
        
        # Too long
        long_tweet = "x" * 281
        assert not composer._validate_tweet(long_tweet)
        
        # Just right
        good_tweet = f"Test tweet {composer.PROMO_CODE} {composer.BASE_URL}"
        assert composer._validate_tweet(good_tweet)
    
    def test_validate_tweet_required_elements(self, composer):
        """Test tweet validation for required elements."""
        # Missing promo code
        tweet1 = f"Test tweet {composer.BASE_URL}"
        assert not composer._validate_tweet(tweet1)
        
        # Missing URL
        tweet2 = f"Test tweet {composer.PROMO_CODE}"
        assert not composer._validate_tweet(tweet2)
        
        # Has both
        tweet3 = f"Test tweet {composer.PROMO_CODE} {composer.BASE_URL}"
        assert composer._validate_tweet(tweet3)
    
    def test_build_utm_params(self, composer):
        """Test UTM parameter building."""
        params = composer._build_utm_params('A', ['#AI', '#GPU'])
        
        assert 'utm_source=twitter' in params
        assert 'utm_medium=social' in params
        assert 'utm_campaign=promo_' in params
        assert 'utm_content=account_a' in params
        assert 'AI_GPU' in params
    
    def test_content_hash_generation(self, composer):
        """Test content hash generation for duplicate detection."""
        content1 = f"Test tweet {composer.PROMO_CODE} {composer.BASE_URL}"
        content2 = f"Different tweet {composer.PROMO_CODE} {composer.BASE_URL}"
        
        hash1 = composer.get_content_hash(content1)
        hash2 = composer.get_content_hash(content2)
        
        assert hash1 != hash2
        
        # Same content should produce same hash
        hash3 = composer.get_content_hash(content1)
        assert hash1 == hash3
