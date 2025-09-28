"""
Système de GIFs trending pour tweets
Récupère les GIFs les plus populaires du moment de façon dynamique
"""

import asyncio
import aiohttp
import logging
import json
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class TrendingGifManager:
    """Gestionnaire de GIFs trending pour les tweets"""
    
    def __init__(self, giphy_api_key: Optional[str] = None, tenor_api_key: Optional[str] = None):
        """
        Initialize with API keys for Giphy and/or Tenor
        """
        self.giphy_api_key = giphy_api_key or os.getenv('GIPHY_API_KEY')
        self.tenor_api_key = tenor_api_key or os.getenv('TENOR_API_KEY')
        self.cache_file = Path("data/trending_gifs.json")
        self.cache_duration = timedelta(hours=3)  # Refresh toutes les 3 heures
        
    async def get_trending_gif(self, hashtags: List[str] = None) -> Optional[Dict]:
        """
        Récupère un GIF trending basé sur les hashtags actuels
        Retourne: {url: str, preview: str, tags: List[str]}
        """
        
        # Check cache first
        cached = self._load_cache()
        if cached and cached.get('gifs'):
            # Si on a des hashtags, essayer de matcher
            if hashtags:
                matched_gif = self._match_gif_to_hashtags(cached['gifs'], hashtags)
                if matched_gif:
                    logger.info(f"Using cached GIF matching hashtags: {matched_gif.get('tags', [])}")
                    return matched_gif
            
            # Sinon prendre un GIF random du cache
            gif = random.choice(cached['gifs'])
            logger.info(f"Using random cached trending GIF: {gif.get('tags', [])}")
            return gif
        
        # Fetch new trending GIFs
        gifs = []
        
        # Try Giphy first (meilleure qualité)
        if self.giphy_api_key:
            giphy_gifs = await self._fetch_giphy_trending(hashtags)
            gifs.extend(giphy_gifs)
        
        # Try Tenor as fallback
        if not gifs and self.tenor_api_key:
            tenor_gifs = await self._fetch_tenor_trending(hashtags)
            gifs.extend(tenor_gifs)
        
        # If still no GIFs, try without API keys (limited)
        if not gifs:
            gifs = await self._fetch_public_trending()
        
        if gifs:
            # Save to cache
            self._save_cache(gifs)
            
            # Return best matching or random
            if hashtags:
                matched_gif = self._match_gif_to_hashtags(gifs, hashtags)
                if matched_gif:
                    return matched_gif
            
            return random.choice(gifs)
        
        logger.warning("No trending GIFs found")
        return None
    
    async def _fetch_giphy_trending(self, hashtags: List[str] = None) -> List[Dict]:
        """Récupère les GIFs trending depuis Giphy"""
        gifs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Si on a des hashtags, chercher des GIFs liés
                if hashtags and len(hashtags) > 0:
                    # Recherche basée sur le hashtag principal
                    search_term = hashtags[0].replace('#', '')
                    url = f"https://api.giphy.com/v1/gifs/search"
                    params = {
                        'api_key': self.giphy_api_key,
                        'q': search_term,
                        'limit': 25,
                        'rating': 'pg-13',
                        'lang': 'en'
                    }
                else:
                    # Sinon prendre les trending généraux
                    url = f"https://api.giphy.com/v1/gifs/trending"
                    params = {
                        'api_key': self.giphy_api_key,
                        'limit': 50,
                        'rating': 'pg-13'
                    }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for gif_data in data.get('data', [])[:30]:
                            # Extraire les URLs
                            images = gif_data.get('images', {})
                            
                            # Préférer la version optimisée pour Twitter
                            gif_url = (
                                images.get('fixed_height', {}).get('url') or
                                images.get('original', {}).get('url')
                            )
                            
                            preview_url = (
                                images.get('preview_gif', {}).get('url') or
                                images.get('fixed_height_small', {}).get('url')
                            )
                            
                            if gif_url:
                                # Extraire les tags
                                title = gif_data.get('title', '').lower()
                                tags = title.split() + [gif_data.get('slug', '')]
                                
                                gifs.append({
                                    'url': gif_url,
                                    'preview': preview_url or gif_url,
                                    'tags': tags,
                                    'source': 'giphy',
                                    'id': gif_data.get('id')
                                })
                        
                        logger.info(f"Fetched {len(gifs)} GIFs from Giphy")
                        
        except Exception as e:
            logger.warning(f"Failed to fetch Giphy GIFs: {e}")
        
        return gifs
    
    async def _fetch_tenor_trending(self, hashtags: List[str] = None) -> List[Dict]:
        """Récupère les GIFs trending depuis Tenor"""
        gifs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                if hashtags and len(hashtags) > 0:
                    # Recherche basée sur hashtag
                    search_term = hashtags[0].replace('#', '')
                    url = f"https://tenor.googleapis.com/v2/search"
                    params = {
                        'key': self.tenor_api_key,
                        'q': search_term,
                        'limit': 20,
                        'contentfilter': 'medium',
                        'media_filter': 'gif'
                    }
                else:
                    # Trending général
                    url = f"https://tenor.googleapis.com/v2/featured"
                    params = {
                        'key': self.tenor_api_key,
                        'limit': 50,
                        'contentfilter': 'medium'
                    }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for result in data.get('results', [])[:30]:
                            media = result.get('media_formats', {})
                            
                            # Obtenir le GIF
                            gif_url = (
                                media.get('gif', {}).get('url') or
                                media.get('mediumgif', {}).get('url')
                            )
                            
                            preview_url = (
                                media.get('tinygif', {}).get('url') or
                                media.get('nanogif', {}).get('url')
                            )
                            
                            if gif_url:
                                # Tags depuis le contenu
                                tags = result.get('tags', []) + [result.get('content_description', '')]
                                
                                gifs.append({
                                    'url': gif_url,
                                    'preview': preview_url or gif_url,
                                    'tags': tags,
                                    'source': 'tenor',
                                    'id': result.get('id')
                                })
                        
                        logger.info(f"Fetched {len(gifs)} GIFs from Tenor")
                        
        except Exception as e:
            logger.warning(f"Failed to fetch Tenor GIFs: {e}")
        
        return gifs
    
    async def _fetch_public_trending(self) -> List[Dict]:
        """Récupère des GIFs trending sans API key (limité)"""
        gifs = []
        
        # Liste de GIFs populaires génériques (fallback)
        generic_trending = [
            {
                'url': 'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
                'preview': 'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/200w.gif',
                'tags': ['working', 'computer', 'typing'],
                'source': 'generic'
            },
            {
                'url': 'https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif',
                'preview': 'https://media.giphy.com/media/LmNwrBhejkK9EFP504/200w.gif',
                'tags': ['meme', 'sweating', 'nervous'],
                'source': 'generic'
            },
            {
                'url': 'https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif',
                'preview': 'https://media.giphy.com/media/26ufdipQqU2lhNA4g/200w.gif',
                'tags': ['mind', 'blown', 'amazing'],
                'source': 'generic'
            },
            {
                'url': 'https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif',
                'preview': 'https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/200w.gif',
                'tags': ['wow', 'surprised', 'reaction'],
                'source': 'generic'
            }
        ]
        
        # Essayer de scraper des GIFs trending publics
        try:
            async with aiohttp.ClientSession() as session:
                # Giphy trending page (public)
                url = "https://giphy.com/trending-gifs"
                headers = {'User-Agent': 'Mozilla/5.0'}
                
                async with session.get(url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        # Le scraping est limité, utiliser les génériques
                        pass
        except:
            pass
        
        # Retourner les génériques
        return generic_trending
    
    def _match_gif_to_hashtags(self, gifs: List[Dict], hashtags: List[str]) -> Optional[Dict]:
        """Trouve le GIF qui correspond le mieux aux hashtags"""
        if not hashtags or not gifs:
            return None
        
        # Nettoyer les hashtags
        clean_tags = [tag.replace('#', '').lower() for tag in hashtags]
        
        best_match = None
        best_score = 0
        
        for gif in gifs:
            score = 0
            gif_tags = [str(tag).lower() for tag in gif.get('tags', [])]
            
            # Calculer le score de correspondance
            for tag in clean_tags:
                for gif_tag in gif_tags:
                    if tag in gif_tag or gif_tag in tag:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = gif
        
        # Si on a trouvé une correspondance
        if best_score > 0:
            return best_match
        
        # Sinon retourner None pour utiliser un random
        return None
    
    def _load_cache(self) -> Optional[Dict]:
        """Charge le cache de GIFs"""
        try:
            if not self.cache_file.exists():
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier l'âge du cache
            cache_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return data
                
        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
        
        return None
    
    def _save_cache(self, gifs: List[Dict]):
        """Sauvegarde les GIFs en cache"""
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gifs': gifs[:50]  # Garder max 50 GIFs
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")


async def test_trending_gifs():
    """Test du système de GIFs trending"""
    print("\n" + "="*60)
    print("🎬 TEST: TRENDING GIFS SYSTEM")
    print("="*60 + "\n")
    
    manager = TrendingGifManager()
    
    # Test 1: GIF trending général
    print("📡 Fetching general trending GIF...")
    gif = await manager.get_trending_gif()
    
    if gif:
        print(f"✅ Found trending GIF:")
        print(f"   URL: {gif['url']}")
        print(f"   Tags: {gif.get('tags', [])[:5]}")
        print(f"   Source: {gif.get('source')}")
    else:
        print("❌ No GIF found")
    
    print()
    
    # Test 2: GIF basé sur hashtags
    hashtags = ['#WorldCup', '#Football']
    print(f"📡 Fetching GIF for hashtags: {hashtags}")
    gif = await manager.get_trending_gif(hashtags)
    
    if gif:
        print(f"✅ Found matching GIF:")
        print(f"   URL: {gif['url']}")
        print(f"   Tags: {gif.get('tags', [])[:5]}")
        print(f"   Source: {gif.get('source')}")
    else:
        print("❌ No matching GIF found")
    
    print("\n" + "="*60)
    print("✅ GIF SYSTEM TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(test_trending_gifs())
