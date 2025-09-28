"""
Unit tests for the scheduler module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, time
import pytz

from app.scheduler import PostScheduler
from app.config import Config
from app.store import Store
from app.twitter_client import TwitterClient
from app.composer import TweetComposer
from app.trends import TrendsManager


class TestPostScheduler:
    """Test suite for PostScheduler."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.timezone = pytz.timezone('Europe/Paris')
        config.post_interval_minutes = 90
        config.min_gap_between_accounts = 45
        config.daily_writes_target = 10
        config.post_window_start = time(9, 0)
        config.post_window_end = time(23, 30)
        return config
    
    @pytest.fixture
    def mock_store(self):
        """Create mock store."""
        store = Mock(spec=Store)
        store.record_post = AsyncMock()
        return store
    
    @pytest.fixture
    def mock_twitter_clients(self):
        """Create mock Twitter clients."""
        client_a = Mock(spec=TwitterClient)
        client_a.post_tweet = AsyncMock(return_value='tweet_id_a')
        
        client_b = Mock(spec=TwitterClient)
        client_b.post_tweet = AsyncMock(return_value='tweet_id_b')
        
        return {'A': client_a, 'B': client_b}
    
    @pytest.fixture
    def mock_composer(self):
        """Create mock composer."""
        composer = Mock(spec=TweetComposer)
        composer.compose_tweet = AsyncMock(side_effect=lambda account: f"Test tweet for {account}")
        return composer
    
    @pytest.fixture
    def mock_trends_manager(self):
        """Create mock trends manager."""
        trends = Mock(spec=TrendsManager)
        trends.refresh_trends = AsyncMock(return_value=[])
        return trends
    
    @pytest.fixture
    def scheduler(self, mock_config, mock_store):
        """Create scheduler instance."""
        return PostScheduler(mock_config, mock_store)
    
    def test_initialization(self, scheduler, mock_twitter_clients, mock_composer, mock_trends_manager):
        """Test scheduler initialization."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        
        assert scheduler.twitter_clients == mock_twitter_clients
        assert scheduler.composer == mock_composer
        assert scheduler.trends_manager == mock_trends_manager
    
    @pytest.mark.asyncio
    async def test_post_for_account_success(self, scheduler, mock_twitter_clients, 
                                           mock_composer, mock_trends_manager, mock_store):
        """Test successful post for an account."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        
        # Mock within posting window
        with patch.object(scheduler, '_is_within_window', return_value=True):
            await scheduler._post_for_account('A')
        
        # Verify tweet was composed and posted
        mock_composer.compose_tweet.assert_called_once_with('A')
        mock_twitter_clients['A'].post_tweet.assert_called_once()
        mock_store.record_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_for_account_outside_window(self, scheduler, mock_twitter_clients,
                                                  mock_composer, mock_trends_manager):
        """Test that posts are skipped outside posting window."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        
        # Mock outside posting window
        with patch.object(scheduler, '_is_within_window', return_value=False):
            await scheduler._post_for_account('A')
        
        # Verify no tweet was composed
        mock_composer.compose_tweet.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_post_for_account_daily_limit(self, scheduler, mock_twitter_clients,
                                               mock_composer, mock_trends_manager):
        """Test that posts respect daily limit."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        scheduler.daily_posts['A'] = 10  # Already at limit
        
        with patch.object(scheduler, '_is_within_window', return_value=True):
            await scheduler._post_for_account('A')
        
        # Verify no tweet was composed
        mock_composer.compose_tweet.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_account_gap_enforcement(self, scheduler, mock_twitter_clients,
                                          mock_composer, mock_trends_manager, mock_config):
        """Test minimum gap between accounts is enforced."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        
        # Set last post time for account B
        now = datetime.now(mock_config.timezone)
        scheduler.last_post_times['B'] = now - timedelta(minutes=30)  # 30 minutes ago
        
        with patch.object(scheduler, '_is_within_window', return_value=True):
            with patch.object(asyncio, 'sleep') as mock_sleep:
                await scheduler._post_for_account('A')
                
                # Should wait 15 more minutes (45 - 30)
                mock_sleep.assert_called()
                wait_time = mock_sleep.call_args[0][0]
                assert 14 * 60 < wait_time < 16 * 60  # Allow some tolerance
    
    def test_is_within_window(self, scheduler, mock_config):
        """Test posting window check."""
        # During window
        dt1 = mock_config.timezone.localize(datetime(2024, 1, 1, 12, 0))
        assert scheduler._is_within_window(dt1)
        
        # Before window
        dt2 = mock_config.timezone.localize(datetime(2024, 1, 1, 8, 0))
        assert not scheduler._is_within_window(dt2)
        
        # After window
        dt3 = mock_config.timezone.localize(datetime(2024, 1, 1, 23, 45))
        assert not scheduler._is_within_window(dt3)
    
    def test_extract_hashtags(self, scheduler):
        """Test hashtag extraction from content."""
        content = "Check out #AI and #GPU computing with #CloudServices"
        hashtags = scheduler._extract_hashtags(content)
        
        assert len(hashtags) == 3
        assert '#AI' in hashtags
        assert '#GPU' in hashtags
        assert '#CloudServices' in hashtags
    
    @pytest.mark.asyncio
    async def test_reset_daily_counters(self, scheduler, mock_config):
        """Test daily counter reset."""
        scheduler.daily_posts = {'A': 5, 'B': 7}
        scheduler.last_reset_date = datetime.now(mock_config.timezone).date() - timedelta(days=1)
        
        await scheduler._reset_daily_counters()
        
        assert scheduler.daily_posts['A'] == 0
        assert scheduler.daily_posts['B'] == 0
        assert scheduler.last_reset_date == datetime.now(mock_config.timezone).date()
    
    def test_get_status(self, scheduler, mock_config):
        """Test status retrieval."""
        scheduler.daily_posts = {'A': 3, 'B': 2}
        scheduler.last_post_times = {
            'A': datetime.now(mock_config.timezone),
            'B': datetime.now(mock_config.timezone)
        }
        
        # Mock scheduler running state
        scheduler.scheduler.running = True
        
        status = scheduler.get_status()
        
        assert status['scheduler_running'] is True
        assert status['account_a']['posted_today'] == 3
        assert status['account_b']['posted_today'] == 2
        assert status['daily_target'] == mock_config.daily_writes_target
        assert 'posting_window' in status
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler, mock_twitter_clients,
                                  mock_composer, mock_trends_manager):
        """Test scheduler start process."""
        scheduler.initialize(mock_twitter_clients, mock_composer, mock_trends_manager)
        
        with patch.object(scheduler.scheduler, 'start'):
            with patch.object(scheduler.scheduler, 'add_job'):
                with patch.object(scheduler, '_schedule_initial_posts', new_callable=AsyncMock):
                    await scheduler.start()
                    
                    # Verify scheduler was started
                    scheduler.scheduler.start.assert_called_once()
                    
                    # Verify jobs were scheduled
                    assert scheduler.scheduler.add_job.call_count >= 2  # At least trends and daily reset
                    
                    # Verify initial posts were scheduled
                    scheduler._schedule_initial_posts.assert_called_once()
                    
                    # Verify trends were refreshed
                    mock_trends_manager.refresh_trends.assert_called_once()
