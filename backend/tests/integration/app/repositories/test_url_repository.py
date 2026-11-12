from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models.url import URL
from app.repositories.url_repository import URLRepository


def test_create_url(
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Should persist a URL and return the created instance.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[], URL]): Fake instance of URL.
    """
    repository = URLRepository(db_session)

    url = url_factory()
    created_url = repository.create(url)

    assert created_url.id is not None
    assert created_url.short_code == url.short_code
    assert created_url.original_url == url.original_url


def test_get_by_short_code(
    db_session: Session,
    url_factory: Callable[[], URL],
) -> None:
    """Should retrievve a URL using its short code.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[], URL]): Fake instance of URL.

    """
    repository = URLRepository(db_session)

    url = repository.create(url_factory())

    result = repository.get_by_short_code(url.short_code)

    assert result is not None
    assert result.id == url.id
    assert result.short_code == url.short_code


def test_get_by_short_code_returns_none(db_session: Session) -> None:
    """Should return None when the short code does not exist.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = URLRepository(db_session)
    result = repository.get_by_short_code("no_exist")
    assert result is None
