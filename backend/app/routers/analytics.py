"""
Analytics and charts endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/charts")
async def get_charts(period: str = "day", db: Session = Depends(get_db)):
    '''Get top tracks for specified period'''
    if period not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Calculate date threshold
    now = datetime.utcnow()
    if period == "day":
        since = now - timedelta(days=1)
    elif period == "week":
        since = now - timedelta(weeks=1)
    else:
        since = now - timedelta(days=30)
    
    # Query: top tracks with user attribution
    results = db.query(
        models.User.username,
        models.Track.title,
        models.Track.artist,
        func.count(models.Search.id).label("count")
    ).join(models.Search).join(models.Track).filter(
        models.Search.searched_at >= since
    ).group_by(
        models.User.id,
        models.Track.id
    ).order_by(desc("count")).limit(50).all()
    
    entries = [
        schemas.ChartEntry(
            username=r[0] or "Anonymous",
            title=r[1],
            artist=r[2],
            count=r[3]
        )
        for r in results
    ]
    
    return schemas.ChartsResponse(period=period, entries=entries)
