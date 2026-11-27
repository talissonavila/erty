from collections.abc import Callable
from http import HTTPStatus
from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.url import get_url_service
from app.main import app
from app.models.url import URL
from app.models.user import User
from app.services.url_service import URLCodeGenerationError, URLService


def test_create_url_returns_201(
    client_with_db: TestClient,
    db_session: Session,
    access_token: str,
) -> None:
    """Returns 201 and persist the shortened URL.

    Args:
    client_with_db (TestClient): The test client configured with the test database.
    db_session (Session): Fixture instance for database.
    access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.post(
        "/urls",
        json={"original_url": "https://example.com/articles/erty"},
        headers=headers,
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


def test_create_url_returns_422_for_invalid_payload(
    client_with_db: TestClient,
    access_token: str,
) -> None:
    """Return 422 when the request payload contains an invalid URL.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.post(
        "/urls",
        json={"original_url": "not-a-valid-url"},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_url_returns_500_when_code_generation_fails(
    client_with_db: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    access_token: str,
) -> None:
    """Returns 500 when the service cannot generate a unique short code.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        monkeypatch (pytest.MonkeyPatch): The fixture used to override dependencies.
        access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    service = create_autospec(URLService, instance=True, spec_set=True)
    service.create_url.side_effect = URLCodeGenerationError(
        "Unable to generate a unique short code."
    )

    monkeypatch.setitem(app.dependency_overrides, get_url_service, lambda: service)

    response = client_with_db.post(
        "/urls",
        json={"original_url": "https://example.com/articles/erty"},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Unable to generate a unique short code."}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"original_url": ""},
        {"original_url": "ftp://example.com"},
        {"original_url": 123},
        {"unexpected_field": "value"},
    ],
)
def test_create_url_returns_422_for_invalid_payloads(
    client_with_db: TestClient,
    payload: dict[str, object],
    access_token: str,
) -> None:
    """Returns 422 when the payload violates the request schema.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        payload (dict[str, object]): Payload expected by '/urls' route to short a URL.
        access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client_with_db.post("/urls", json=payload, headers=headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_urls_returns_only_authenticated_user_urls(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    another_user: User,
    url_factory: Callable[[], URL],
    access_token: str,
) -> None:
    """Return only URLs belonging to the authenticated user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        another_user (User): Another user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    user_url = url_factory(user)
    another_user_url = url_factory(another_user)

    db_session.add_all([user_url, another_user_url])
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.get("/urls", headers=headers)

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert len(data["urls"]) == 1
    assert data["urls"][0]["id"] == user_url.id
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_urls_supports_pagination(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[], URL],
    access_token: str,
) -> None:
    """Return URLs according to the requested pagination.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    urls = [url_factory(user) for _ in range(3)]

    db_session.add_all(urls)
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.get(
        "/urls?limit=2&offset=1",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert len(data["urls"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_list_urls_requires_authentication(
    client_with_db: TestClient,
) -> None:
    """Return 401 when authentication is missing.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
    """
    response = client_with_db.get("/urls")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_url_returns_200_for_owner(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Return a URL when it belongs to the authenticated user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(user)
    db_session.add(url)
    db_session.commit()
    db_session.refresh(url)

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.get(
        f"/urls/{url.id}",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert data["id"] == url.id
    assert data["original_url"] == url.original_url
    assert data["short_code"] == url.short_code
    assert data["is_active"] is True


def test_get_url_returns_404_for_another_user_url(
    client_with_db: TestClient,
    db_session: Session,
    another_user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Prevent users from accessing URLs belonging to others.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        another_user (User): Another user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(another_user)
    db_session.add(url)
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.get(
        f"/urls/{url.id}",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_url_returns_404_for_nonexistent_url(
    client_with_db: TestClient,
    access_token: str,
) -> None:
    """Return 404 when the requested URL does not exist.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.get(
        "/urls/999999",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_url_returns_200(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Update a URL belonging to the authenticated user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(user)
    db_session.add(url)
    db_session.commit()
    db_session.refresh(url)

    headers = {"Authorization": f"Bearer {access_token}"}
    new_url = "https://example.com/updated"

    response = client_with_db.patch(
        f"/urls/{url.id}",
        json={"original_url": new_url, "is_active": False},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert data["original_url"] == new_url
    assert data["is_active"] is False
    assert data["short_code"] == url.short_code


def test_update_url_preserves_omitted_fields(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Preserve fields that were not included in the update payload.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(user)
    original_url = url.original_url
    short_code = url.short_code

    db_session.add(url)
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.patch(
        f"/urls/{url.id}",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert data["original_url"] == original_url
    assert data["short_code"] == short_code
    assert data["is_active"] is False


def test_update_url_can_clear_expires_at(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Allow clearing the URL expiration date.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    from datetime import UTC, datetime

    url = url_factory(user)
    url.expires_at = datetime(2027, 1, 1, tzinfo=UTC)

    db_session.add(url)
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.patch(
        f"/urls/{url.id}",
        json={"expires_at": None},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["expires_at"] is None


def test_update_url_returns_404_for_another_user_url(
    client_with_db: TestClient,
    db_session: Session,
    another_user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Prevent updating URLs belonging to another user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        another_user (User): Another user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(another_user)
    original_url = url.original_url

    db_session.add(url)
    db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.patch(
        f"/urls/{url.id}",
        json={"original_url": "https://example.com/unauthorized"},
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    db_session.refresh(url)
    assert url.original_url == original_url


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"original_url": None},
        {"is_active": None},
        {"unexpected_field": "value"},
    ],
)
def test_update_url_returns_422_for_invalid_payload(
    client_with_db: TestClient,
    access_token: str,
    payload: dict[str, object],
) -> None:
    """Reject invalid URL update payloads.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        access_token (str): Access token to be validated.
        payload (dict[str, object]): A dict with arguments used to update a URL.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.patch(
        "/urls/1",
        json=payload,
        headers=headers,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_url_returns_204(
    client_with_db: TestClient,
    db_session: Session,
    user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Delete a URL belonging to the authenticated user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(user)
    db_session.add(url)
    db_session.commit()
    db_session.refresh(url)

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.delete(
        f"/urls/{url.id}",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert db_session.get(URL, url.id) is None


def test_delete_url_returns_404_for_another_user_url(
    client_with_db: TestClient,
    db_session: Session,
    another_user: User,
    url_factory: Callable[[User], URL],
    access_token: str,
) -> None:
    """Prevent deleting URLs belonging to another user.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        db_session (Session): Fixture instance for database.
        another_user (User): Another user stored in test database.
        url_factory (Callable[[], URL]): Factory that creates a URL instance for
        testing.
        access_token (str): Access token to be validated.
    """
    url = url_factory(another_user)
    db_session.add(url)
    db_session.commit()
    db_session.refresh(url)

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.delete(
        f"/urls/{url.id}",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert db_session.get(URL, url.id) is not None


def test_delete_url_returns_404_for_nonexistent_url(
    client_with_db: TestClient,
    access_token: str,
) -> None:
    """Return 404 when attempting to delete a nonexistent URL.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
        access_token (str): Access token to be validated.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client_with_db.delete(
        "/urls/999999",
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_url_requires_authentication(
    client_with_db: TestClient,
) -> None:
    """Return 401 when authentication is missing.

    Args:
        client_with_db (TestClient): The test client configured with the test database.
    """
    response = client_with_db.delete("/urls/1")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
