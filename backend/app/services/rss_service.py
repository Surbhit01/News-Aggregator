"""
RSS feed service: fetches and parses articles from RSS sources.
Primary discovery mechanism for MVP (web search deferred to Phase 3).
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import feedparser
import re

from app.core.config import settings

RSS_FETCH_TIMEOUT = 10.0  # seconds per feed

logger = logging.getLogger(__name__)

# Category → RSS feed URL mapping
CATEGORY_FEEDS: Dict[str, List[str]] = {
    "Technology": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.wired.com/feed/rss",
    ],
    "Finance": [
        "https://feeds.content.dowjones.io/public/rss/mw_top_stories",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.bloomberg.com/markets/news.rss",
    ],
    "Geopolitics": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.reuters.com/world/rss",
    ],
    "Science": [
        "https://www.nature.com/nature.rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "https://www.sciencedaily.com/rss/all.xml",
    ],
    "Health": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/rss-feeds/news-english.xml",
        "https://feeds.bbci.co.uk/news/health/rss.xml",
    ],
    "Sports": [
        "https://www.espn.com/espn/rss/news",
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
}

# General catch-all feeds
GENERAL_FEEDS = [
    "https://news.google.com/rss",
    "https://www.reddit.com/r/news/.rss",
]


def _extract_content(entry: feedparser.FeedParserDict) -> str:
    """Extract the best available content from a feed entry."""
    if hasattr(entry, "content") and entry.content:
        html = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        html = entry.summary or ""
    else:
        html = ""
    # Strip HTML tags
    return re.sub(r"<[^>]+>", "", html)


async def fetch_rss_articles(
    categories: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    preferred_sources: Optional[List[str]] = None,
    blocked_sources: Optional[List[str]] = None,
    max_articles: int = 50,
) -> List[Dict[str, Any]]:
    """Fetch articles from RSS feeds based on categories and preferences."""
    feeds_to_fetch = []

    # Gather feed URLs
    if categories:
        for cat in categories:
            feeds_to_fetch.extend(CATEGORY_FEEDS.get(cat, []))
    else:
        # Default: fetch all categories
        for cat_feeds in CATEGORY_FEEDS.values():
            feeds_to_fetch.extend(cat_feeds)

    # Add preferred sources (treat as direct RSS URLs)
    if preferred_sources:
        feeds_to_fetch.extend(preferred_sources)

    # Add general feeds as fallback
    feeds_to_fetch.extend(GENERAL_FEEDS)

    # Deduplicate
    feeds_to_fetch = list(set(feeds_to_fetch))

    # Filter out blocked sources
    if blocked_sources:
        feeds_to_fetch = [
            f for f in feeds_to_fetch
            if not any(blocked.lower() in f.lower() for blocked in blocked_sources)
        ]

    articles = []
    for feed_url in feeds_to_fetch[:20]:  # Limit to 20 feeds per run
        try:
            # Fetch with timeout via asyncio.to_thread
            feed = await asyncio.wait_for(
                asyncio.to_thread(feedparser.parse, feed_url),
                timeout=RSS_FETCH_TIMEOUT,
            )
            if feed.bozo and not feed.entries:
                logger.warning(f"Failed to parse feed: {feed_url}")
                continue

            source_name = feed.feed.get("title", feed_url.split("/")[2])

            for entry in feed.entries[:20]:  # Max 20 per feed
                title = entry.get("title", "")
                content = _extract_content(entry)
                link = entry.get("link", "")

                # Keyword filter (if keywords provided)
                if keywords:
                    combined = (title + " " + content).lower()
                    if not any(kw.lower() in combined for kw in keywords):
                        continue

                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])

                articles.append({
                    "title": title,
                    "content": content[:5000],  # Truncate long content
                    "summary": entry.get("summary", "")[:1000],
                    "source_url": link,
                    "source_name": source_name,
                    "author": entry.get("author", ""),
                    "published_at": published.isoformat() if published else None,
                    "categories": categories or [],
                })
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            continue

    # Sort by published date (newest first)
    articles.sort(
        key=lambda a: a.get("published_at") or "",
        reverse=True,
    )

    return articles[:max_articles]