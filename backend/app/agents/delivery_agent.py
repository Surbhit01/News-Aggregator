"""
Delivery Agent: Persists the digest and articles to the database.
Handles the final output of the agent pipeline.
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from langgraph.graph import END

from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.db.crud import save_article, create_digest

logger = logging.getLogger(__name__)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse a datetime from string or return as-is if already datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(value[:19], fmt[:19])
            except ValueError:
                continue
    return None


async def delivery_agent(state: AgentState) -> Dict[str, Any]:
    """Persist processed articles and digest to the database."""
    logger.info(f"Delivery agent persisting {len(state.selected_articles_for_digest)} articles")

    db = SessionLocal()
    try:
        article_ids = []
        for article in state.selected_articles_for_digest:
            db_article = save_article(db, {
                "user_id": state.user_id,
                "source_url": article.get("source_url", ""),
                "source_name": article.get("source_name", ""),
                "title": article.get("title", "Untitled"),
                "content": article.get("content", ""),
                "summary": article.get("summary", ""),
                "tl_dr": article.get("tl_dr", ""),
                "key_takeaways": article.get("key_takeaways", []),
                "author": article.get("author", ""),
                "published_at": _parse_datetime(article.get("published_at")),
                "categories": article.get("categories", []),
                "bias_rating": article.get("bias_rating", "unknown"),
                "estimated_read_time_minutes": article.get("estimated_read_time_minutes", 1),
                "relevance_score": article.get("relevance_score", 0.0),
                "impact_radar": article.get("impact_radar", []),
            })
            article_ids.append(db_article.id)

        # Create digest entry
        digest_content = state.agent_outputs.get("digest_content", "")
        if digest_content and article_ids:
            create_digest(
                db=db,
                user_id=state.user_id,
                digest_type="morning_briefing",
                title=f"Morning Briefing - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                content=digest_content,
                article_ids=article_ids,
            )

        logger.info(f"Saved {len(article_ids)} articles and digest")
    finally:
        db.close()

    return {"current_node": END}