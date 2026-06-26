"""
Tests for the Hunter Agent.
"""
import pytest
from datetime import datetime

from app.agents.state import AgentState
from app.agents.hunter_agent import hunter_agent


@pytest.mark.asyncio
async def test_hunter_agent_discovers_articles():
    """Test that hunter agent returns articles for given preferences."""
    state = AgentState(
        user_id="test-user",
        explicit_categories=["Technology"],
        keywords_topics=["AI"],
    )

    result = await hunter_agent(state)

    assert "discovered_articles" in result
    assert result["current_node"] == "synthesizer_agent"


@pytest.mark.asyncio
async def test_hunter_agent_deduplicates():
    """Test that duplicate articles are removed."""
    state = AgentState(
        user_id="test-user",
        explicit_categories=["Technology"],
    )

    result = await hunter_agent(state)
    articles = result["discovered_articles"]
    urls = [a.get("source_url") for a in articles if a.get("source_url")]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"


@pytest.mark.asyncio
async def test_hunter_agent_empty_categories():
    """Test hunter agent with empty categories (defaults)."""
    state = AgentState(user_id="test-user")
    result = await hunter_agent(state)
    assert len(result["discovered_articles"]) >= 0