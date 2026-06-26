"""
Feedback Processor Agent: Processes user feedback to update implicit preferences.
Learns from "show more", "show less", and "irrelevant" signals.
Persists updated preferences to the database.
"""
import logging
from typing import Any, Dict

from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.db.crud import upsert_preferences

logger = logging.getLogger(__name__)


async def feedback_processor_agent(state: AgentState) -> Dict[str, Any]:
    """Process user feedback and update implicit preference scores."""
    logger.info(f"Feedback processor processing {len(state.user_feedback)} feedback entries")

    feedback = state.user_feedback
    prefs = dict(state.implicit_preferences)

    for fb in feedback:
        feedback_type = fb.get("feedback_type", "")
        topics = fb.get("topics", [])

        for topic in topics:
            topic_lower = topic.lower()
            if feedback_type == "show_more":
                prefs[topic_lower] = prefs.get(topic_lower, 0) + 0.1
            elif feedback_type == "show_less":
                prefs[topic_lower] = max(prefs.get(topic_lower, 0) - 0.1, 0)
            elif feedback_type == "irrelevant":
                prefs[topic_lower] = max(prefs.get(topic_lower, 0) - 0.3, 0)

            # Clamp to [0, 1]
            prefs[topic_lower] = round(min(prefs[topic_lower], 1.0), 2)

    # Persist updated preferences to the database
    db = None
    try:
        db = SessionLocal()
        upsert_preferences(db, state.user_id, {"implicit_preferences": prefs})
        logger.info(f"Persisted {len(prefs)} implicit preferences for user {state.user_id}")
    except Exception as e:
        logger.error(f"Failed to persist implicit preferences: {e}")
    finally:
        if db:
            db.close()

    logger.info(f"Updated {len(prefs)} implicit preference dimensions")
    return {
        "implicit_preferences": prefs,
        "current_node": "output_formatter_agent",
    }