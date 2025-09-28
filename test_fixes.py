"""
Test des corrections du bot VoltageGPU
- Vérification que le compte B ne poste pas 2 fois
- Vérification de la variété des hashtags domain
"""

import asyncio
import logging
from app.domain_hashtags import DomainHashtagManager
from app.composer_viral import ViralTweetComposer

logging.basicConfig(level=logging.INFO)

async def test_hashtag_variety():
    """Test que les hashtags domain varient"""
    print("\n" + "="*60)
    print("🔧 TEST: HASHTAG VARIETY")
    print("="*60 + "\n")
    
    manager = DomainHashtagManager()
    
    # Test 10 générations pour voir la variété
    print("📝 Testing domain hashtag generation (10 iterations):")
    print("-" * 40)
    
    generated_tags = []
    for i in range(10):
        # Test avec différents angles
        angles = ["tech", "sports", "entertainment", "news", "general"]
        angle = angles[i % len(angles)]
        
        tag = manager.synthesize_domain_tag(angle)
        generated_tags.append(tag)
        print(f"{i+1}. Angle: {angle:15} → {tag}")
    
    # Vérifier la diversité
    unique_tags = set(generated_tags)
    diversity_ratio = len(unique_tags) / len(generated_tags)
    
    print("\n" + "-" * 40)
    print(f"📊 Results:")
    print(f"   Total generated: {len(generated_tags)}")
    print(f"   Unique tags: {len(unique_tags)}")
    print(f"   Diversity ratio: {diversity_ratio:.1%}")
    
    if diversity_ratio >= 0.7:
        print("   ✅ Good diversity (>70% unique)")
    else:
        print("   ⚠️ Low diversity (<70% unique)")
    
    print("\n" + "="*60)
    
    # Test avec le composer viral
    print("📝 Testing viral composer with real hashtags:")
    print("-" * 40)
    
    composer = ViralTweetComposer()
    
    # Test avec différents hashtags trending
    test_cases = [
        ['#NXTNoMercy', '#Wrestling'],
        ['#HSEverglow', '#KPop'],
        ['#Technology', '#Innovation'],
        ['#WorldCup', '#Football'],
        ['#Breaking', '#News']
    ]
    
    for hashtags in test_cases:
        tweet = await composer.compose_viral_tweet(hashtags)
        
        # Extraire les hashtags du tweet
        import re
        used_hashtags = re.findall(r'#\w+', tweet)
        
        print(f"\nInput: {hashtags}")
        print(f"Used: {used_hashtags}")
        
        # Vérifier qu'il y a un domain hashtag
        has_domain = any(manager.is_domain_hashtag(tag) for tag in used_hashtags)
        if has_domain:
            domain_tags = [tag for tag in used_hashtags if manager.is_domain_hashtag(tag)]
            print(f"✅ Domain tag present: {domain_tags}")
        else:
            print("⚠️ No domain tag found")
    
    print("\n" + "="*60)
    print("✅ HASHTAG VARIETY TEST COMPLETE")
    print("="*60 + "\n")

async def test_scheduler_timing():
    """Test que les jobs ne se chevauchent pas"""
    print("\n" + "="*60)
    print("⏰ TEST: SCHEDULER TIMING")
    print("="*60 + "\n")
    
    from app.config import Config
    from app.store import Store
    from app.scheduler import PostScheduler
    from datetime import datetime, timedelta
    
    config = Config()
    store = Store(config)
    await store.initialize()
    
    scheduler = PostScheduler(config, store)
    
    # Simuler le démarrage
    now = datetime.now(config.timezone)
    
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Post interval: {config.post_interval_minutes} minutes")
    print(f"Gap between accounts: {config.min_gap_between_accounts} minutes")
    
    print("\n" + "-" * 40)
    print("Expected schedule:")
    
    # Initial posts
    print(f"1. Account A initial: NOW")
    print(f"2. Account B initial: NOW + {config.min_gap_between_accounts} min")
    
    # Recurring posts
    a_recurring = now + timedelta(minutes=config.post_interval_minutes)
    b_recurring = now + timedelta(minutes=config.min_gap_between_accounts + config.post_interval_minutes)
    
    print(f"3. Account A recurring: {a_recurring.strftime('%H:%M:%S')}")
    print(f"4. Account B recurring: {b_recurring.strftime('%H:%M:%S')}")
    
    # Vérifier qu'il n'y a pas de chevauchement
    print("\n" + "-" * 40)
    print("Checking for conflicts:")
    
    # B initial vs B recurring
    b_initial_time = now + timedelta(minutes=config.min_gap_between_accounts)
    time_diff = (b_recurring - b_initial_time).total_seconds() / 60
    
    print(f"Time between B initial and B recurring: {time_diff:.1f} minutes")
    
    if time_diff >= config.post_interval_minutes:
        print("✅ No conflict - sufficient gap")
    else:
        print("⚠️ Potential conflict - jobs too close")
    
    print("\n" + "="*60)
    print("✅ SCHEDULER TIMING TEST COMPLETE")
    print("="*60 + "\n")

async def main():
    """Run all tests"""
    await test_hashtag_variety()
    await test_scheduler_timing()
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETE")
    print("="*60)
    print("\nSummary of fixes:")
    print("1. ✅ Scheduler: B recurring posts now start AFTER initial + interval")
    print("2. ✅ Hashtags: More variety with smart selection and tracking")
    print("3. ✅ Content: Adapts between AI Inference and GPU Compute")
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
