from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class ArticleSummary(BaseModel):
    id: str
    title: str
    source_name: Optional[str] = None
    source_url: str
    tl_dr: Optional[str] = None
    key_takeaways: Optional[List[str]] = None
    bias_rating: Optional[str] = None
    estimated_read_time_minutes: Optional[int] = None
    published_at: Optional[datetime] = None
    categories: List[str]
    relevance_score: float = 0.0
    is_read: bool = False
    impact_radar: List[str] = []


class DigestResponse(BaseModel):
    id: str
    digest_type: str
    title: Optional[str] = None
    content: str
    articles: List[ArticleSummary]
    generated_at: datetime
    delivered_at: Optional[datetime] = None


class DigestRequest(BaseModel):
    type: str = "daily"  # "daily" | "on_demand"
    topic: Optional[str] = None


class TLDRResponse(BaseModel):
    article_id: str
    title: str
    tl_dr: str
    key_takeaways: List[str]


class ReadingTimeFilter(BaseModel):
    max_minutes: int = 5