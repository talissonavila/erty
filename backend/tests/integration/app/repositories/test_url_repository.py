from collections.abc import Callable
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.url import URL
from app.models.user import User
from app.repositories.url_repository import URLRepository, URLShortCodeConflictError


def test_create_url(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should persist a URL and return the created instance.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    url = url_factory(user)
    created_url = repository.create(url)

    assert created_url.id is not None
    assert created_url.short_code == url.short_code
    assert created_url.original_url == url.original_url
    assert created_url.created_at is not None
    assert created_url.is_active is True
    assert created_url.expires_at is None


def test_get_by_short_code(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should retrievve a URL using its short code.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    url = repository.create(url_factory(user))

    result = repository.get_by_short_code(url.short_code)

    assert result is not None
    assert result.id == url.id
    assert result.short_code == url.short_code
    assert result.original_url == url.original_url
    assert result.created_at is not None
    assert result.is_active is True


def test_get_by_short_code_returns_none(db_session: Session) -> None:
    """Should return None when the short code does not exist.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = URLRepository(db_session)
    result = repository.get_by_short_code("no_exist")
    assert result is None


def test_create_raises_conflict_for_duplicate_short_code(
    db_session: Session,
    user: User,
) -> None:
    """Should isolate duplicate short code errors using a savepoint.

    Args:
        db_session (Session): Fixture instance for database.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    original_url = URL(
        original_url="https://example.com",
        short_code="duplicate1",
        user_id=user.id,
    )

    repository.create(original_url)

    duplicate_url = URL(
        original_url="http://another-example.com",
        short_code="duplicate1",
        user_id=user.id,
    )

    with pytest.raises(URLShortCodeConflictError):
        repository.create(duplicate_url)

    result = repository.get_by_short_code("duplicate1")

    assert result is not None
    assert result.original_url == "https://example.com"


def test_create_raises_integrity_error_for_other_constraints(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Raise IntegrityError when another database constraint fails.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)
    url = url_factory(user)

    error = IntegrityError(
        statement="INSERT", params={}, orig=Exception("Other integrity error")
    )

    with patch.object(repository.session, "flush", side_effect=error):
        with pytest.raises(IntegrityError) as exc:
            repository.create(url)

    assert exc.value is error


def test_get_all_by_user_id(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should retrieve only URLs beloging to the specific user.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    first_url = repository.create(url_factory(user))
    second_url = repository.create(url_factory(user))

    result = repository.get_all_by_user_id(user.id)

    assert len(result) == 2
    assert {url.id for url in result} == {first_url.id, second_url.id}
    assert all(url.user_id == user.id for url in result)


def test_get_all_by_user_id_respects_pagination(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should respect limit and offset when retrieving URLs.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    urls = [repository.create(url_factory(user)) for _ in range(3)]

    result = repository.get_all_by_user_id(user_id=user.id, limit=2, offset=1)

    assert len(result) == 2
    assert {url.id for url in result}.issubset({url.id for url in urls})


def test_get_by_id_and_user_id(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should retrieve a URL beloging to the specific user.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    url = repository.create(url_factory(user))

    result = repository.get_by_id_and_user_id(
        url_id=url.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == url.id


def test_get_by_id_and_user_id_returns_none_for_another_user(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
    another_user: User,
) -> None:
    """Should not retrieve URLs beloging to another user.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
        another_user (User): Another user stored in test database.
    """
    repository = URLRepository(db_session)

    url = repository.create(url_factory(user))

    result = repository.get_by_id_and_user_id(
        url_id=url.id,
        user_id=another_user.id,
    )

    assert result is None


def test_delete_url(
    db_session: Session,
    url_factory: Callable[[User], URL],
    user: User,
) -> None:
    """Should delete a URL from the database.

    Args:
        db_session (Session): Fixture instance for database.
        url_factory (Callable[[User], URL]): Fake instance of URL.
        user (User): A user stored in test database.
    """
    repository = URLRepository(db_session)

    url = repository.create(url_factory(user))

    repository.delete(url)

    result = repository.get_by_id_and_user_id(
        url_id=url.id,
        user_id=user.id,
    )
    assert result is None
