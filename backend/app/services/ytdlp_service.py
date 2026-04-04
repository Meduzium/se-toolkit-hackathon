"""
yt-dlp service for YouTube search and MP3 extraction
"""

import subprocess
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)

class YtDlpService:
    def __init__(self):
        self.download_dir = Path(settings.audio_download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        '''Search YouTube for videos matching query'''
        try:
            cmd = [
                "yt-dlp",
                "-j",
                "--no-warnings",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                f"ytsearch{limit}:{query}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp search error: {result.stderr}")
                return []
            
            # Parse JSON lines output
            results = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        results.append({
                            "title": data.get("title", "Unknown"),
                            "artist": data.get("uploader", "Unknown"),
                            "youtube_url": data.get("webpage_url", ""),
                            "id": data.get("id", ""),
                            "duration": data.get("duration", 0),
                        })
                    except json.JSONDecodeError:
                        continue
            
            return results[:limit]
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def download(self, youtube_url: str, title: str) -> Optional[str]:
        '''Download audio from YouTube URL and return file path'''
        try:
            filename = f"{title.replace(' ', '_')}.mp3"
            filepath = self.download_dir / filename
            
            cmd = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                "-o", str(filepath.with_suffix("")),
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and filepath.exists():
                return str(filepath)
            else:
                logger.error(f"Download error: {result.stderr}")
                return None
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

ytdlp_service = YtDlpService()
