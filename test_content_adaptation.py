"""
Test du système d'adaptation de contenu AI Inference vs GPU Compute
"""

import asyncio
import logging
from app.composer_viral import ViralTweetComposer
from app.content_adapter import ContentAdapter

logging.basicConfig(level=logging.INFO)

async def test_content_adaptation():
    print("\n" + "="*60)
    print("🧪 TEST: CONTENT ADAPTATION (AI vs GPU)")
    print("="*60 + "\n")
    
    composer = ViralTweetComposer()
    adapter = ContentAdapter()
    
    # Test 1: Hashtags AI/LLM → Should generate AI Inference content
    print("📝 TEST 1: AI Inference Context")
    print("-" * 40)
    
    ai_hashtags = ['#AIInference', '#LLM', '#DeepLearning']
    context = adapter.detect_context(ai_hashtags)
    print(f"Hashtags: {ai_hashtags}")
    print(f"Detected context: {context}")
    
    tweet = await composer.compose_viral_tweet(ai_hashtags)
    print(f"\nGenerated tweet:\n{tweet}")
    print(f"Length: {len(tweet)} chars")
    
    # Verify it contains AI pricing
    if '$' in tweet and '/M' in tweet:
        print("✅ Contains AI model pricing (per million tokens)")
    else:
        print("⚠️ Missing AI model pricing")
    
    print("\n" + "-" * 40)
    
    # Test 2: Hashtags GPU/Cloud → Should generate GPU Compute content
    print("📝 TEST 2: GPU Compute Context")
    print("-" * 40)
    
    gpu_hashtags = ['#GPUCompute', '#CloudComputing', '#NVIDIA']
    context = adapter.detect_context(gpu_hashtags)
    print(f"Hashtags: {gpu_hashtags}")
    print(f"Detected context: {context}")
    
    tweet = await composer.compose_viral_tweet(gpu_hashtags)
    print(f"\nGenerated tweet:\n{tweet}")
    print(f"Length: {len(tweet)} chars")
    
    # Verify it contains GPU pricing
    if '$' in tweet and '/hr' in tweet:
        print("✅ Contains GPU pricing (per hour)")
    else:
        print("⚠️ Missing GPU pricing")
    
    print("\n" + "-" * 40)
    
    # Test 3: Mixed/General hashtags → Should alternate
    print("📝 TEST 3: General Context (should adapt)")
    print("-" * 40)
    
    general_hashtags = ['#Technology', '#Innovation', '#Tech']
    context = adapter.detect_context(general_hashtags)
    print(f"Hashtags: {general_hashtags}")
    print(f"Detected context: {context}")
    
    tweet = await composer.compose_viral_tweet(general_hashtags)
    print(f"\nGenerated tweet:\n{tweet}")
    print(f"Length: {len(tweet)} chars")
    
    # Check which type it generated
    if '/M' in tweet:
        print("✅ Generated AI Inference content")
    elif '/hr' in tweet:
        print("✅ Generated GPU Compute content")
    else:
        print("⚠️ Content type unclear")
    
    print("\n" + "="*60)
    
    # Test 4: Real world example with trending hashtag
    print("📝 TEST 4: Real World Example")
    print("-" * 40)
    
    real_hashtags = ['#NXTNoMercy', '#AIInference']  # Mix trending + domain
    context = adapter.detect_context(real_hashtags)
    print(f"Hashtags: {real_hashtags}")
    print(f"Detected context: {context}")
    
    tweet = await composer.compose_viral_tweet(real_hashtags)
    print(f"\nGenerated tweet:\n{tweet}")
    print(f"Length: {len(tweet)} chars")
    
    # Analyze content
    print("\n📊 Content Analysis:")
    if 'DeepSeek' in tweet or 'Hermes' in tweet or 'Qwen' in tweet:
        print("✅ Contains real AI model names")
    if 'OpenAI' in tweet or 'o1' in tweet or 'o3' in tweet or 'gpt' in tweet.lower():
        print("✅ Contains OpenAI comparison")
    if 'AWS' in tweet:
        print("✅ Contains AWS comparison")
    if 'SHA-256-C7E8976BBAF2' in tweet:
        print("✅ Contains promo code")
    if 'voltagegpu.com' in tweet or 'vtgpu.ai' in tweet:
        print("✅ Contains URL")
    
    print("\n" + "="*60)
    print("✅ CONTENT ADAPTATION TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_content_adaptation())
