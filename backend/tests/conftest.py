"""
Pytest configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.db.models import User
from app.core.config import settings

# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite:///./test_news_aggregator.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a clean test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for tests."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_test_password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user