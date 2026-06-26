"""
Tests for the RSS feed service.
"""
import pytest
from app.services.rss_service import fetch_rss_articles


@pytest.mark.asyncio
async def test_fetch_rss_default():
    """Test fetching RSS with default settings."""
    articles = await fetch_rss_articles(categories=["Technology"], max_articles=5)
    assert isinstance(articles, list)
    # May be empty if no network, but should not crash
    for article in articles:
        assert "title" in article
        assert "source_url" in article
        assert "source_name" in article


@pytest.mark.asyncio
async def test_fetch_rss_with_keywords():
    """Test fetching RSS with keyword filtering."""
    articles = await fetch_rss_articles(
        categories=["Technology"],
        keywords=["AI", "software"],
        max_articles=10,
    )
    assert isinstance(articles, list)


@pytest.mark.asyncio
async def test_fetch_rss_with_blocked_sources():
    """Test that blocked sources are excluded."""
    articles = await fetch_rss_articles(
        categories=["Technology"],
        blocked_sources=["techcrunch"],
        max_articles=5,
    )
    for article in articles:
        assert "techcrunch" not in article.get("source_url", "").lower()


@pytest.mark.asyncio
async def test_fetch_rss_max_articles():
    """Test the max_articles limit."""
    articles = await fetch_rss_articles(categories=["Technology"], max_articles=3)
    assert len(articles) <= 3