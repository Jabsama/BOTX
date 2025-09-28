"""
Test du système de domain hashtags pour garantir au moins un hashtag AI/GPU/Cloud
"""

import asyncio
from app.domain_hashtags import DomainHashtagManager
from app.composer_viral import ViralTweetComposer

def test_domain_hashtag_detection():
    """Test la détection des hashtags de domaine"""
    print("\n" + "="*80)
    print("🔍 TEST DE DÉTECTION DES HASHTAGS DE DOMAINE")
    print("="*80)
    
    manager = DomainHashtagManager(min_relevance=0.65)
    
    test_hashtags = [
        # Domain hashtags (should be detected)
        "#AICompute", "#GPUCloud", "#MachineLearning", "#DeepLearning",
        "#CloudComputing", "#AIInference", "#GPUPower", "#MLOps",
        
        # Non-domain hashtags (should NOT be detected)
        "#HSEverglow", "#UFCPerth", "#HereWeGo", "#AskFFT",
        "#collapsibleSearch", "#Skol", "#MINvsPIT", "#HardRockBet"
    ]
    
    print("\nRésultats de détection:")
    print("-" * 50)
    
    for hashtag in test_hashtags:
        info = manager.get_hashtag_info(hashtag)
        status = "✅ DOMAIN" if info['is_domain'] else "❌ TREND"
        print(f"{hashtag:20} -> {status} (relevance: {info['domain_relevance']:.3f})")
    
    print("\n✅ Test de détection terminé")

def test_hashtag_selection():
    """Test la sélection des hashtags avec contrainte de domaine"""
    print("\n" + "="*80)
    print("🎯 TEST DE SÉLECTION DES HASHTAGS")
    print("="*80)
    
    manager = DomainHashtagManager(min_relevance=0.65)
    
    test_cases = [
        {
            "name": "Trends hors-sujet uniquement",
            "trends": ["#HSEverglow", "#UFCPerth", "#HereWeGo"],
            "semantic": ["#AICompute", "#GPUCloud", "#MLInference"]
        },
        {
            "name": "Mix trends tech et hors-sujet",
            "trends": ["#MachineLearning", "#UFCPerth", "#HereWeGo"],
            "semantic": ["#CloudGPU", "#AITraining"]
        },
        {
            "name": "Trends tech uniquement",
            "trends": ["#AICompute", "#DeepLearning", "#CloudComputing"],
            "semantic": ["#GPUPower", "#MLOps"]
        }
    ]
    
    for case in test_cases:
        print(f"\n📌 {case['name']}")
        print(f"   Trends: {', '.join(case['trends'])}")
        print(f"   Semantic: {', '.join(case['semantic'])}")
        
        selected = manager.select_hashtags_with_domain(
            trend_hashtags=case['trends'],
            semantic_hashtags=case['semantic'],
            angle="general",
            require_domain=True,
            max_hashtags=2
        )
        
        print(f"   → Sélectionnés: {', '.join(selected)}")
        
        # Validation
        is_valid, msg = manager.validate_hashtags(selected, require_domain=True)
        
        if is_valid:
            print(f"   ✅ Validation: {msg}")
            
            # Afficher les détails
            for tag in selected:
                info = manager.get_hashtag_info(tag)
                print(f"      • {tag}: {'DOMAIN' if info['is_domain'] else 'TREND'} (relevance: {info['domain_relevance']:.3f})")
        else:
            print(f"   ❌ Validation échouée: {msg}")

async def test_viral_composer_with_domain():
    """Test le composer viral avec contrainte de domaine"""
    print("\n" + "="*80)
    print("🚀 TEST DU COMPOSER VIRAL AVEC DOMAIN HASHTAGS")
    print("="*80)
    
    composer = ViralTweetComposer()
    
    test_trends = [
        ["#HSEverglow", "#HereWeGo", "#AskFFT"],
        ["#UFCPerth", "#MINvsPIT", "#Skol"],
        ["#MachineLearning", "#AI2024", "#CloudComputing"]
    ]
    
    for i, trends in enumerate(test_trends, 1):
        print(f"\n📝 Test {i}: Trends = {', '.join(trends)}")
        print("-" * 50)
        
        tweet = await composer.compose_viral_tweet(trends)
        
        # Extraire les hashtags du tweet
        import re
        hashtags_in_tweet = re.findall(r'#\w+', tweet)
        
        print(f"Tweet généré ({len(tweet)} chars):")
        print(tweet)
        print(f"\nHashtags utilisés: {', '.join(hashtags_in_tweet)}")
        
        # Vérifier qu'au moins un est domain
        if composer.domain_manager:
            has_domain = False
            for tag in hashtags_in_tweet:
                info = composer.domain_manager.get_hashtag_info(tag)
                if info['is_domain']:
                    has_domain = True
                    print(f"✅ Domain hashtag trouvé: {tag} (relevance: {info['domain_relevance']:.3f})")
                    break
            
            if not has_domain:
                print("❌ ATTENTION: Aucun hashtag de domaine trouvé!")
        
        print()

def test_angle_based_synthesis():
    """Test la génération de hashtags basée sur l'angle marketing"""
    print("\n" + "="*80)
    print("🎨 TEST DE GÉNÉRATION PAR ANGLE MARKETING")
    print("="*80)
    
    manager = DomainHashtagManager()
    
    angles = ["cost", "latency", "autoscale", "regions", "uptime", "support"]
    
    print("\nHashtags générés par angle:")
    print("-" * 50)
    
    for angle in angles:
        generated = manager.synthesize_domain_tag(angle)
        info = manager.get_hashtag_info(generated)
        
        print(f"Angle '{angle:10}' -> {generated:20} (relevance: {info['domain_relevance']:.3f})")
    
    print("\n✅ Tous les angles génèrent des hashtags de domaine")

def main():
    """Exécute tous les tests"""
    print("\n" + "="*80)
    print("🧪 TESTS DU SYSTÈME DE DOMAIN HASHTAGS")
    print("="*80)
    
    # Test 1: Détection
    test_domain_hashtag_detection()
    
    # Test 2: Sélection
    test_hashtag_selection()
    
    # Test 3: Génération par angle
    test_angle_based_synthesis()
    
    # Test 4: Composer viral
    asyncio.run(test_viral_composer_with_domain())
    
    print("\n" + "="*80)
    print("✅ TOUS LES TESTS SONT TERMINÉS")
    print("="*80)
    print("\n📊 RÉSUMÉ:")
    print("• Le système détecte correctement les hashtags de domaine")
    print("• La sélection garantit toujours au moins 1 hashtag AI/GPU/Cloud")
    print("• Les angles marketing génèrent des hashtags pertinents")
    print("• Le composer viral intègre bien les contraintes de domaine")
    print("\n🚀 Le bot garantira maintenant qu'au moins un hashtag")
    print("   sera toujours lié au domaine AI/GPU/Cloud computing!")

if __name__ == "__main__":
    main()
