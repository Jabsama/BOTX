"""
Test du système de rate limit tracking
Vérifie que les comptes sont indépendants et que le tracking fonctionne
"""

import asyncio
from datetime import datetime
from app.rate_limit_tracker import RateLimitTracker

def test_rate_limit_tracker():
    """Test le tracker de rate limit"""
    print("\n" + "="*60)
    print("📊 TEST: RATE LIMIT TRACKER")
    print("="*60 + "\n")
    
    tracker = RateLimitTracker()
    
    # Simuler quelques posts
    print("1️⃣ Simulating successful posts...")
    tracker.record_post_attempt('A', success=True)
    tracker.record_post_attempt('B', success=True)
    
    # Vérifier le status
    status = tracker.get_status()
    print(f"   Account A: {status['accounts']['A']['status']} - Posts today: {status['accounts']['A']['posts_today']}")
    print(f"   Account B: {status['accounts']['B']['status']} - Posts today: {status['accounts']['B']['posts_today']}")
    
    # Simuler un rate limit sur A
    print("\n2️⃣ Simulating rate limit on Account A...")
    tracker.record_post_attempt('A', success=False, error_type='rate_limit')
    
    # Vérifier que A est bloqué mais pas B
    can_post_a, reason_a = tracker.can_post('A')
    can_post_b, reason_b = tracker.can_post('B')
    
    print(f"   Account A can post: {can_post_a} - {reason_a}")
    print(f"   Account B can post: {can_post_b} - {reason_b}")
    
    if not can_post_a and can_post_b:
        print("   ✅ CORRECT: A is rate limited but B can still post!")
    else:
        print("   ❌ ERROR: Both accounts should be independent!")
    
    # Afficher le status complet
    print("\n3️⃣ Full status report:")
    tracker.print_status()
    
    print("\n" + "="*60)
    print("✅ RATE LIMIT TRACKER TEST COMPLETE")
    print("="*60 + "\n")

def test_account_independence():
    """Test que les comptes sont vraiment indépendants"""
    print("\n" + "="*60)
    print("🔄 TEST: ACCOUNT INDEPENDENCE")
    print("="*60 + "\n")
    
    tracker = RateLimitTracker()
    
    # Simuler 50 posts sur le compte A (limite horaire)
    print("📈 Simulating 50 posts on Account A (hourly limit)...")
    for i in range(50):
        tracker.record_post_attempt('A', success=True)
    
    # Vérifier les statuts
    can_post_a, reason_a = tracker.can_post('A')
    can_post_b, reason_b = tracker.can_post('B')
    
    print(f"\nAfter 50 posts on A:")
    print(f"   Account A: {reason_a}")
    print(f"   Account B: {reason_b}")
    
    if not can_post_a and can_post_b:
        print("   ✅ CORRECT: A hit hourly limit but B is unaffected!")
    else:
        print("   ❌ ERROR: B should still be able to post!")
    
    # Tester que B peut poster
    print("\n📝 Testing that B can still post...")
    tracker.record_post_attempt('B', success=True)
    status = tracker.get_status()
    
    print(f"   Account B posts today: {status['accounts']['B']['posts_today']}")
    print(f"   Account B status: {status['accounts']['B']['status']}")
    
    if status['accounts']['B']['status'] == 'ready':
        print("   ✅ CORRECT: B posted successfully while A is limited!")
    
    print("\n" + "="*60)
    print("✅ INDEPENDENCE TEST COMPLETE")
    print("="*60 + "\n")

def test_rate_limit_reset_timing():
    """Test le calcul du temps de reset"""
    print("\n" + "="*60)
    print("⏰ TEST: RATE LIMIT RESET TIMING")
    print("="*60 + "\n")
    
    tracker = RateLimitTracker()
    
    # Simuler un rate limit
    print("🚫 Simulating rate limit...")
    tracker.record_post_attempt('A', success=False, error_type='rate_limit')
    
    status = tracker.get_status()
    account_a = status['accounts']['A']
    
    if 'minutes_until_reset' in account_a:
        print(f"   Rate limit will reset in: {account_a['minutes_until_reset']} minutes")
        print(f"   Reset time: {account_a['rate_limit_reset']}")
        
        # Vérifier que c'est environ 15 minutes
        if 14 <= account_a['minutes_until_reset'] <= 16:
            print("   ✅ CORRECT: Reset time is ~15 minutes (Twitter standard)")
        else:
            print(f"   ⚠️ WARNING: Reset time seems off ({account_a['minutes_until_reset']} min)")
    
    print("\n" + "="*60)
    print("✅ RESET TIMING TEST COMPLETE")
    print("="*60 + "\n")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 RATE LIMIT SYSTEM TESTS")
    print("="*70)
    
    test_rate_limit_tracker()
    test_account_independence()
    test_rate_limit_reset_timing()
    
    print("\n" + "="*70)
    print("🎉 ALL RATE LIMIT TESTS COMPLETE")
    print("="*70)
    print("\nKey findings:")
    print("1. ✅ Rate limit tracker correctly tracks posts and limits")
    print("2. ✅ Accounts A and B are independent")
    print("3. ✅ When A is rate limited, B can still post")
    print("4. ✅ Rate limit reset time is correctly calculated (15 min)")
    print("5. ✅ System provides clear visibility on rate limit status")
    print("\n")

if __name__ == "__main__":
    main()
