import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import Organization, User, get_current_organization, get_current_user
from app.core.rate_limiter import auth_rate_limiter
from app.main import app

# Test SQLite in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_auth_rate_limiter():
    """Reset rate limiter before and after each test."""
    auth_rate_limiter.reset()
    yield
    auth_rate_limiter.reset()


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables for every test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def org_a(db_session):
    """Primary test organization."""
    org = Organization(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        name="Acme Corp India",
        slug="acme-india",
        is_active=True,
    )
    db_session.add(org)
    user = User(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        organization_id=org.id,
        email="admin@acme.in",
        full_name="Acme Admin",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def org_b(db_session):
    """Second test organization for multi-tenant isolation testing."""
    org = Organization(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        name="Beta Global Tech",
        slug="beta-global",
        is_active=True,
    )
    db_session.add(org)
    user = User(
        id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        organization_id=org.id,
        email="admin@betaglobal.com",
        full_name="Beta Admin",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def client(db_session, org_a):
    """FastAPI TestClient with db override and default org_a."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_org():
        return org_a

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_organization] = override_get_current_org

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
