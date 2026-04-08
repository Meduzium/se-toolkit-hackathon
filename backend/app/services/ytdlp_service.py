import subprocess
import json
import logging
import os
import re
from typing import List, Dict, Optional
from pathlib import Path
import yt_dlp
from ..config import settings

logger = logging.getLogger(__name__)

class YtDlpService:
    def __init__(self):
        self.download_dir = Path(settings.audio_download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.cookies_file = (settings.ytdlp_cookies_file or "").strip()
        self.last_error: Optional[str] = None

    @staticmethod
    def _map_download_error(stderr: str) -> str:
        err = (stderr or "").lower()
        if "cookies are no longer valid" in err:
            return "YouTube cookies are expired/rotated. Re-export cookies.txt from your logged-in browser and restart backend."
        if "sign in to confirm you\u2019re not a bot" in err or "sign in to confirm you're not a bot" in err:
            return "YouTube requires authenticated cookies for this video. Update cookies.txt and try again."
        if "http error 429" in err or "too many requests" in err:
            return "YouTube rate-limited requests (429). Wait a bit or rotate IP/cookies and retry."
        return "Download failed"

    @staticmethod
    def _normalize_track_metadata(title: str, uploader: str) -> tuple[str, str]:
        clean_title = (title or "Unknown").strip()
        clean_artist = (uploader or "Unknown").strip()

        # Remove uploader/channel prefix when titles look like "Channel - Artist - Track".
        if clean_artist and clean_artist.lower() != "unknown":
            uploader_prefix = f"{clean_artist} - "
            if clean_title.lower().startswith(uploader_prefix.lower()):
                clean_title = clean_title[len(uploader_prefix):].strip()

        # Parse common music title forms: "Artist - Track" or "Artist – Track".
        split_match = re.split(r"\s[-–]\s", clean_title, maxsplit=1)
        if len(split_match) == 2:
            possible_artist, possible_title = split_match[0].strip(), split_match[1].strip()
            if possible_artist and possible_title:
                clean_artist = possible_artist
                clean_title = possible_title

        return clean_title or "Unknown", clean_artist or "Unknown"
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        '''Search YouTube for videos matching query'''
        try:
            cmd = [
                "yt-dlp",
                "-j",
                "--no-warnings",
                "--flat-playlist",
                "--skip-download",
                f"ytsearch{limit}:{query}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp search error: {result.stderr}")
                return []
            
            # Parse JSON lines output
            results = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        title, artist = self._normalize_track_metadata(
                            title=data.get("title", "Unknown"),
                            uploader=data.get("uploader", "Unknown"),
                        )
                        results.append({
                            "title": title,
                            "artist": artist,
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
        '''Download audio from YouTube URL via subprocess with explicit environment'''
        try:
            self.last_error = None
            # Sanitize filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_title:
                safe_title = "track"
            safe_title = safe_title[:50]  # Limit length
            filename = f"{safe_title}.m4a"  # m4a instead of mp3 - no transcoding needed
            filepath = self.download_dir / filename
            
            # Build command with explicit flags
            cmd = [
                "yt-dlp",
                "--verbose",
                

                "--js-runtimes", "node",
                "--ffmpeg-location", "/usr/bin/",
                "--force-ipv4",
                "--socket-timeout", "60",
                
                "-f", "ba[ext=m4a]/ba",
                "-x",
                "--audio-format", "m4a",
                
                "--extractor-retries", "10",
                "--fragment-retries", "10",
                "--retries", "10",
                
                "-o", f"{filepath.with_suffix('')}.%(ext)s",
                
                youtube_url
            ]

            if self.cookies_file:
                cookies_path = Path(self.cookies_file)
                if cookies_path.exists():
                    cmd = cmd[:-1] + ["--cookies", str(cookies_path), youtube_url]
                    logger.info(f"Using yt-dlp cookies file: {cookies_path}")
                else:
                    logger.warning(
                        f"Configured YTDLP_COOKIES_FILE not found: {cookies_path}. "
                        "Downloads may fail with LOGIN_REQUIRED."
                    )
            
            # Prepare environment with explicit PATH
            env = os.environ.copy()
            env['PATH'] = '/usr/local/bin:/usr/bin:/bin'
            
            logger.info(f"Starting download: {youtube_url}")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Run with explicit environment
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            # Log output
            if result.stdout:
                logger.info(f"yt-dlp stdout (last 500 chars): {result.stdout[-500:]}")
            if result.stderr:
                logger.warning(f"yt-dlp stderr (last 500 chars): {result.stderr}")
            
            if result.returncode == 0 and filepath.exists():
                logger.info(f"Download successful: {filepath}")
                return str(filepath)
            else:
                self.last_error = self._map_download_error(result.stderr)
                logger.error(f"Download failed with return code {result.returncode}")
                return None
        
        except subprocess.TimeoutExpired:
            logger.error(f"Download timeout for {youtube_url}")
            self.last_error = "Download timed out. Try a shorter track or retry later."
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            self.last_error = "Internal download error"
            return None

ytdlp_service = YtDlpService()
