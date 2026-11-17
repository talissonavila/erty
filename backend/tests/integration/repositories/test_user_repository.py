from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserEmailConflictError, UserRepository


def test_create_user(db_session: Session) -> None:
    """Test that a user can be persisted in the database.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = User(
        email="test@example.com",
        hashed_password="hashed_password_example",
    )

    created_user = repository.create_user(user)

    assert created_user.id is not None
    assert created_user.email == "test@example.com"
    assert created_user.hashed_password == "hashed_password_example"


def test_get_by_email(db_session: Session) -> None:
    """Test that a user can be retrieved by email.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = User(
        email="search@example.com",
        hashed_password="hashed_password_example",
    )
    repository.create_user(user)

    retrieved_user = repository.get_by_email("search@example.com")

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


def test_get_by_id(db_session: Session) -> None:
    """Test that a user can be retrieved by ID.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = User(
        email="user_by_id@example.com",
        hashed_password="hashed_password_example",
    )
    repository.create_user(user)

    retrieved_user = repository.get_by_id(user.id)

    assert retrieved_user is not None
    assert retrieved_user.email == user.email
    assert retrieved_user.id == user.id


def test_create_user_with_duplicate_email(db_session: Session) -> None:
    """Test that creating users with duplicate emails raises an exception.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    first_user = User(
        email="duplicate@example.com",
        hashed_password="hashed_password_1",
    )
    second_user = User(
        email="duplicate@example.com",
        hashed_password="hashed_password_2",
    )

    repository.create_user(first_user)

    with pytest.raises(UserEmailConflictError):
        repository.create_user(second_user)

    retrieved_user = repository.get_by_email("duplicate@example.com")

    assert retrieved_user is not None
    assert retrieved_user.id == first_user.id


def test_get_by_email_returns_none_when_user_does_not_exist(
    db_session: Session,
) -> None:
    """Test that searching for a nonexistent email returns None.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = repository.get_by_email("nonexistent@example.com")

    assert user is None


def test_get_by_id_returns_none_when_user_does_not_exist(
    db_session: Session,
) -> None:
    """Test that searching for a nonexistent ID returns None.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = repository.get_by_id(999999)

    assert user is None


def test_create_user_with_default_values(db_session: Session) -> None:
    """Test that default values are correctly assigned to a new user.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = User(
        email="defaults@example.com",
        hashed_password="hashed_password_example",
    )

    created_user = repository.create_user(user)

    assert created_user.is_active is True
    assert created_user.created_at is not None


def test_create_user_propagates_unhandled_integrity_error(
    db_session: Session,
) -> None:
    """Test that unexpected integrity errors are propagated.

    Args:
        db_session (Session): Fixture instance for database.
    """
    repository = UserRepository(db_session)

    user = User(
        email="integrity@example.com",
        hashed_password="hashed_password_example",
    )

    error = IntegrityError(
        "INSERT INTO users (...)",
        {},
        Exception("Unexpected integrity error"),
    )

    with pytest.raises(IntegrityError) as exc_info:
        with patch.object(db_session, "flush", side_effect=error):
            repository.create_user(user)

    assert exc_info.value is error
