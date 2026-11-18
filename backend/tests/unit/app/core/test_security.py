from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.settings import settings

MINUTE_IN_SECONDS = 60


@pytest.fixture
def plain_password() -> str:
    """Provide a plain password for testing.

    Returns:
        str: A plain password to use in tests.
    """
    return "mysecretpassword"


@pytest.fixture
def hashed_password(plain_password: str) -> str:
    """Provide a hashed password for testing.

    Args:
        plain_password (str): The plain password fixture.

    Returns:
        str: The hashed password.
    """
    return get_password_hash(plain_password)


@pytest.fixture
def access_token(plain_password: str) -> str:
    """Returns a JWT token based on a text.

    Args:
        plain_password (str): A plain password to use in tests.
    """
    return create_access_token(plain_password)


@pytest.fixture
def token_payload(access_token: str) -> dict[str, object]:
    """Returns the payload from token decode.

    Args:
        access_token (str): The JWT access token encoded.
    """
    return jwt.decode(
        access_token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )


@pytest.fixture
def incorrect_secret_key():
    """Returns a incorrect secret key."""
    return "a-incorrect-secret-key-string-to-use-in-tests"


def test_get_password_hash(
    plain_password: str,
    hashed_password: str,
):
    """Tests if get_password_hash function hashed the password correctly.

    Args:
        plain_password (str): The plain password fixture.
        hashed_password (str): The hashed password fixture.
    """
    assert hashed_password != plain_password
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0


def test_get_password_hash_generates_different_hashes(
    plain_password: str,
):
    """Tests if the get_password_hash generates different hash to every call.

    Args:
        plain_password (str): The plain password fixture.
    """

    hash1 = get_password_hash(plain_password)
    hash2 = get_password_hash(plain_password)

    assert hash1 != hash2


def test_verify_password_with_correct_password(
    plain_password: str,
    hashed_password: str,
):
    """Tests if verify_password validates correctly the password.

    Args:
        plain_password (str): The plain password fixture.
    """
    assert verify_password(plain_password, hashed_password) is True


def test_verify_password_with_incorrect_password(
    hashed_password: str,
):
    """Tests if verify_password returns False when password is incorrect.

    Args:
        hashed_password (str): The hashed password fixture.
    """
    assert verify_password("wrong_password", hashed_password) is False


def test_verify_password_with_empty_password(
    hashed_password: str,
):
    """Tests if verify_password returns False when password is empty.

    Args:
        hashed_password (str): The hashed password fixture.
    """

    assert verify_password("", hashed_password) is False


def test_get_password_hash_uses_argon2(
    hashed_password: str,
) -> None:
    """Test that the generated hash uses Argon2.

    Args:
        hashed_password (str): The hashed password fixture.
    """
    assert hashed_password.startswith("$argon2id$")


def test_create_access_token_generates_a_valid_token(access_token: str) -> None:
    """Tests if create_access_token function is a valid token.

    Ags:
        access_token (str): The token response from fixture.
    """
    assert isinstance(access_token, str)


def test_create_access_token_has_correct_payload(
    plain_password: str,
    token_payload: dict[str, object],
) -> None:
    """Tests if create_access_token function has correct payload.

    Ags:
        token_payload (dict[str, object]): The decode token payload.
    """

    assert "sub" in token_payload
    assert "iat" in token_payload
    assert "exp" in token_payload
    assert token_payload["sub"] == plain_password


def test_create_access_token_has_correct_expire_date(
    token_payload: dict[str, object],
) -> None:
    """Tests if create_access_token function has correct expiring date.

    Ags:
        token_payload (dict[str, object]): The decode token payload.
    """

    assert (
        token_payload["exp"] - token_payload["iat"]
        == (settings.jwt_access_token_expire_minutes) * MINUTE_IN_SECONDS
    )


def test_create_access_token_decodes_token_correctly(
    token_payload: dict[str, object], plain_password: str
) -> None:
    """Tests if create_access_token function decode token correctly.

    Ags:
        token_payload (dict[str, object]): The decode token payload.
        plain_password (str): The password used to generate token.
    """
    datetime_now = datetime.now(UTC)
    exp_datetime = datetime.fromtimestamp(token_payload["exp"], tz=UTC)

    assert exp_datetime > datetime_now
    assert token_payload["sub"] == plain_password


def test_create_access_token_rejects_token_with_invalid_signature(
    incorrect_secret_key: str,
):
    """Tests if create_access_token function rejects token decode with invalid
    signature.

    Args:
        incorrect_secret_key (str): Incorrect secret key.
    """
    invalid_token = jwt.encode(
        {"sub": "test_user"},
        incorrect_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            invalid_token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )


def test_create_access_token_rejects_when_token_has_expired():
    """Tests if create_access_token raises ExpiredSignatureError when token expires."""
    issued_at = datetime.now(UTC) - timedelta(minutes=10)
    expire = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "sub": "test-user",
        "iat": issued_at,
        "exp": expire,
    }
    expired_token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
