from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.url import URL


def test_redirects_to_original_url(
    client_with_db: TestClient,
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Test that an existing short URL redirects to its original URL.

    Args:
        client_with_db: Test client configured with the test database.
        db_session: Database session used to persist the URL.
        url_factory: Factory that creates a URL instance for testing.
    """
    url = url_factory()
    db_session.add(url)
    db_session.flush()

    response = client_with_db.get(
        f"/{url.short_code}",
        follow_redirects=False,
    )

    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert response.headers["location"] == url.original_url


def test_returns_404_when_short_code_does_not_exist(
    client_with_db: TestClient,
) -> None:
    """Test that a request with a non-existent short code returns 404.

    Args:
    client_with_db (TestClient): Test client configured with the test database.
    """
    response = client_with_db.get(
        "/missing123",
        follow_redirects=False,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Short URL not found."
    assert response.headers["content-type"].startswith("application/json")


def test_returns_404_when_url_is_inactive(
    client_with_db: TestClient,
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Test that an inactive URL cannot be accessed.

    Args:
        client_with_db: Test client configured with the test database.
        db_session: Database session used to persist the URL.
        url_factory: Factory that creates a URL instance for testing.
    """
    url = url_factory()
    url.is_active = False

    db_session.add(url)
    db_session.flush()

    response = client_with_db.get(
        f"/{url.short_code}",
        follow_redirects=False,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_returns_404_when_url_is_expired(
    client_with_db: TestClient,
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Test that an expired URL cannot be accessed.

    Args:
        client_with_db: Test client configured with the test database.
        db_session: Database session used to persist the URL.
        url_factory: Factory that creates a URL instance for testing.
    """
    url = url_factory()
    url.expires_at = datetime.now(UTC) - timedelta(days=1)

    db_session.add(url)
    db_session.flush()

    response = client_with_db.get(
        f"/{url.short_code}",
        follow_redirects=False,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_redirects_when_url_has_future_expiration(
    client_with_db: TestClient,
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Allows redirect when the URL has not expired.

    Args:
    client_with_db (TestClient): Test client configured with the test database.
    db_session (Session): Database session used to persist the URL.
    url_factory (Callable[[], URL]): Factory that creates a URL instance for testing.
    """
    url = url_factory()
    url.expires_at = datetime.now(UTC) + timedelta(days=1)

    db_session.add(url)
    db_session.flush()

    response = client_with_db.get(
        f"/{url.short_code}",
        follow_redirects=False,
    )

    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert response.headers["location"] == url.original_url
