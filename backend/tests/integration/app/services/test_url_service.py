from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models.url import URL
from app.repositories.url_repository import URLRepository
from app.services.url_service import URLService


def test_create_url_persists_url_in_database(
    db_session: Session,
) -> None:
    """Ensure URLService creates and persists a URL in PostgreSQL.

    Args:
    db_session (Session): Fixture instance for database.
    """
    repository = URLRepository(db_session)
    service = URLService(repository)

    created_url = service.create_url("https://example.com/articles/erty")

    persisted_url = db_session.get(URL, created_url.id)

    assert persisted_url is not None
    assert persisted_url.original_url == "https://example.com/articles/erty"
    assert persisted_url.short_code == created_url.short_code
    assert len(persisted_url.short_code) == URLService.CODE_LENGTH
    assert persisted_url.is_active is True
    assert persisted_url.created_at is not None


def test_get_original_url_retrieves_persisted_url(
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Ensure URLService retrieves a URL persisted in PostgreSQL.

    Args:
    db_session (Session): Fixture instance for database.
    url_factory (Callable[[], URL]): Factory that creates a URL instance for testing.
    """
    repository = URLRepository(db_session)
    service = URLService(repository)

    url = url_factory()
    db_session.add(url)
    db_session.flush()

    original_url = service.get_original_url(url.short_code)

    assert original_url == url.original_url
