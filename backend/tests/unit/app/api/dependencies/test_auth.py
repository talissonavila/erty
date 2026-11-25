from collections.abc import Generator
from unittest.mock import Mock, create_autospec, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.models.user import User

ERROR_MESSAGE = "User credentials invalid."


@pytest.fixture
def mock_user_repository() -> Generator[Mock, None, None]:
    """Provide a mocked UserRepository instance."""
    with patch("app.api.dependencies.auth.UserRepository") as _mock:
        yield _mock


@pytest.fixture
def mock_decode_access_token() -> Generator[Mock, None, None]:
    """Provide a mocked decode_access_token function."""
    with patch("app.api.dependencies.auth.decode_access_token") as _mock:
        yield _mock


@pytest.fixture
def mock_session() -> Session:
    """Provide a mocked SQLAlchemy Session instance."""
    return create_autospec(Session, instance=True, spec_set=True)


def test_get_current_user_returns_user_to_decoded_token(
    mock_user_repository: Mock,
    mock_decode_access_token: Mock,
    user: User,
    access_token: str,
    mock_session: Session,
) -> None:
    """Ensure get_current_user returns the user when the token is decoded successfully.

    Args:
        mock_user_repository (Mock): Mocked UserRepository class.
        mock_decode_access_token (Mock): Mocked decode_access_token function.
        user (User): User instance returned by the repository.
        access_token (str): Valid access token.
        mock_session (Session): Mocked database session.
    """
    payload = {"sub": "1"}

    mock_decode_access_token.return_value = payload
    mock_user_repository.return_value.get_by_id.return_value = user

    result = get_current_user(token=access_token, session=mock_session)

    assert result is user
    mock_decode_access_token.assert_called_once_with(access_token)
    mock_user_repository.return_value.get_by_id.assert_called_once_with(1)


def test_get_current_user_raises_error_to_invalid_token(
    mock_decode_access_token: Mock,
    mock_session: Session,
    access_token: str,
) -> None:
    """Ensure get_current_user raises HTTPException for an invalid token.

    Args:
        mock_decode_access_token (Mock): Mocked decode_access_token function.
        mock_session (Session): Database session fixture.
        access_token (str): Access token to be validated.
    """
    mock_decode_access_token.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=access_token,
            session=mock_session,
        )

    assert exc_info.value.detail == ERROR_MESSAGE
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize(
    "payload",
    [
        {"iat": 1795108244, "exp": 1795110044},
        {"sub": "abc", "iat": 1795108244, "exp": 1795110044},
    ],
    ids=["missing-sub", "non-numeric-sub"],
)
def test_get_current_user_raises_error_to_invalid_sub(
    payload: dict[str, object],
    mock_decode_access_token: Mock,
    mock_session: Session,
    access_token: str,
) -> None:
    """Ensure get_current_user raises HTTPException for an invalid subject.

    Args:
        payload (dict[str, object]): Decoded token payload with a missing or
        non-numeric subject.
        mock_decode_access_token (Mock): Mocked decode_access_token function.
        mock_session (Session): Mocked database session.
        access_token (str): Access token to be validated.
    """
    mock_decode_access_token.return_value = payload

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=access_token, session=mock_session)

    assert exc_info.value.detail == ERROR_MESSAGE
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_raises_error_to_missing_user(
    mock_decode_access_token: Mock,
    mock_user_repository: Mock,
    mock_session: Session,
    access_token: str,
) -> None:
    """Ensure get_current_user raises HTTPException when user doesn't exist.

    Args:
        mock_decode_access_token (Mock): Mocked decode_access_token function.
        mock_user_repository (Mock): Mocked UserRepository class.
        mock_session (Session): Mocked database session.
        access_token (str): Access token to be validated.
    """
    mock_decode_access_token.return_value = {"sub": "999999"}
    mock_user_repository.return_value.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=access_token,
            session=mock_session,
        )
    assert exc_info.value.detail == ERROR_MESSAGE
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_raises_error_to_inactive_user(
    mock_decode_access_token: Mock,
    mock_user_repository: Mock,
    mock_session: Session,
    mock_user: User,
    access_token: str,
) -> None:
    """Ensure get_current_user raises HTTPException for an inactive user.

    Args:
        mock_decode_access_token (Mock): Mocked decode_access_token function.
        mock_user_repository (Mock): Mocked UserRepository class.
        mock_session (Session): Mocked database session.
        mock_user (User): Inactive user instance.
        access_token (str): Valid access token.
    """
    mock_decode_access_token.return_value = {"sub": "1"}
    mock_user.is_active = False
    mock_user_repository.return_value.get_by_id.return_value = mock_user

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=access_token,
            session=mock_session,
        )

    assert exc_info.value.detail == ERROR_MESSAGE
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
