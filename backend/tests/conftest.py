"""Shared test fixtures and configuration for VERISUB backend tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

# Import all models so they register with Base.metadata
import backend.app.models  # noqa: F401

# ── Test database setup ──────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# Enable foreign key enforcement on SQLite
@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Fixtures ─────────────────────────────────────────────────────────
@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(setup_database) -> Generator[Session, None, None]:
    """Provide a transactional database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(setup_database) -> Generator[TestClient, None, None]:
    """Provide a TestClient with the test database wired in."""

    def _override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper constants ─────────────────────────────────────────────────
VALID_PASSWORD = "StrongP@ss1"
WEAK_PASSWORD = "weak"
REGISTER_PAYLOAD = {
    "organization_name": "TestCo",
    "organization_email": "org@testco.com",
    "admin_full_name": "Admin User",
    "admin_email": "admin@testco.com",
    "admin_password": VALID_PASSWORD,
}


def register_and_login(client: TestClient, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Register an organization and return the response data including tokens."""
    if payload is None:
        payload = REGISTER_PAYLOAD.copy()
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    return resp.json()


def auth_headers(access_token: str, org_id: str | None = None) -> dict[str, str]:
    """Build authorization headers for authenticated requests."""
    headers = {"Authorization": f"Bearer {access_token}"}
    if org_id:
        headers["X-Organization-ID"] = str(org_id)
    return headers
