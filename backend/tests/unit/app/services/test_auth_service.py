from typing import cast
from unittest.mock import create_autospec, patch

import pytest

from app.core.security import decode_access_token, get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService, InvalidCredentialsError


@pytest.fixture
def repository() -> UserRepository:
    """Returns a mocked UserRepository instance."""
    return cast(
        UserRepository,
        create_autospec(UserRepository, instance=True, spec_set=True),
    )


@pytest.fixture
def service(repository: UserRepository) -> AuthService:
    """Returns a AuthService with a mocked repository.

    Args:
        repository (UserRepository): The mocked UserRepository instance.
    """
    return AuthService(repository)


@pytest.fixture
def mock_user(password: str) -> User:
    """Returns a mocked User.

    Args:
        password (str): A plain password fixture.
    """
    return User(
        id=1,
        email="user_by_id@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
    )


@pytest.fixture
def authenticated_service(
    service: AuthService,
    repository: UserRepository,
    mock_user: User,
) -> AuthService:
    """Returns an AuthService configured with a valid user.

    Args:
        service (AuthService): A AuthService with a mocked repository.
        repository (UserRepository): A mocked UserRepository instance.
        mock_user (User): A mocked user.
    """
    repository.get_by_email.return_value = mock_user
    return service


def test_authenticate_raises_error_when_user_not_found(
    service: AuthService, repository: UserRepository, mock_user: User, password: str
):
    """Tests if authenticate method raises InvalidCredentialsError with proper message
    when user is not found.

    Args:
        service (AuthService): A AuthService with a mocked repository.
        repository (UserRepository): A mocked UserRepository instance.
        mock_user (User): A mocked user. Used to get user email.
        password (str): A plain password.
    """
    repository.get_by_email.return_value = None
    with pytest.raises(InvalidCredentialsError, match="User credentials invalid."):
        service.authenticate(email=mock_user.email, password=password)

    repository.get_by_email.assert_called_once_with(mock_user.email)


def test_authenticate_raises_error_when_user_is_inactive(
    authenticated_service: AuthService, mock_user: User, password: str
):
    """Tests if authenticate method raises InvalidCredentialsError with proper message
    when user is inactive.

    Args:
        authenticated_service (AuthService): A mocked AuthService with a mocked user
        created.
        mock_user (User): A mocked user.
        password (str): A plain password.
    """
    mock_user.is_active = False
    with pytest.raises(InvalidCredentialsError, match="User credentials invalid."):
        authenticated_service.authenticate(
            email=mock_user.email,
            password=password,
        )


@patch("app.services.auth_service.verify_password", return_value=False)
def test_authenticate_raises_error_when_password_is_incorrect(
    mock_verify_password,
    authenticated_service: AuthService,
    mock_user: User,
    password: str,
):
    """Tests if authenticate method raises InvalidCredentialsError with proper message
    when password is incorrect.

    Args:
        mock_verify_password ():
        authenticated_service (AuthService): A mocked AuthService with a mocked user
        created.
        mock_user (User): A mocked user.
        password (str):
    """
    with pytest.raises(InvalidCredentialsError, match="User credentials invalid."):
        authenticated_service.authenticate(email=mock_user.email, password=password)
    mock_verify_password.assert_called_once_with(
        plain_password=password,
        hashed_password=mock_user.hashed_password,
    )


def test_authenticate_returns_token_when_credentials_are_valid(
    authenticated_service: AuthService,
    mock_user: User,
    password: str,
):
    """Tests if authenticate method returns a JWT token when credentials are valid.

    Args:
        authenticated_service (AuthService): A mocked AuthService with a mocked user
        created.
        mock_user (User): A mocked user.
        password (str): A plain password.
    """
    access_token = authenticated_service.authenticate(
        email=mock_user.email,
        password=password,
    )
    assert isinstance(access_token, str)
    assert access_token != ""


def test_authenticate_returns_token_with_user_id_as_subject(
    authenticated_service: AuthService,
    mock_user: User,
    password: str,
):
    """Tests if authenticate method returns token with user id as payload subject.

    Args:
        authenticated_service (AuthService): A mocked AuthService with a mocked user
        created.
        mock_user (User): A mocked user.
        password (str): A plain password.
    """
    access_token = authenticated_service.authenticate(
        email=mock_user.email,
        password=password,
    )

    payload = decode_access_token(access_token)

    assert all(key in payload for key in ["sub", "iat", "exp"])
    assert payload["sub"] == str(mock_user.id)
    assert payload["exp"] > payload["iat"]
