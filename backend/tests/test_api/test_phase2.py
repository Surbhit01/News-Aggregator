"""
Integration tests for Phase 2 endpoints: auth, digest, history, biases, feedback.
"""
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings
from app.db.session import get_db, init_db
from app.db.crud import create_user

client = TestClient(app)


def _get_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/auth/register", json={
            "email": "new@test.com", "password": "secret123"
        })
        app.dependency_overrides.clear()
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "new@test.com"
        assert data["token_type"] == "bearer"

    def test_register_duplicate(self, db_session):
        create_user(db_session, "dup@test.com", "hashed")
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/auth/register", json={
            "email": "dup@test.com", "password": "secret123"
        })
        app.dependency_overrides.clear()
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    def test_register_short_password(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/auth/register", json={
            "email": "short@test.com", "password": "ab"
        })
        app.dependency_overrides.clear()
        assert resp.status_code == 422

    def test_login(self, db_session):
        # Register first
        app.dependency_overrides[get_db] = lambda: db_session
        client.post("/api/auth/register", json={
            "email": "logintest@test.com", "password": "secret123"
        })
        resp = client.post("/api/auth/login", json={
            "email": "logintest@test.com", "password": "secret123"
        })
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_bad_password(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com", "password": "wrong"
        })
        app.dependency_overrides.clear()
        assert resp.status_code == 401

    def test_me(self, db_session):
        user = create_user(db_session, "me@test.com", "hashed_not_used")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@test.com"

    def test_me_no_auth(self):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


# ── Digest Tests ──────────────────────────────────────────────────────────────

class TestDigest:
    def test_digest_no_auth(self):
        resp = client.get("/api/digest?type=daily")
        assert resp.status_code == 401

    def test_digest_first_request_returns_202(self, db_session):
        user = create_user(db_session, "digest@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/digest?type=daily",
                          headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        # Should return 202 (being generated) since no digest exists yet
        assert resp.status_code == 202

    def test_digest_on_demand_requires_topic(self, db_session):
        user = create_user(db_session, "ondemand@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/digest?type=on_demand",
                          headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 422

    def test_digest_on_demand_returns_202(self, db_session):
        user = create_user(db_session, "ondemand2@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/digest?type=on_demand&topic=AI",
                          headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 202

    def test_articles_list(self, db_session):
        user = create_user(db_session, "articles@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/digest/articles?max_minutes=5",
                          headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_article_tldr_not_found(self, db_session):
        user = create_user(db_session, "tldr@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/digest/articles/nonexistent-id/tldr",
                          headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 404


# ── History Tests ─────────────────────────────────────────────────────────────

class TestHistory:
    def test_history_no_auth(self):
        resp = client.get("/api/history")
        assert resp.status_code == 401

    def test_log_reads(self, db_session):
        user = create_user(db_session, "history@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session

        # Log a read
        resp = client.post("/api/history/log",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": "art-123", "read_time_seconds": 60})
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged"

        # Retrieve history
        resp = client.get("/api/history",
            headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["article_id"] == "art-123"


# ── Bias Tests ────────────────────────────────────────────────────────────────

class TestBiases:
    def test_list_biases_no_auth(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/biases")
        app.dependency_overrides.clear()
        assert resp.status_code == 200  # Public endpoint

    def test_create_bias_requires_auth(self, db_session):
        resp = client.post("/api/biases", json={
            "domain": "example.com", "bias_rating": "neutral"
        })
        assert resp.status_code == 401

    def test_create_and_list_bias(self, db_session):
        user = create_user(db_session, "bias@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session

        # Create
        resp = client.post("/api/biases",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": "example.com", "bias_rating": "neutral", "confidence": 0.9})
        assert resp.status_code == 201
        assert resp.json()["domain"] == "example.com"

        # List should include it
        resp = client.get("/api/biases")
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        # The list returns domain → bias_rating mapping

    def test_create_invalid_bias(self, db_session):
        user = create_user(db_session, "bias2@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/biases",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": "test.com", "bias_rating": "invalid_value"})
        app.dependency_overrides.clear()
        assert resp.status_code == 422

    def test_delete_bias(self, db_session):
        user = create_user(db_session, "bias3@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session

        # Create
        client.post("/api/biases",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": "delete-me.com", "bias_rating": "liberal"})

        # Delete
        resp = client.delete("/api/biases/delete-me.com",
            headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200

    def test_delete_nonexistent_bias(self, db_session):
        user = create_user(db_session, "bias4@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.delete("/api/biases/nonexistent.com",
            headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 404


# ── Feedback Tests ────────────────────────────────────────────────────────────

class TestFeedback:
    def test_feedback_no_auth(self):
        resp = client.get("/api/feedback")
        assert resp.status_code in (401, 405)  # 405 if no GET handler

    def test_submit_feedback(self, db_session):
        user = create_user(db_session, "fb@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": "art-fb-1", "feedback_type": "show_more"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["feedback_type"] == "show_more"

    def test_feedback_invalid_type(self, db_session):
        user = create_user(db_session, "fb2@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.post("/api/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": "art-fb-2", "feedback_type": "invalid"})
        app.dependency_overrides.clear()
        assert resp.status_code == 422


# ── Preference Stats Tests ────────────────────────────────────────────────────

class TestPreferenceStats:
    def test_stats_no_prefs(self, db_session):
        user = create_user(db_session, "stats@test.com", "hashed")
        token = _get_token(user.id)
        app.dependency_overrides[get_db] = lambda: db_session
        resp = client.get("/api/preferences/stats",
            headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["total_categories"] == 0