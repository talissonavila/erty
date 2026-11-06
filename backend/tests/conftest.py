from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    with SessionLocal() as session:
        yield session


@pytest.fixture
def db_dependency() -> Generator[Session, None, None]:
    """Provide a session through the get_db_dependency."""
    generator = get_db()
    session = next(generator)

    yield session

    generator.close()
