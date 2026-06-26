"""
Reading history routes: track which articles users click/read.
Triggers implicit preference learning from reading behavior.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.crud import log_reading, get_reading_history, get_article
from app.api.deps import get_current_user
from app.db.models import User
from app.services.preference_service import learn_from_reading
from pydantic import BaseModel
from datetime import datetime, timezone


class ReadingLogRequest(BaseModel):
    article_id: str
    read_time_seconds: int = 0


class ReadingHistoryEntry(BaseModel):
    id: str
    article_id: str
    read_time_seconds: int
    clicked_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/log")
async def log_article_read(
    data: ReadingLogRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log an article read event and update implicit preferences."""
    # Log the read
    entry = log_reading(db, user.id, data.article_id, data.read_time_seconds)

    # Trigger implicit learning from this read
    article = get_article(db, data.article_id)
    if article:
        topics = (article.categories or []) + ([article.title] if article.title else [])
        learn_from_reading(
            db=db,
            user_id=user.id,
            article_topics=topics,
            read_time_seconds=data.read_time_seconds,
        )

    return {"id": entry.id, "article_id": entry.article_id, "status": "logged"}


@router.get("", response_model=List[ReadingHistoryEntry])
async def get_user_history(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's reading history."""
    entries = get_reading_history(db, user.id, limit=limit)
    return entries