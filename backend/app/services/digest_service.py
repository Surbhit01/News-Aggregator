"""
Digest service: handles morning briefing generation and on-demand digest creation.
Orchestrates the agent pipeline for digest generation.
"""
import asyncio
import logging
from typing import Optional, Set
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.agents.graph import news_graph
from app.db.session import SessionLocal
from app.db.crud import create_digest, get_preferences
from app.services.cache import get_cached_digest, set_cached_digest

logger = logging.getLogger(__name__)

# Track in-progress generation tasks to avoid duplicates
_generation_tasks: Set[str] = set()


async def _run_agent_pipeline(user_id: str, query: Optional[str] = None) -> AgentState:
    """Run the full LangGraph agent pipeline and return final state."""
    db = SessionLocal()
    try:
        prefs = get_preferences(db, user_id)
        print(f"User {user_id} preferences: {prefs}")
        initial_state = AgentState(
            user_id=user_id,
            explicit_categories=prefs.categories if prefs else ["Technology", "Finance"],
            keywords_topics=prefs.keywords if prefs else [],
            preferred_sources=prefs.preferred_sources if prefs else [],
            blocked_sources=prefs.blocked_sources if prefs else [],
            tracked_entities=prefs.tracked_entities if prefs else [],
            implicit_preferences=prefs.implicit_preferences if prefs else {},
            current_query=query,
        )
    finally:
        db.close()

    final_state = await news_graph.ainvoke(initial_state)
    return final_state


async def _generate_and_cache(user_id: str, digest_type: str, topic: Optional[str] = None) -> Optional[str]:
    """Generate digest, cache it, and persist to DB. Returns content or None on failure."""
    task_key = f"{user_id}:{digest_type}:{topic or ''}"
    if task_key in _generation_tasks:
        logger.info(f"Generation already in progress for {task_key}")
        return None
    _generation_tasks.add(task_key)

    try:
        if digest_type == "on_demand" and topic:
            final_state = await _run_agent_pipeline(user_id, query=topic)
        else:
            final_state = await _run_agent_pipeline(user_id)

        content = final_state.agent_outputs.get("digest_content", "")

        if content and "No articles" not in content and "No digest" not in content:
            # Cache it
            await set_cached_digest(user_id, content, digest_type)

            # Persist to DB
            db = SessionLocal()
            try:
                create_digest(
                    db=db,
                    user_id=user_id,
                    digest_type=digest_type,
                    title=f"Morning Briefing - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
                          if digest_type == "morning_briefing" else f"On Demand: {topic}",
                    content=content,
                    article_ids=[],  # Articles saved by delivery_agent
                )
                logger.info(f"Digest saved for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to persist digest: {e}")
            finally:
                db.close()

            return content
        else:
            logger.warning(f"Digest generation produced no content for {task_key}")
            return None
    except Exception as e:
        logger.error(f"Digest generation failed for {task_key}: {e}", exc_info=True)
        return None
    finally:
        _generation_tasks.discard(task_key)


def trigger_digest_generation(user_id: str, digest_type: str = "morning_briefing", topic: Optional[str] = None):
    """Fire-and-forget digest generation in the background."""
    async def _safe_wrapper():
        try:
            await _generate_and_cache(user_id, digest_type, topic)
        except Exception as e:
            logger.error(f"Unhandled error in digest generation for {user_id}: {e}", exc_info=True)

    asyncio.create_task(_safe_wrapper())
    logger.info(f"Triggered {digest_type} digest generation for user {user_id}")


async def get_or_generate_digest(user_id: str, digest_type: str = "morning_briefing", topic: Optional[str] = None) -> Optional[str]:
    """Get cached digest, or trigger generation and return None."""
    # Check cache first
    cached = await get_cached_digest(user_id, digest_type)
    if cached:
        logger.info(f"Returning cached {digest_type} digest for user {user_id}")
        return cached

    # Check DB
    from app.db.crud import get_digests_for_user
    db = SessionLocal()
    try:
        digests = get_digests_for_user(db, user_id, limit=1)
        if digests:
            content = digests[0].content
            # Re-cache it
            await set_cached_digest(user_id, content, digest_type)
            return content
    finally:
        db.close()

    # Trigger generation
    trigger_digest_generation(user_id, digest_type, topic)
    return None