import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, Integer
from sqlalchemy.dialects.sqlite import TEXT as SQLITE_TEXT
from app.db.session import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, index=True, nullable=False)
    categories = Column(JSON, default=list)       # e.g., ["Finance", "Technology"]
    keywords = Column(JSON, default=list)          # e.g., ["AI regulation", "Apple stock"]
    preferred_sources = Column(JSON, default=list) # e.g., ["https://techcrunch.com"]
    blocked_sources = Column(JSON, default=list)
    tracked_entities = Column(JSON, default=list)  # e.g., [{"type": "stock", "name": "AAPL"}]
    implicit_preferences = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, index=True, nullable=False)
    source_url = Column(String, nullable=False)
    source_name = Column(String)
    title = Column(String, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    tl_dr = Column(String)
    key_takeaways = Column(JSON)
    author = Column(String)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    categories = Column(JSON, default=list)
    bias_rating = Column(String)  # "liberal", "conservative", "neutral", "unknown"
    estimated_read_time_minutes = Column(Integer)
    is_read = Column(Boolean, default=False)
    relevance_score = Column(Float, default=0.0)
    impact_radar = Column(JSON, default=list)


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, index=True, nullable=False)
    article_id = Column(String, nullable=False)
    feedback_type = Column(String, nullable=False)  # "show_more", "show_less", "irrelevant"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Digest(Base):
    __tablename__ = "digests"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, index=True, nullable=False)
    digest_type = Column(String, nullable=False)   # "morning_briefing", "on_demand"
    title = Column(String)
    content = Column(Text)
    article_ids = Column(JSON, default=list)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, index=True, nullable=False)
    article_id = Column(String, nullable=False)
    read_time_seconds = Column(Integer, default=0)
    clicked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SourceBias(Base):
    """Configurable source bias ratings stored in the database."""
    __tablename__ = "source_biases"

    id = Column(String, primary_key=True, default=_uuid)
    domain = Column(String, unique=True, index=True, nullable=False)
    bias_rating = Column(String, nullable=False)   # "liberal", "conservative", "neutral", "unknown"
    confidence = Column(Float, default=0.7)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
