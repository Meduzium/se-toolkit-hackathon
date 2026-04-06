"""
Pydantic schemas for request/response validation
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TrackBase(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None

class Track(TrackBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None
    youtube_url: Optional[str] = None

class ChartEntry(BaseModel):
    username: Optional[str]
    title: str
    artist: str
    count: int

class ChartsResponse(BaseModel):
    period: str
    entries: List[ChartEntry]
