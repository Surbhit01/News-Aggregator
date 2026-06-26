"""
Automated persona test flows.
Each persona registers, configures preferences, exercises the API,
asserts on responses, and cleans up.
All API calls use the test DB via dependency_overrides.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(email: str, password: str):
    """Register a test user. Dependency override must be set by caller."""
    resp = client.post("/api/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    data = resp.json()
    return data["access_token"], data["user_id"]


def _setup(db_session):
    """Set the test DB dependency override and return cleanup."""
    app.dependency_overrides[get_db] = lambda: db_session
    return lambda: app.dependency_overrides.clear()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Persona: Alex (Tech Executive) ───────────────────────────────────────────

class TestAlexPersona:
    """Busy VP of Engineering — tech + finance, AI keywords, feedback loop."""

    EMAIL = "persona_alex@test.com"
    PWD = "alex123"

    def test_01_register(self, db_session):
        cleanup = _setup(db_session)
        resp = client.post("/api/auth/register", json={"email": self.EMAIL, "password": self.PWD})
        cleanup()
        assert resp.status_code == 201
        assert "access_token" in resp.json()

    def test_02_set_preferences(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.put("/api/preferences", json={
            "categories": ["Technology", "Finance"],
            "keywords": ["AI", "machine learning", "fintech", "startup funding"],
            "tracked_entities": [{"type": "industry", "name": "fintech"}, {"type": "stock", "name": "NVDA"}],
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        data = resp.json()
        assert "Technology" in data["categories"]
        assert "AI" in data["keywords"]
        assert len(data["tracked_entities"]) == 2

    def test_03_get_preferences(self, db_session):
        cleanup = _setup(db_session)
        token, uid = _register(self.EMAIL, self.PWD)
        client.put("/api/preferences", json={"categories": ["Technology"]}, headers=_auth_header(token))
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["user_id"] == uid

    def test_04_preference_stats(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        client.put("/api/preferences", json={"categories": ["Technology", "Finance"]}, headers=_auth_header(token))
        resp = client.get("/api/preferences/stats", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["total_categories"] >= 2

    def test_05_digest_triggers_generation(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest?type=daily", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 202

    def test_06_articles_list(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest/articles", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200

    def test_07_articles_filtered(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest/articles?max_minutes=5", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200

    def test_08_submit_feedback(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/feedback", json={
            "article_id": "test-art-alex-1", "feedback_type": "show_more",
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["feedback_type"] == "show_more"

    def test_09_log_reading(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/history/log", json={
            "article_id": "test-art-alex-2", "read_time_seconds": 45,
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged"

    def test_10_get_history(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        client.post("/api/history/log", json={"article_id": "test-hx", "read_time_seconds": 30}, headers=_auth_header(token))
        resp = client.get("/api/history", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ── Persona: Maria (Policy Analyst) ──────────────────────────────────────────

class TestMariaPersona:
    """Think tank analyst — geopolitics, source curation, bias management."""

    EMAIL = "persona_maria@test.com"
    PWD = "maria456"

    def test_01_set_preferences_with_sources(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.put("/api/preferences", json={
            "categories": ["Geopolitics", "Science", "Health"],
            "keywords": ["regulation", "policy", "climate change", "public health"],
            "preferred_sources": ["https://reuters.com", "https://bbc.com"],
            "blocked_sources": ["https://breitbart.com"],
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        data = resp.json()
        assert "reuters.com" in str(data["preferred_sources"]).lower()
        assert "breitbart.com" in str(data["blocked_sources"]).lower()

    def test_02_add_custom_bias(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/biases", json={
            "domain": "apnews.com", "bias_rating": "neutral", "confidence": 0.9,
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 201
        assert resp.json()["domain"] == "apnews.com"

    def test_03_list_biases(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        client.post("/api/biases", json={"domain": "apnews.com", "bias_rating": "neutral"}, headers=_auth_header(token))
        resp = client.get("/api/biases")
        cleanup()
        assert resp.status_code == 200

    def test_04_delete_nonexistent_bias(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.delete("/api/biases/nonexistent.com", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 404

    def test_05_create_invalid_bias(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/biases", json={
            "domain": "x.com", "bias_rating": "invalid",
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 422

    def test_06_digest_on_demand(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest?type=on_demand&topic=climate", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 202

    def test_07_digest_on_demand_no_topic(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest?type=on_demand", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 422

    def test_08_submit_feedback_show_less(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/feedback", json={
            "article_id": "test-art-maria", "feedback_type": "show_less",
        }, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200

    def test_09_bias_crud_cycle(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        # Create
        client.post("/api/biases", json={"domain": "test-cycle.com", "bias_rating": "liberal"}, headers=_auth_header(token))
        # Delete
        resp = client.delete("/api/biases/test-cycle.com", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200


# ── Persona: Priya (Casual Consumer) ─────────────────────────────────────────

class TestPriyaPersona:
    """Marketing professional — broad categories, casual usage, error testing."""

    EMAIL = "persona_priya@test.com"
    PWD = "priya789"

    def test_01_register_minimal(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.put("/api/preferences", json={"categories": ["Technology", "Sports", "Entertainment"]}, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["categories"] == ["Technology", "Sports", "Entertainment"]

    def test_02_get_user_profile(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/auth/me", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["email"] == self.EMAIL

    def test_03_login(self, db_session):
        cleanup = _setup(db_session)
        _register(self.EMAIL, self.PWD)
        resp = client.post("/api/auth/login", json={"email": self.EMAIL, "password": self.PWD})
        cleanup()
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_04_login_wrong_password(self, db_session):
        cleanup = _setup(db_session)
        resp = client.post("/api/auth/login", json={"email": "nonexistent@test.com", "password": "wrong"})
        cleanup()
        assert resp.status_code == 401

    def test_05_register_duplicate(self, db_session):
        cleanup = _setup(db_session)
        _register(self.EMAIL, self.PWD)
        resp = client.post("/api/auth/register", json={"email": self.EMAIL, "password": self.PWD})
        cleanup()
        assert resp.status_code == 409

    def test_06_register_short_password(self, db_session):
        cleanup = _setup(db_session)
        resp = client.post("/api/auth/register", json={"email": "short@test.com", "password": "ab"})
        cleanup()
        assert resp.status_code == 422

    def test_07_feedback_invalid_type(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.post("/api/feedback", json={"article_id": "x", "feedback_type": "invalid"}, headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 422

    def test_08_article_tldr_not_found(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/digest/articles/bad-id/tldr", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 404

    def test_09_unauthorized_access(self, db_session):
        resp = client.get("/api/preferences")
        assert resp.status_code == 401

    def test_10_health_check(self, db_session):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Persona: Dev (API Edge Cases) ────────────────────────────────────────────

class TestDevPersona:
    """Technical user testing edge cases and error handling."""

    EMAIL = "persona_dev@test.com"
    PWD = "devpass123"

    def test_01_full_preference_workflow(self, db_session):
        cleanup = _setup(db_session)
        token, uid = _register(self.EMAIL, self.PWD)
        # Set all fields
        client.put("/api/preferences", json={
            "categories": ["Technology"],
            "keywords": ["AI", "cloud"],
            "preferred_sources": ["https://techcrunch.com"],
            "blocked_sources": ["https://example.com"],
            "tracked_entities": [{"type": "stock", "name": "AAPL"}],
        }, headers=_auth_header(token))
        # Verify all persisted
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        data = resp.json()
        assert data["categories"] == ["Technology"]
        assert "AI" in data["keywords"]
        assert any("techcrunch" in s.lower() for s in data["preferred_sources"])
        assert any("example" in s.lower() for s in data["blocked_sources"])
        assert any(e["name"] == "AAPL" for e in data["tracked_entities"])

    def test_02_preferences_empty_defaults(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200
        assert resp.json()["categories"] == []

    def test_03_invalid_token(self, db_session):
        resp = client.get("/api/preferences", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    def test_04_digest_no_auth(self, db_session):
        assert client.get("/api/digest?type=daily").status_code == 401
        assert client.get("/api/digest/articles").status_code == 401

    def test_05_incremental_updates(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        # Set categories
        client.put("/api/preferences", json={"categories": ["Technology"]}, headers=_auth_header(token))
        # Add keywords (should not lose categories)
        client.put("/api/preferences", json={"keywords": ["AI"]}, headers=_auth_header(token))
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        data = resp.json()
        assert "Technology" in data["categories"]
        assert "AI" in data["keywords"]


# ── Persona: Sam (Preference Persistence) ────────────────────────────────────

class TestSamPersona:
    """Tests preference persistence, tracked entities, and history."""

    EMAIL = "persona_sam@test.com"
    PWD = "sam2024"

    def test_01_tracked_entities(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        client.put("/api/preferences", json={
            "tracked_entities": [{"type": "stock", "name": "AAPL"}, {"type": "industry", "name": "EV"}],
        }, headers=_auth_header(token))
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        assert len(resp.json()["tracked_entities"]) == 2

    def test_02_multiple_reads_logged(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        for i in range(5):
            client.post("/api/history/log", json={"article_id": f"hist-{i}", "read_time_seconds": 30}, headers=_auth_header(token))
        resp = client.get("/api/history?limit=10", headers=_auth_header(token))
        cleanup()
        assert len(resp.json()) == 5

    def test_03_feedback_then_get_prefs(self, db_session):
        cleanup = _setup(db_session)
        token, _ = _register(self.EMAIL, self.PWD)
        client.post("/api/feedback", json={"article_id": "fb-art", "feedback_type": "show_more"}, headers=_auth_header(token))
        resp = client.get("/api/preferences", headers=_auth_header(token))
        cleanup()
        assert resp.status_code == 200