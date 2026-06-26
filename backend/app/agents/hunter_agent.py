"""
Hunter Agent: Discovers news articles based on user preferences.
Uses RSS feeds (primary) and can be extended with web search.
"""
import logging
from typing import Any, Dict
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.services.rss_service import fetch_rss_articles
from app.core.config import settings

logger = logging.getLogger(__name__)


async def hunter_agent(state: AgentState) -> Dict[str, Any]:
    """Discover news articles based on user preferences and interests."""
    logger.info(f"Hunter agent running for user {state.user_id}")

    categories = state.explicit_categories or ["Technology", "Finance"]
    keywords = state.keywords_topics or []
    sources = state.preferred_sources or []
    blocked = state.blocked_sources or []

    discovered = await fetch_rss_articles(
        categories=categories,
        keywords=keywords,
        preferred_sources=sources,
        blocked_sources=blocked,
        max_articles=settings.MAX_ARTICLES_TOTAL,
    )

    # Apply implicit preference scoring
    for article in discovered:
        score = 0.0
        # Boost by keyword matches
        for kw in keywords:
            if kw.lower() in (article.get("title", "") + article.get("content", "")).lower():
                score += 0.2
        # Boost by implicit preferences
        for pref_key, pref_val in state.implicit_preferences.items():
            if pref_key.lower() in (article.get("title", "") + article.get("content", "")).lower():
                score += pref_val
        article["relevance_score"] = min(round(score, 2), 1.0)
        article["discovered_at"] = datetime.now(timezone.utc).isoformat()

    # Deduplicate by source URL
    seen_urls = set()
    unique_articles = []
    for a in discovered:
        url = a.get("source_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(a)

    # Sort by relevance
    unique_articles.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)

    logger.info(f"Discovered {len(unique_articles)} unique articles")
    return {"discovered_articles": unique_articles, "current_node": "synthesizer_agent"}