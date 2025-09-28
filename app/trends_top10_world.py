"""
REAL TOP 10 WORLD TRENDING HASHTAGS
Récupère les VRAIS hashtags du TOP 10 mondial en temps réel
"""

import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import tweepy

logger = logging.getLogger(__name__)


class Top10WorldTrends:
    """Récupère le VRAI TOP 10 des hashtags mondiaux"""
    
    def __init__(self, twitter_bearer_token: Optional[str] = None):
        self.bearer_token = twitter_bearer_token
        self.cache_file = Path("data/top10_world.json")
        self.cache_duration = timedelta(hours=6)  # Refresh toutes les 6 heures
        
    async def get_real_top10_world(self) -> List[str]:
        """
        Récupère le VRAI TOP 10 mondial des hashtags
        Priorité:
        1. Twitter API officielle (Trends/place)
        2. Scraping de sites de trends fiables
        3. Agrégation multi-sources
        """
        
        # Check cache (6 heures)
        cached = self._load_cache()
        if cached:
            logger.info(f"Using cached TOP 10: {', '.join(cached[:5])}")
            return cached
        
        top10 = []
        
        # 1. Essayer Twitter API officielle
        if self.bearer_token:
            top10 = await self._get_twitter_official_trends()
        
        # 2. Si pas assez, scraper les sites de trends
        if len(top10) < 10:
            scraped = await self._scrape_trend_sites()
            top10.extend(scraped)
        
        # 3. Nettoyer et prendre le TOP 10
        top10 = self._clean_and_rank(top10)[:10]
        
        # Sauvegarder en cache
        if top10:
            self._save_cache(top10)
            logger.info(f"✅ REAL TOP 10 WORLD: {', '.join(top10)}")
        
        return top10
    
    async def _get_twitter_official_trends(self) -> List[str]:
        """Utilise l'API Twitter officielle pour les trends mondiales"""
        if not self.bearer_token:
            return []
        
        try:
            # Client Twitter v2
            client = tweepy.Client(bearer_token=self.bearer_token)
            
            # WOEID 1 = Worldwide
            # Note: Twitter v2 n'a pas encore l'endpoint trends, on doit utiliser v1.1
            auth = tweepy.OAuth2BearerHandler(self.bearer_token)
            api = tweepy.API(auth)
            
            # Récupérer les trends mondiales
            trends = api.get_place_trends(1)  # 1 = Worldwide WOEID
            
            hashtags = []
            if trends and len(trends) > 0:
                for trend in trends[0]['trends'][:20]:  # Top 20
                    name = trend['name']
                    if name.startswith('#'):
                        hashtags.append(name)
                    
            logger.info(f"Twitter API: Found {len(hashtags)} official trends")
            return hashtags
            
        except Exception as e:
            logger.warning(f"Twitter API trends failed: {e}")
            return []
    
    async def _scrape_trend_sites(self) -> List[str]:
        """Scrape les sites de trends fiables pour le TOP 10 mondial"""
        all_trends = []
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Sites fiables pour les trends mondiales
            sources = [
                {
                    'url': 'https://trends24.in/',
                    'pattern': r'<a[^>]*href="/[^"]*"[^>]*>([#][^<]+)</a>'
                },
                {
                    'url': 'https://getdaytrends.com/',
                    'pattern': r'<td class="main"[^>]*>.*?([#]\w+).*?</td>'
                },
                {
                    'url': 'https://trendogate.com/',
                    'pattern': r'class="trend-name"[^>]*>([#][^<]+)</span>'
                },
                {
                    'url': 'https://www.trendsmap.com/twitter/trends/1',  # 1 = Worldwide
                    'pattern': r'<a[^>]*class="[^"]*trend[^"]*"[^>]*>([#][^<]+)</a>'
                }
            ]
            
            for source in sources:
                try:
                    async with session.get(source['url'], headers=headers, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Extraire les hashtags
                            matches = re.findall(source['pattern'], html, re.IGNORECASE | re.DOTALL)
                            
                            for match in matches[:20]:  # Top 20 par source
                                hashtag = match.strip()
                                if hashtag.startswith('#') and len(hashtag) > 2:
                                    all_trends.append(hashtag)
                            
                            logger.info(f"Scraped {len(matches)} trends from {source['url']}")
                            
                except Exception as e:
                    logger.debug(f"Failed to scrape {source['url']}: {e}")
                    continue
            
            # Essayer aussi l'API non officielle de Twitter trends
            try:
                # API alternative pour trends Twitter
                trend_api_url = "https://api.twitter.com/1.1/trends/place.json?id=1"
                
                # Utiliser un proxy API public si disponible
                proxy_urls = [
                    "https://twitter-trends.iamrohit.in/api.php?woeid=1",
                    "https://trends.24o.it/get.php?location=worldwide"
                ]
                
                for proxy_url in proxy_urls:
                    try:
                        async with session.get(proxy_url, headers=headers, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Parser selon le format
                                if isinstance(data, list):
                                    for item in data[:20]:
                                        if isinstance(item, dict) and 'name' in item:
                                            name = item['name']
                                            if name.startswith('#'):
                                                all_trends.append(name)
                                elif isinstance(data, dict) and 'trends' in data:
                                    for trend in data['trends'][:20]:
                                        if 'name' in trend and trend['name'].startswith('#'):
                                            all_trends.append(trend['name'])
                                            
                    except:
                        continue
                        
            except:
                pass
        
        return all_trends
    
    def _clean_and_rank(self, hashtags: List[str]) -> List[str]:
        """Nettoie et classe les hashtags par fréquence"""
        from collections import Counter
        
        # Nettoyer
        cleaned = []
        for tag in hashtags:
            # Enlever les espaces et caractères spéciaux
            tag = tag.strip()
            
            # Vérifier que c'est un vrai hashtag
            if not tag.startswith('#'):
                continue
            
            # Enlever les hashtags non-ASCII
            try:
                tag.encode('ascii')
            except:
                continue
            
            # Filtrer le bruit
            if self._is_noise(tag):
                continue
            
            cleaned.append(tag)
        
        # Compter les occurrences (plus fréquent = plus trending)
        counter = Counter(cleaned)
        
        # Retourner par ordre de fréquence
        return [tag for tag, count in counter.most_common()]
    
    def _is_noise(self, hashtag: str) -> bool:
        """Filtre le bruit et les faux hashtags"""
        tag_lower = hashtag.lower()
        
        # Filtrer les hex colors
        if re.match(r'^#[0-9a-f]{3,8}$', tag_lower):
            return True
        
        # Filtrer les pure numbers
        if re.match(r'^#\d+$', hashtag):
            return True
        
        # Filtrer les mots trop courts
        if len(hashtag) < 3:
            return True
        
        # Filtrer les patterns de spam connus
        spam_patterns = [
            'collapsible', 'θ', 'ち', '05508', 
            'test', 'debug', 'lorem', 'ipsum'
        ]
        
        for pattern in spam_patterns:
            if pattern in tag_lower:
                return True
        
        return False
    
    def _load_cache(self) -> Optional[List[str]]:
        """Charge le cache s'il est valide (< 6 heures)"""
        try:
            if not self.cache_file.exists():
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier l'âge du cache
            cache_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return data['trends']
                
        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
        
        return None
    
    def _save_cache(self, trends: List[str]):
        """Sauvegarde les trends en cache"""
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'trends': trends,
                'source': 'top10_world'
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")


async def test_top10():
    """Test du système TOP 10 mondial"""
    print("\n" + "="*60)
    print("🌍 REAL TOP 10 WORLD TRENDING HASHTAGS")
    print("="*60 + "\n")
    
    # Charger le bearer token depuis l'environnement
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    extractor = Top10WorldTrends(bearer_token)
    
    print("📡 Fetching REAL TOP 10 WORLD trends...")
    print("⏰ Cache: 6 hours\n")
    
    trends = await extractor.get_real_top10_world()
    
    if trends:
        print(f"✅ Found {len(trends)} REAL trending hashtags:\n")
        for i, trend in enumerate(trends, 1):
            print(f"  {i:2}. {trend}")
        
        print(f"\n📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔄 Will refresh in 6 hours")
    else:
        print("❌ No trends found - check your connection")
    
    print("\n" + "="*60)
    print("✅ These are REAL WORLD TRENDS, not generated!")
    print("="*60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(test_top10())
