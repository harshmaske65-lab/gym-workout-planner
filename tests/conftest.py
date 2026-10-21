"""Test setup that isolates the app from the real gym.db file.

The tests install a temporary in-memory SQLAlchemy database module before
importing main.py. This prevents tests from adding/removing rows in gym.db.
Run pytest from the project root so templates/ and static/ resolve correctly.
"""
from __future__ import annotations

import os
import sys
import tempfile
import types

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# These values are for tests only, not production secrets.
os.environ["GYM_SESSION_SECRET"] = "white-box-tests-only-secret-do-not-use-in-production"
os.environ["GYM_HTTPS_ONLY"] = "false"

_test_tmpdir = tempfile.TemporaryDirectory(prefix="gym-planner-tests-")
_test_db_path = os.path.join(_test_tmpdir.name, "white_box_test.db")
_test_engine = create_engine(
    f"sqlite:///{_test_db_path}",
    connect_args={"check_same_thread": False},
)
_TestBase = declarative_base()
_TestSessionLocal = sessionmaker(
    bind=_test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def _test_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Provide a temporary `database` module before `main` or `models` import it.
# This is intentionally isolated from the project's real database.py / gym.db.
_test_database_module = types.ModuleType("database")
_test_database_module.Base = _TestBase
_test_database_module.engine = _test_engine
_test_database_module.SessionLocal = _TestSessionLocal
_test_database_module.get_db = _test_get_db
sys.modules["database"] = _test_database_module
sys.modules.pop("models", None)
sys.modules.pop("main", None)

import main  # noqa: E402  (must import only after replacing the database module)
from models import MembershipPlan, MembershipSelection, User  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(clean_database):
    """FastAPI test client with DB dependency overridden to the in-memory DB."""
    main.app.dependency_overrides[main.get_db] = _test_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_database():
    """Give each test clean user/selection data while keeping seeded plans."""
    _TestBase.metadata.create_all(bind=_test_engine)
    db = _TestSessionLocal()
    try:
        db.query(MembershipSelection).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.query(MembershipPlan).update({MembershipPlan.is_active: True})
        db.commit()
    finally:
        db.close()
    yield
    db = _TestSessionLocal()
    try:
        db.query(MembershipSelection).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.query(MembershipPlan).update({MembershipPlan.is_active: True})
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db_session():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def create_user():
    """Create a test user. Returns the persisted User object ID."""
    def _create_user(email: str, *, name: str = "Test Member", password: str = "StrongPass123!", role: str = "user") -> int:
        db = _TestSessionLocal()
        try:
            user = User(
                full_name=name,
                email=email.strip().lower(),
                password_hash=main.password_hasher.hash(password),
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id
        finally:
            db.close()
    return _create_user
def pytest_unconfigure(config):
    """Close SQLite connections before cleaning up the temporary database."""
    _test_engine.dispose()
    _test_tmpdir.cleanup()