"""
Test du système avec les VRAIS hashtags du TOP 10 mondial
"""

import asyncio
import logging
from app.composer import TweetComposer
from app.config import Config
from app.store import Store
from app.trends import TrendsManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_real_trends():
    print("\n" + "="*60)
    print("🌍 TEST: TWEET AVEC VRAIS HASHTAGS TOP 10 MONDIAL")
    print("="*60 + "\n")
    
    # Initialize components
    config = Config()
    store = Store(config)
    await store.initialize()
    trends = TrendsManager(config, store)
    composer = TweetComposer(config, store, trends)
    
    # Generate 3 tweets to see variety
    for i in range(3):
        print(f"\n📝 TWEET #{i+1}:")
        print("-" * 50)
        
        tweet = await composer.compose_tweet('A' if i % 2 == 0 else 'B')
        
        if tweet:
            print(tweet)
            print(f"\n📊 Length: {len(tweet)} chars")
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', tweet)
            print(f"🏷️ Hashtags used: {', '.join(hashtags)}")
            
            # Check if domain hashtag is present
            domain_tags = ['#GPU', '#AI', '#Cloud', '#MachineLearning', '#DeepLearning', '#GPUCompute']
            has_domain = any(tag in tweet for tag in domain_tags)
            print(f"✅ Domain hashtag present: {has_domain}")
        else:
            print("❌ Failed to generate tweet")
        
        print("-" * 50)
        await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE - Check if hashtags are from TOP 10 WORLD")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_real_trends())
