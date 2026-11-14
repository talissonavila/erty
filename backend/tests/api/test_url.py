from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.url import get_url_service
from app.db.session import get_db
from app.main import app
from app.models.url import URL
from app.services.url_service import URLCodeGenerationError, URLService


@pytest.fixture
def client_with_db(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Provide a test client connected to the test database.

    Args:
        client (TestClient): The test client.
        db_session (Session): Fixture instance for database.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.

    Returns:
        client (TestClient): The test client configured with the database override.
    """

    def override_get_db() -> Generator[Session, None, None]:
        """Yield the test database session."""
        yield db_session

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    return client


def test_create_url_returns_201(
    client_with_db: TestClient, db_session: Session
) -> None:
    """Returns 201 and persist the shortened URL.

    Args:
    client_with_db (TestClient): The test client configured with the test database.
    db_session (Session): Fixture instance for database.
    """
    response = client_with_db.post(
        "/urls", json={"original_url": "https://example.com/articles/erty"}
    )

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()

    assert data["original_url"] == "https://example.com/articles/erty"
    assert len(data["short_code"]) == URLService.CODE_LENGTH
    assert data["is_active"] is True
    assert data["id"] is not None
    assert data["created_at"] is not None

    persisted_url = db_session.get(URL, data["id"])

    assert persisted_url is not None
    assert persisted_url.short_code == data["short_code"]


def test_create_url_returns_422_for_invalid_payload(client_with_db: TestClient) -> None:
    """Return 422 when the request payload contains an invalid URL.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
    """
    response = client_with_db.post("/urls", json={"original_url": "not-a-valid-url"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_url_returns_500_when_code_generation_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Returns 500 when the service cannot generate a unique short code.

    Args:
        client (TestClient): The test client.
        monkeypatch (pytest.MonkeyPatch): The fixture used to override dependencies.
    """
    service = create_autospec(URLService, instance=True, spec_set=True)
    service.create_url.side_effect = URLCodeGenerationError(
        "Unable to generate a unique short code."
    )

    monkeypatch.setitem(app.dependency_overrides, get_url_service, lambda: service)

    response = client.post(
        "/urls", json={"original_url": "https://example.com/articles/erty"}
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Unable to generate a unique short code."}
