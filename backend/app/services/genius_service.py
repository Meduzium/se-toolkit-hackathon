"""
Genius API service for fetching album art
"""

import requests
import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

class GeniusService:
    def __init__(self):
        self.api_key = settings.genius_api_key
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def get_album_art(self, title: str, artist: str) -> Optional[str]:
        '''Fetch album art URL from Genius'''
        if not self.api_key:
            return None
        
        try:
            query = f"{title} {artist}"
            params = {"q": query}
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["response"]["hits"]:
                    hit = data["response"]["hits"][0]
                    song = hit["result"]
                    return song.get("song_art_image_url") or song.get("primary_artist", {}).get("image_url")
        
        except Exception as e:
            logger.error(f"Genius API error: {e}")
        
        return None

genius_service = GeniusService()
