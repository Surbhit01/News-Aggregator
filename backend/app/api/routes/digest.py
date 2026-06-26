from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.crud import get_article, get_digests_for_user
from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.digest import DigestResponse, ArticleSummary
from app.services.cache import get_cached_digest
from app.services.digest_service import trigger_digest_generation

router = APIRouter(prefix="/api/digest", tags=["digest"])


def _build_article_summaries(db: Session, article_ids: List[str]) -> List[ArticleSummary]:
    articles = []
    for aid in (article_ids or []):
        article = get_article(db, aid)
        if article:
            articles.append(ArticleSummary(
                id=article.id,
                title=article.title,
                source_name=article.source_name,
                source_url=article.source_url,
                tl_dr=article.tl_dr,
                key_takeaways=article.key_takeaways,
                bias_rating=article.bias_rating,
                estimated_read_time_minutes=article.estimated_read_time_minutes,
                published_at=article.published_at,
                categories=article.categories or [],
                relevance_score=article.relevance_score or 0.0,
                is_read=article.is_read,
                impact_radar=article.impact_radar or [],
            ))
    return articles


@router.get("")
async def get_digest(
    type: str = Query("daily", description="daily | on_demand"),
    topic: Optional[str] = Query(None, description="Topic for on-demand digest"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch curated news digest.

    - `type=daily`: Returns the most recent morning briefing from cache or DB.
      If none exists, triggers background generation and returns 202 Accepted.
    - `type=on_demand`: Triggers background generation and returns 202 Accepted.
    """
    if type == "on_demand":
        if not topic:
            raise HTTPException(status_code=422, detail="topic is required for on_demand digest")
        trigger_digest_generation(user.id, "on_demand", topic)
        raise HTTPException(
            status_code=202,
            detail=f"Generating on-demand digest for '{topic}'. Check back in a few seconds.",
        )

    # Daily: check cache first, then DB
    cached = await get_cached_digest(user.id)
    if cached:
        return _cached_response(user, cached)

    digests = get_digests_for_user(db, user.id, limit=1)
    if digests:
        content = digests[0].content
        articles = _build_article_summaries(db, digests[0].article_ids or [])
        return DigestResponse(
            id=digests[0].id,
            digest_type=digests[0].digest_type,
            title=digests[0].title,
            content=content,
            articles=articles,
            generated_at=digests[0].generated_at,
            delivered_at=digests[0].delivered_at,
        )

    # No digest exists — trigger generation
    trigger_digest_generation(user.id)
    raise HTTPException(
        status_code=202,
        detail="Generating your morning briefing. Check back in a few seconds.",
    )


def _cached_response(user: User, content: str) -> DigestResponse:
    """Build a proper DigestResponse from cached content."""
    return DigestResponse(
        id="cached",
        digest_type="morning_briefing",
        title="Morning Briefing",
        content=content,
        articles=[],
        generated_at=datetime.now(timezone.utc),
        delivered_at=None,
    )


@router.get("/articles", response_model=List[ArticleSummary])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    max_minutes: Optional[int] = Query(None, ge=1, description="Filter by max reading time"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get articles for the current user, sorted by relevance."""
    from app.db.crud import get_articles_by_user

    articles = get_articles_by_user(db, user.id, skip=skip, limit=limit * 2)

    result = []
    for a in articles:
        if max_minutes and (a.estimated_read_time_minutes or 99) > max_minutes:
            continue
        result.append(ArticleSummary(
            id=a.id,
            title=a.title,
            source_name=a.source_name,
            source_url=a.source_url,
            tl_dr=a.tl_dr,
            key_takeaways=a.key_takeaways,
            bias_rating=a.bias_rating,
            estimated_read_time_minutes=a.estimated_read_time_minutes,
            published_at=a.published_at,
            categories=a.categories or [],
            relevance_score=a.relevance_score or 0.0,
            is_read=a.is_read,
            impact_radar=a.impact_radar or [],
        ))
        if len(result) >= limit:
            break

    return result


@router.get("/articles/{article_id}/tldr")
async def get_article_tldr(
    article_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get TL;DR and key takeaways for a specific article."""
    article = get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {
        "article_id": article.id,
        "title": article.title,
        "tl_dr": article.tl_dr,
        "key_takeaways": article.key_takeaways or [],
        "bias_rating": article.bias_rating,
        "estimated_read_time_minutes": article.estimated_read_time_minutes,
        "source_name": article.source_name,
    }