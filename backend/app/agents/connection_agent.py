"""
Connector Agent: Links news to the user's personal context.
Identifies impact relevance and generates actionable alerts.
"""
import logging
from typing import Any, Dict

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def _identify_impact(article: Dict[str, Any], tracked_entities: list) -> list:
    """Identify who/what is impacted by this news."""
    content = (article.get("title", "") + " " + (article.get("content", "") or "")).lower()
    impacted = []

    industry_keywords = {
        "tech industry": ["technology", "software", "ai", "startup", "tech", "silicon valley", "app"],
        "finance industry": ["finance", "bank", "stock", "market", "investor", "trading", "wall street"],
        "healthcare industry": ["health", "medical", "hospital", "drug", "pharmaceutical", "patient"],
        "education sector": ["education", "school", "university", "student", "teacher", "college"],
        "manufacturing": ["manufacturing", "factory", "supply chain", "industrial", "production"],
        "retail": ["retail", "e-commerce", "shopping", "consumer", "store", "amazon"],
    }

    for industry, keywords in industry_keywords.items():
        if any(kw in content for kw in keywords):
            impacted.append(industry)

    # Check tracked entities
    for entity in tracked_entities:
        name = entity.get("name", "").lower()
        if name and name in content:
            impacted.append(f"{entity.get('type', 'tracked')}: {entity.get('name', '')}")

    return impacted


def _generate_alert(article: Dict[str, Any], impacts: list) -> Dict[str, Any]:
    """Generate an alert if the news is critical for the user."""
    title = article.get("title", "")
    content = (article.get("content", "") or "").lower()

    urgency_keywords = [
        "urgent", "breaking", "critical", "warning", "alert", "crisis",
        "emergency", "important", "major", "significant", "deadline",
    ]
    urgency_score = sum(1 for kw in urgency_keywords if kw in content.lower())
    is_critical = urgency_score >= 2 or any(
        kw in title.lower() for kw in ["breaking", "urgent", "critical", "alert"]
    )

    if is_critical and impacts:
        return {
            "type": "actionable",
            "title": f"⚠️ {title}",
            "message": f"This affects: {', '.join(impacts[:3])}",
            "article_id": article.get("id", ""),
            "severity": "high" if urgency_score >= 3 else "medium",
        }
    return None


async def connection_agent(state: AgentState) -> Dict[str, Any]:
    """Link articles to user context and generate alerts."""
    logger.info(f"Connection agent analyzing {len(state.synthesized_articles)} articles")

    alerts = []
    for article in state.synthesized_articles:
        impacts = _identify_impact(article, state.tracked_entities)
        article["impact_radar"] = impacts

        alert = _generate_alert(article, impacts)
        if alert:
            alerts.append(alert)

    return {
        "agent_outputs": {
            **state.agent_outputs,
            "alerts": alerts,
        },
        "current_node": "tracker_agent",
    }