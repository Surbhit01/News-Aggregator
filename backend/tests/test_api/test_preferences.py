"""
Tests for the preferences API routes.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db, init_db
from app.db.crud import create_user
from app.core.config import settings
from jose import jwt

client = TestClient(app)


def _get_token(user_id: str) -> str:
    """Generate a test JWT token."""
    return jwt.encode({"sub": user_id}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def test_get_preferences_no_auth():
    """Test that unauthenticated requests are rejected."""
    response = client.get("/api/preferences")
    assert response.status_code == 401


def test_get_preferences_default(db_session):
    """Test that default preferences are returned when none exist."""
    # Create a user directly
    user = create_user(db_session, "pref_test@example.com", "hashed")
    token = _get_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Override the DB dependency
    app.dependency_overrides[get_db] = lambda: db_session
    response = client.get("/api/preferences", headers=headers)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["categories"] == []
    assert data["keywords"] == []
    assert data["user_id"] == user.id


def test_update_preferences(db_session):
    """Test setting user preferences."""
    user = create_user(db_session, "update_test@example.com", "hashed")
    token = _get_token(user.id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "categories": ["Technology", "Finance"],
        "keywords": ["AI", "stocks"],
    }

    app.dependency_overrides[get_db] = lambda: db_session
    response = client.put("/api/preferences", json=payload, headers=headers)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "Technology" in data["categories"]
    assert "AI" in data["keywords"]


def test_preference_stats(db_session):
    """Test preference stats endpoint."""
    user = create_user(db_session, "stats_test@example.com", "hashed")
    token = _get_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    app.dependency_overrides[get_db] = lambda: db_session
    response = client.get("/api/preferences/stats", headers=headers)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "total_categories" in data