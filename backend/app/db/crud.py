"""
CRUD operations for database models.
Provides reusable query functions used by services and API routes.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

from app.db.models import (
    User, UserPreference, Article, UserFeedback, Digest, ReadingHistory,
)


# ── User ──────────────────────────────────────────────────────────────────────

def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── User Preferences ──────────────────────────────────────────────────────────

def get_preferences(db: Session, user_id: str) -> Optional[UserPreference]:
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


def upsert_preferences(db: Session, user_id: str, data: Dict[str, Any]) -> UserPreference:
    prefs = get_preferences(db, user_id)
    if prefs:
        for key, value in data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
    else:
        prefs = UserPreference(user_id=user_id, **data)
        db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


# ── Articles ──────────────────────────────────────────────────────────────────

def save_article(db: Session, article_data: Dict[str, Any]) -> Article:
    article = Article(**article_data)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_articles_by_user(
    db: Session, user_id: str, skip: int = 0, limit: int = 20
) -> List[Article]:
    """Get articles sorted by relevance score descending."""
    return (
        db.query(Article)
        .filter(Article.user_id == user_id)
        .order_by(desc(Article.relevance_score))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_article(db: Session, article_id: str) -> Optional[Article]:
    return db.query(Article).filter(Article.id == article_id).first()


def update_article(db: Session, article_id: str, data: Dict[str, Any]) -> Optional[Article]:
    article = get_article(db, article_id)
    if article:
        for key, value in data.items():
            if hasattr(article, key):
                setattr(article, key, value)
        db.commit()
        db.refresh(article)
    return article


# ── Feedback ──────────────────────────────────────────────────────────────────

def create_feedback(db: Session, user_id: str, article_id: str, feedback_type: str) -> UserFeedback:
    fb = UserFeedback(user_id=user_id, article_id=article_id, feedback_type=feedback_type)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def get_feedback_for_article(db: Session, article_id: str) -> List[UserFeedback]:
    return db.query(UserFeedback).filter(UserFeedback.article_id == article_id).all()


# ── Digests ───────────────────────────────────────────────────────────────────

def create_digest(db: Session, user_id: str, digest_type: str, title: str, content: str, article_ids: List[str]) -> Digest:
    digest = Digest(user_id=user_id, digest_type=digest_type, title=title, content=content, article_ids=article_ids)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest


def get_digests_for_user(db: Session, user_id: str, limit: int = 10) -> List[Digest]:
    return db.query(Digest).filter(Digest.user_id == user_id).order_by(desc(Digest.generated_at)).limit(limit).all()


# ── Reading History ───────────────────────────────────────────────────────────

def log_reading(db: Session, user_id: str, article_id: str, read_time_seconds: int = 0) -> ReadingHistory:
    entry = ReadingHistory(user_id=user_id, article_id=article_id, read_time_seconds=read_time_seconds)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_reading_history(db: Session, user_id: str, limit: int = 50) -> List[ReadingHistory]:
    return (
        db.query(ReadingHistory)
        .filter(ReadingHistory.user_id == user_id)
        .order_by(desc(ReadingHistory.clicked_at))
        .limit(limit)
        .all()
    )


# ── Source Biases ─────────────────────────────────────────────────────────────

from app.db.models import SourceBias


def get_all_source_biases(db: Session) -> Dict[str, str]:
    """Return a dict mapping domain → bias_rating from the database."""
    biases = db.query(SourceBias).all()
    return {b.domain: b.bias_rating for b in biases}


def upsert_source_bias(db: Session, domain: str, bias_rating: str, confidence: float = 0.7, notes: str = None) -> SourceBias:
    bias = db.query(SourceBias).filter(SourceBias.domain == domain).first()
    if bias:
        bias.bias_rating = bias_rating
        bias.confidence = confidence
        bias.notes = notes
    else:
        bias = SourceBias(domain=domain, bias_rating=bias_rating, confidence=confidence, notes=notes)
        db.add(bias)
    db.commit()
    db.refresh(bias)
    return bias


def delete_source_bias(db: Session, domain: str) -> bool:
    bias = db.query(SourceBias).filter(SourceBias.domain == domain).first()
    if bias:
        db.delete(bias)
        db.commit()
        return True
    return False