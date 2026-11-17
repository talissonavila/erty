import pytest

from app.core.security import get_password_hash, verify_password


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
