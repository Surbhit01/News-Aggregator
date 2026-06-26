"""
Tracker Agent: Monitors user-defined tracked entities (stocks, industries, cities).
Prioritizes articles relevant to tracked interests.
"""
import logging
from typing import Any, Dict

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


async def tracker_agent(state: AgentState) -> Dict[str, Any]:
    """Filter and prioritize articles based on tracked entities."""
    logger.info(f"Tracker agent running for user {state.user_id}")

    tracked = state.tracked_entities
    if not tracked:
        return {"current_node": "feedback_processor_agent"}

    # Boost scores for articles matching tracked entities
    for article in state.synthesized_articles:
        content = (article.get("title", "") + " " + (article.get("content", "") or "")).lower()
        for entity in tracked:
            name = entity.get("name", "").lower()
            if name and name in content:
                article["relevance_score"] = min(
                    (article.get("relevance_score", 0) or 0) + 0.3, 1.0
                )
                article["tracked_match"] = True

    # Re-sort by updated relevance
    state.synthesized_articles.sort(
        key=lambda a: a.get("relevance_score", 0), reverse=True
    )

    return {"current_node": "feedback_processor_agent"}