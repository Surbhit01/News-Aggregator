"""
Preference service: business logic for managing user preferences.
Handles implicit preference learning from reading history and feedback.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db.crud import get_preferences, upsert_preferences, get_reading_history

logger = logging.getLogger(__name__)

PREFERENCE_DECAY_FACTOR = 0.95  # How quickly old preferences fade


def learn_from_reading(
    db: Session,
    user_id: str,
    article_topics: List[str],
    read_time_seconds: int,
) -> Dict[str, float]:
    """Update implicit preferences based on reading behavior."""
    prefs = get_preferences(db, user_id)
    if not prefs:
        return {}

    implicit = dict(prefs.implicit_preferences or {})

    # Boost topics from the article
    for topic in article_topics:
        topic_lower = topic.lower()
        boost = min(read_time_seconds / 120.0, 0.3)  # Max 0.3 boost per article
        implicit[topic_lower] = min(implicit.get(topic_lower, 0) + boost, 1.0)

    # Apply decay to all preferences
    for key in implicit:
        implicit[key] = round(implicit[key] * PREFERENCE_DECAY_FACTOR, 2)

    # Remove stale preferences
    implicit = {k: v for k, v in implicit.items() if v > 0.05}

    upsert_preferences(db, user_id, {"implicit_preferences": implicit})
    logger.info(f"Learned {len(article_topics)} preference signals for user {user_id}")

    return implicit


def get_preference_profile(db: Session, user_id: str) -> Dict[str, Any]:
    """Build a comprehensive preference profile for the user."""
    prefs = get_preferences(db, user_id)
    if not prefs:
        return {
            "categories": [],
            "keywords": [],
            "preferred_sources": [],
            "blocked_sources": [],
            "tracked_entities": [],
            "implicit_preferences": {},
            "reading_trend": [],
        }

    # Analyze reading trend (last 7 days)
    history = get_reading_history(db, user_id, limit=100)
    recent = [h for h in history if h.clicked_at > datetime.now(timezone.utc) - timedelta(days=7)]

    return {
        "categories": prefs.categories or [],
        "keywords": prefs.keywords or [],
        "preferred_sources": prefs.preferred_sources or [],
        "blocked_sources": prefs.blocked_sources or [],
        "tracked_entities": prefs.tracked_entities or [],
        "implicit_preferences": prefs.implicit_preferences or {},
        "total_reads_recent": len(recent),
    }