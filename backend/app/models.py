"""
SQLAlchemy ORM Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    searches = relationship("Search", back_populates="user")


class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), nullable=False)
    album_art_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    searches = relationship("Search", back_populates="track")
    __table_args__ = (Index("idx_tracks_title_artist", "title", "artist"),)


class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="searches")
    track = relationship("Track", back_populates="searches")
    __table_args__ = (Index("idx_searches_user_track_time", "user_id", "track_id", "searched_at"),)
