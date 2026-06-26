from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
from app.db.crud import get_preferences, upsert_preferences
from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.preferences import UserPreferenceUpdate, UserPreferenceResponse, PreferenceStats

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferenceResponse)
async def get_user_preferences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user preferences. Returns defaults if none set."""
    prefs = get_preferences(db, user.id)
    if not prefs:
        # Return default empty preferences instead of 404
        from app.db.crud import upsert_preferences
        prefs = upsert_preferences(db, user.id, {})
    return prefs


@router.put("", response_model=UserPreferenceResponse)
async def update_user_preferences(
    data: UserPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update user preferences."""
    update_data = data.model_dump(exclude_none=True)
    # tracked_entities is already serialized by Pydantic v2's model_dump
    prefs = upsert_preferences(db, user.id, update_data)
    return prefs


@router.get("/stats", response_model=PreferenceStats)
async def get_preference_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get preference statistics for the dashboard."""
    prefs = get_preferences(db, user.id)
    if not prefs:
        return PreferenceStats(
            total_categories=0, total_keywords=0,
            total_preferred_sources=0, total_blocked_sources=0,
            total_tracked_entities=0,
        )
    return PreferenceStats(
        total_categories=len(prefs.categories or []),
        total_keywords=len(prefs.keywords or []),
        total_preferred_sources=len(prefs.preferred_sources or []),
        total_blocked_sources=len(prefs.blocked_sources or []),
        total_tracked_entities=len(prefs.tracked_entities or []),
    )