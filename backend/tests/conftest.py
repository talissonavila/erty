from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, get_db
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated database session for integration tests."""
    connection = engine.connect()
    transaction = connection.begin()

    session = SessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_dependency() -> Generator[Session, None, None]:
    """Provide a session through the get_db dependency."""
    yield from get_db()
