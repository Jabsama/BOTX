"""
Main application entry point for VoltageGPU Twitter Bot.
Orchestrates all components and manages the bot lifecycle.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional
import click

from .config import Config
from .store import Store
from .twitter_client import TwitterClientManager
from .trends import TrendsManager
from .composer import TweetComposer
from .scheduler import PostScheduler
from .tracker import StatusTracker, json_logger

# Import rate limit tracker and posting timer
try:
    from .rate_limit_tracker import rate_limit_tracker
    from .posting_timer import start_posting_timer
except ImportError:
    rate_limit_tracker = None
    start_posting_timer = None

# Configure logging with UTF-8 encoding for Windows
import sys
import io

# Force UTF-8 for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class VoltageGPUBot:
    """Main bot application class."""
    
    def __init__(self):
        self.config = None
        self.store = None
        self.twitter_manager = None
        self.trends_manager = None
        self.composer = None
        self.scheduler = None
        self.tracker = None
        self.running = False
        
    async def initialize(self):
        """Initialize all bot components."""
        try:
            logger.info("Initializing VoltageGPU Twitter Bot...")
            
            # Initialize configuration
            self.config = Config()
            logger.info(f"Configuration loaded - Timezone: {self.config.timezone}")
            
            # Initialize database
            self.store = Store(self.config)
            await self.store.initialize()
            logger.info("Database initialized")
            
            # Initialize Twitter clients
            self.twitter_manager = TwitterClientManager(self.config)
            await self.twitter_manager.initialize()
            logger.info(f"Twitter clients initialized: {len(self.twitter_manager.clients)} accounts")
            
            # Initialize trends manager
            self.trends_manager = TrendsManager(self.config, self.store)
            search_client = self.twitter_manager.get_search_client()
            if search_client:
                self.trends_manager.set_twitter_client(search_client)
            logger.info("Trends manager initialized")
            
            # Initialize composer
            self.composer = TweetComposer(self.config, self.store, self.trends_manager)
            logger.info("Tweet composer initialized")
            
            # Initialize scheduler
            self.scheduler = PostScheduler(self.config, self.store)
            self.scheduler.initialize(
                self.twitter_manager.get_all_clients(),
                self.composer,
                self.trends_manager
            )
            logger.info("Scheduler initialized")
            
            # Initialize tracker
            self.tracker = StatusTracker(self.config, self.store)
            self.tracker.set_components(self.scheduler, self.trends_manager)
            logger.info("Status tracker initialized")
            
            # Log successful initialization
            json_logger.info("Bot initialized successfully", 
                           accounts=len(self.twitter_manager.clients))
            
            logger.info("VoltageGPU Twitter Bot initialization complete!")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            json_logger.error("Bot initialization failed", error=str(e))
            raise
    
    async def start(self):
        """Start the bot and all services."""
        try:
            logger.info("Starting VoltageGPU Twitter Bot...")
            self.running = True
            
            # Start scheduler
            await self.scheduler.start()
            
            # Start tracker server in background
            tracker_task = asyncio.create_task(
                self.tracker.start_server(host="0.0.0.0", port=8000)
            )
            
            # Rate limit tracker is available but we don't start the visual timer
            # The tracking and auto-retry still work in the background
            if rate_limit_tracker:
                logger.info("Rate limit tracking enabled with auto-retry on rate limits")
            
            logger.info("Bot started successfully!")
            logger.info("Status tracker available at http://localhost:8000/status")
            
            json_logger.info("Bot started", 
                           status_url="http://localhost:8000/status")
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
                # Log periodic status
                if asyncio.get_event_loop().time() % 600 < 60:  # Every 10 minutes
                    # Properly handle async coroutine
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.tracker.log_status())
                    except RuntimeError:
                        await self.tracker.log_status()
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            json_logger.error("Bot runtime error", error=str(e))
            raise
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping VoltageGPU Twitter Bot...")
        self.running = False
        
        try:
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop()
            
            # Close database
            if self.store:
                await self.store.close()
            
            logger.info("Bot stopped successfully")
            json_logger.info("Bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            json_logger.error("Error during shutdown", error=str(e))


# Global bot instance
bot = VoltageGPUBot()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    asyncio.create_task(bot.stop())
    sys.exit(0)


@click.group()
def cli():
    """VoltageGPU Twitter Bot CLI."""
    pass


@cli.command()
def run():
    """Run the bot."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create data directory
    Path('data').mkdir(exist_ok=True)
    
    # Run the bot
    async def main():
        await bot.initialize()
        await bot.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


@cli.command()
def status():
    """Display current bot status."""
    async def get_status():
        await bot.initialize()
        status = await bot.tracker._get_full_status()
        
        print("\n=== VoltageGPU Twitter Bot Status ===\n")
        print(f"Time: {status['now']}")
        print(f"Timezone: {status['timezone']}")
        print(f"Scheduler: {'Running' if status['scheduler_running'] else 'Stopped'}")
        print(f"Posting Window: {status['posting_window']}")
        print()
        
        print("Account A:")
        print(f"  Next Run: {status['account_a']['next_run_local'] or 'Not scheduled'}")
        print(f"  Posted Today: {status['account_a']['posted_today']}")
        print(f"  Last Tweet: {status['account_a']['last_tweet_id'] or 'None'}")
        print()
        
        print("Account B:")
        print(f"  Next Run: {status['account_b']['next_run_local'] or 'Not scheduled'}")
        print(f"  Posted Today: {status['account_b']['posted_today']}")
        print(f"  Last Tweet: {status['account_b']['last_tweet_id'] or 'None'}")
        print()
        
        print(f"Daily Target: {status['writes_budget_today']['target']} posts per account")
        print()
        
        if status['trend_samples']:
            print("Current Trends:")
            for trend in status['trend_samples'][:5]:
                print(f"  {trend}")
        
        await bot.store.close()
    
    asyncio.run(get_status())


@cli.command()
@click.option('--account', '-a', type=click.Choice(['A', 'B']), required=True,
              help='Account to post from')
@click.option('--dry-run', is_flag=True, help='Generate tweet without posting')
def post(account, dry_run):
    """Manually trigger a post."""
    async def manual_post():
        await bot.initialize()
        
        # Generate tweet
        tweet = await bot.composer.compose_tweet(account)
        
        if not tweet:
            print("Failed to compose tweet")
            return
        
        print(f"\nGenerated tweet ({len(tweet)} chars):")
        print("-" * 50)
        print(tweet)
        print("-" * 50)
        
        if not dry_run:
            # Post tweet
            tweet_id = await bot.twitter_manager.post_tweet(account, tweet)
            
            if tweet_id:
                print(f"\nSuccessfully posted! Tweet ID: {tweet_id}")
                
                # Record in database
                hashtags = [tag for tag in tweet.split() if tag.startswith('#')]
                await bot.store.record_post(account, tweet_id, tweet, hashtags)
            else:
                print("\nFailed to post tweet")
        else:
            print("\n(Dry run - tweet not posted)")
        
        await bot.store.close()
    
    asyncio.run(manual_post())


@cli.command()
def trends():
    """Display current trending hashtags."""
    async def show_trends():
        await bot.initialize()
        
        # Refresh trends
        print("Fetching latest trends...")
        trends = await bot.trends_manager.refresh_trends()
        
        print("\n=== Current Trending Hashtags ===\n")
        
        if trends:
            for i, trend in enumerate(trends[:20], 1):
                sources = ', '.join(trend['sources'])
                print(f"{i:2}. {trend['hashtag']:20} Score: {trend['score']:.2f} "
                      f"Sources: [{sources}]")
        else:
            print("No trends available")
        
        await bot.store.close()
    
    asyncio.run(show_trends())


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to analyze')
def metrics(days):
    """Display bot metrics."""
    async def show_metrics():
        await bot.initialize()
        
        print(f"\n=== Bot Metrics (Last {days} Days) ===\n")
        
        # Get metrics
        total_a = await bot.store.get_total_posts('A')
        total_b = await bot.store.get_total_posts('B')
        today_a = await bot.store.get_posts_today('A')
        today_b = await bot.store.get_posts_today('B')
        hashtags = await bot.store.get_unique_hashtags(days)
        
        print(f"Total Posts:")
        print(f"  Account A: {total_a}")
        print(f"  Account B: {total_b}")
        print(f"  Combined: {total_a + total_b}")
        print()
        
        print(f"Posts Today:")
        print(f"  Account A: {today_a}")
        print(f"  Account B: {today_b}")
        print(f"  Combined: {today_a + today_b}")
        print()
        
        print(f"Unique Hashtags Used: {len(hashtags)}")
        
        if hashtags:
            print(f"\nTop 10 Hashtags:")
            for tag in hashtags[:10]:
                print(f"  {tag}")
        
        await bot.store.close()
    
    asyncio.run(show_metrics())


if __name__ == '__main__':
    cli()
