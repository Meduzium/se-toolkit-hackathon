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
async def download(title: str, youtube_url: str):
    '''Download audio file from YouTube'''
    file_path = ytdlp_service.download(youtube_url, title)
    if not file_path:
        raise HTTPException(status_code=500, detail="Download failed")
    return {"file_path": file_path, "status": "ok"}

@router.post("/log-search")
async def log_search(user_id: int, track_id: int, db: Session = Depends(get_db)):
    '''Log a search to the database'''
    search = models.Search(user_id=user_id, track_id=track_id)
    db.add(search)
    db.commit()
    return {"status": "logged"}
