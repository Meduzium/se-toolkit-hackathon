"""
Music search and download endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..services.ytdlp_service import ytdlp_service
from ..services.genius_service import genius_service

router = APIRouter(prefix="/api", tags=["music"])

@router.get("/search")
async def search(q: str, db: Session = Depends(get_db)):
    '''Search for tracks on YouTube'''
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    results = ytdlp_service.search(q, limit=10)
    return {"results": results}

@router.post("/download")
async def download(
    title: str, 
    youtube_url: str,
    telegram_id: int = None,
    username: str = None,
    artist: str = "Unknown",
    db: Session = Depends(get_db)
):
    '''Download audio file from YouTube and track in database'''
    file_path = ytdlp_service.download(youtube_url, title)
    if not file_path:
        raise HTTPException(status_code=500, detail="Download failed")
    
    # Track download in database if user info provided
    if telegram_id:
        # Get or create user
        user = db.query(models.User).filter(
            models.User.telegram_id == telegram_id
        ).first()
        
        if not user:
            user = models.User(
                telegram_id=telegram_id,
                username=username
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Get or create track
        track = db.query(models.Track).filter(
            models.Track.title == title,
            models.Track.artist == artist
        ).first()
        
        if not track:
            track = models.Track(
                title=title,
                artist=artist
            )
            db.add(track)
            db.commit()
            db.refresh(track)
        
        # Log the search/download
        search = models.Search(
            user_id=user.id,
            track_id=track.id
        )
        db.add(search)
        db.commit()
    
    return {"file_path": file_path, "status": "ok"}

@router.post("/log-search")
async def log_search(user_id: int, track_id: int, db: Session = Depends(get_db)):
    '''Log a search to the database'''
    search = models.Search(user_id=user_id, track_id=track_id)
    db.add(search)
    db.commit()
    return {"status": "logged"}


@router.get("/lyrics", response_model=schemas.LyricsResponse)
async def get_lyrics(title: str, artist: str = "Unknown"):
    '''Fetch lyrics via Genius service'''
    if not title or len(title.strip()) < 2:
        raise HTTPException(status_code=400, detail="Title too short")

    lyrics = genius_service.get_lyrics(title=title.strip(), artist=artist.strip() or "Unknown")
    return schemas.LyricsResponse(
        title=title,
        artist=artist,
        lyrics=lyrics,
        found=bool(lyrics),
    )


@router.get("/cover", response_model=schemas.CoverResponse)
async def get_cover(title: str, artist: str = "Unknown"):
    '''Fetch track/album cover via Genius service'''
    if not title or len(title.strip()) < 2:
        raise HTTPException(status_code=400, detail="Title too short")

    cover_url = genius_service.get_album_art(title=title.strip(), artist=artist.strip() or "Unknown")
    return schemas.CoverResponse(
        title=title,
        artist=artist,
        cover_url=cover_url,
        found=bool(cover_url),
    )
