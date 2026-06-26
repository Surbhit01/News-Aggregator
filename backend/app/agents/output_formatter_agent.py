"""
Output Formatter Agent: Selects articles for the digest and formats the final output.
"""
import logging
from typing import Any, Dict

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


async def output_formatter_agent(state: AgentState) -> Dict[str, Any]:
    """Select top articles for digest and prepare formatted output."""
    logger.info("Output formatter preparing digest")

    articles = state.synthesized_articles
    if not articles:
        return {
            "selected_articles_for_digest": [],
            "agent_outputs": {**state.agent_outputs, "digest_summary": "No articles available."},
            "current_node": "delivery_agent",
        }

    # Select top 10 most relevant articles
    articles.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)
    selected = articles[:10]

    # Build digest content
    digest_sections = []
    for i, article in enumerate(selected, 1):
        digest_sections.append(
            f"{i}. {article.get('title', 'Untitled')}\n"
            f"   {article.get('tl_dr', '')}\n"
            f"   [{article.get('source_name', 'Unknown')}] "
            f"| {article.get('estimated_read_time_minutes', '?')} min read"
            f"| Bias: {article.get('bias_rating', 'unknown')}\n"
        )

    digest_content = "\n".join(digest_sections)

    return {
        "selected_articles_for_digest": selected,
        "agent_outputs": {
            **state.agent_outputs,
            "digest_content": digest_content,
        },
        "current_node": "delivery_agent",
    }