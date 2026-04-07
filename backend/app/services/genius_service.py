"""
Genius API service for fetching track metadata and lyrics.
"""

import logging
import re
from html import unescape
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import quote_plus

import requests
from ..config import settings

logger = logging.getLogger(__name__)

class GeniusService:
    def __init__(self):
        self.api_key = settings.genius_api_key
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    @staticmethod
    def _normalize_title_artist(title: str, artist: str) -> tuple[str, str]:
        clean_title = (title or "").strip()
        clean_artist = (artist or "Unknown").strip()

        # Common YouTube style title: "Artist - Track".
        if " - " in clean_title:
            left, right = [p.strip() for p in clean_title.split(" - ", 1)]
            if clean_artist.lower() != "unknown":
                if left.lower() == clean_artist.lower() and right:
                    clean_title = right
                elif right.lower() == clean_artist.lower() and left:
                    clean_title = left
            elif left and right:
                clean_artist, clean_title = left, right

        # Remove duplicated artist prefix if it remains in title.
        artist_prefix = f"{clean_artist} - "
        if clean_artist.lower() != "unknown" and clean_title.lower().startswith(artist_prefix.lower()):
            clean_title = clean_title[len(artist_prefix):].strip()

        return clean_title, clean_artist

    def _search_song(self, title: str, artist: str) -> Optional[dict]:
        title, artist = self._normalize_title_artist(title, artist)
        queries = self._build_queries(title, artist)

        # 1) Try official Genius API (requires valid token).
        if self.api_key:
            for query in queries:
                params = {"q": query}
                response = requests.get(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    params=params,
                    timeout=8,
                )

                if response.status_code == 401:
                    logger.warning("Genius API returned 401 Unauthorized, falling back to web search API")
                    break

                if response.status_code != 200:
                    continue

                song = self._pick_best_song(response.json().get("response", {}).get("hits", []), title, artist)
                if song:
                    return song

        # 2) Fallback to Genius web API endpoint that does not require OAuth token.
        for query in queries:
            web_api_url = f"https://genius.com/api/search/multi?q={quote_plus(query)}"
            web_response = requests.get(web_api_url, timeout=8)
            if web_response.status_code != 200:
                continue

            sections = web_response.json().get("response", {}).get("sections", [])
            hits = []
            for section in sections:
                if section.get("type") == "song":
                    hits = section.get("hits", [])
                    break

            song = self._pick_best_song(hits, title, artist)
            if song:
                return song

        return None

    @staticmethod
    def _title_variants(title: str) -> list[str]:
        variants = [title.strip()]

        # Split mixed letter-digit forms like "Ка50" -> "Ка 50" / "Ка-50".
        spaced = re.sub(r"(?<=\D)(\d)", r" \1", title).strip()
        dashed = re.sub(r"(?<=\D)(\d)", r"-\1", title).strip()
        if spaced:
            variants.append(spaced)
        if dashed:
            variants.append(dashed)

        # Also try variant without punctuation.
        compact = re.sub(r"[\-_:]+", " ", title).strip()
        if compact:
            variants.append(compact)

        seen = set()
        unique_variants = []
        for item in variants:
            normalized = re.sub(r"\s+", " ", item).strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_variants.append(item)
        return unique_variants

    def _build_queries(self, title: str, artist: str) -> list[str]:
        queries = []
        title_variants = self._title_variants(title)
        is_unknown_artist = artist.lower() == "unknown"

        for tv in title_variants:
            if not is_unknown_artist:
                queries.append(f"{artist} {tv}".strip())
                queries.append(f"{tv} {artist}".strip())
            queries.append(tv)

        # De-duplicate while preserving order.
        seen = set()
        unique_queries = []
        for query in queries:
            key = query.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique_queries.append(query)
        return unique_queries

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        return re.sub(r"[\W_]+", "", (value or "").lower(), flags=re.UNICODE)

    @staticmethod
    def _pick_best_song(hits: list, title: str, artist: str) -> Optional[dict]:
        if not hits:
            return None

        normalized_title = title.lower().strip()
        normalized_artist = artist.lower().strip()
        normalized_title_compact = GeniusService._normalize_for_match(title)

        best_song = None
        best_score = -1

        for hit in hits:
            song = hit.get("result", {})
            song_title = song.get("title", "").lower()
            primary_artist = song.get("primary_artist", {}).get("name", "").lower()

            score = 0
            if normalized_title and normalized_title == song_title:
                score += 100
            if normalized_title and normalized_title in song_title:
                score += 60

            song_title_compact = GeniusService._normalize_for_match(song_title)
            if normalized_title_compact and normalized_title_compact == song_title_compact:
                score += 100
            elif normalized_title_compact and normalized_title_compact in song_title_compact:
                score += 70

            if normalized_artist != "unknown":
                if normalized_artist == primary_artist:
                    score += 50
                elif normalized_artist in primary_artist:
                    score += 25

            if score > best_score:
                best_score = score
                best_song = song

        if best_song:
            return best_song

        return hits[0].get("result")

    @staticmethod
    def _clean_lyrics_text(raw_html: str) -> Optional[str]:
        if not raw_html:
            return None

        class LyricsParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_lyrics = False
                self.lyrics_depth = 0
                self.current_parts = []
                self.containers = []

            def handle_starttag(self, tag, attrs):
                attrs_map = dict(attrs)
                if tag == "div" and attrs_map.get("data-lyrics-container") == "true":
                    self.in_lyrics = True
                    self.lyrics_depth = 1
                    self.current_parts = []
                    return

                if self.in_lyrics:
                    if tag == "div":
                        self.lyrics_depth += 1
                    if tag == "br":
                        self.current_parts.append("\n")

            def handle_endtag(self, tag):
                if not self.in_lyrics:
                    return

                if tag == "div":
                    self.lyrics_depth -= 1
                    if self.lyrics_depth == 0:
                        self.in_lyrics = False
                        block = "".join(self.current_parts).strip()
                        if block:
                            self.containers.append(block)
                        self.current_parts = []

            def handle_data(self, data):
                if self.in_lyrics and data:
                    self.current_parts.append(data)

        parser = LyricsParser()
        parser.feed(raw_html)
        containers = parser.containers
        if not containers:
            return None

        parts = []
        for block in containers:
            text = unescape(block)

            # Remove common metadata artifacts that can appear above lyrics.
            text = re.sub(r"^\s*\d+\s+Contributors.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
            text = re.sub(r"Translations?[A-Za-zА-Яа-яЁё]+", "", text)

            # Put section tags on their own lines for readability.
            text = re.sub(r"\s*(\[[^\]]+\])\s*", r"\n\1\n", text)
            text = re.sub(r"\n\s+", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]{2,}", " ", text)
            cleaned = text.strip()
            if cleaned:
                parts.append(cleaned)

        if not parts:
            return None

        merged = "\n\n".join(parts).strip()

        # Deduplicate accidental repeated blocks that can appear in rendered HTML.
        lines = [ln.rstrip() for ln in merged.splitlines()]
        deduped_lines = []
        previous = None
        for ln in lines:
            if ln == previous and ln:
                continue
            deduped_lines.append(ln)
            previous = ln

        return "\n".join(deduped_lines).strip()
    
    def get_album_art(self, title: str, artist: str) -> Optional[str]:
        '''Fetch album art URL from Genius'''
        try:
            song = self._search_song(title, artist)
            if song:
                return song.get("song_art_image_url") or song.get("primary_artist", {}).get("image_url")
        
        except Exception as e:
            logger.error(f"Genius API error: {e}")
        
        return None

    def get_lyrics(self, title: str, artist: str) -> Optional[str]:
        '''Fetch lyrics text by using Genius search API and parsing the song page.'''
        try:
            song = self._search_song(title, artist)
            if not song:
                return None

            song_url = song.get("url")
            if not song_url:
                return None

            page = requests.get(song_url, timeout=10)
            if page.status_code != 200:
                return None

            return self._clean_lyrics_text(page.text)
        except Exception as e:
            logger.error(f"Genius lyrics fetch error: {e}")
            return None

genius_service = GeniusService()
