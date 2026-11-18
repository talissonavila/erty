from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.settings import settings

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Generate a secure password hash.

    Args:
        password (str): Password without hash.

    Returns:
        str: Password hashed.
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its stored hash.

    Args:
        plain_password (str): Raw password.
        hashed_password (str): Hashed password.

    Returns:
        bool: Returns True if password is correct. False, otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a JWT access token for the given subject.

    Args:
        subject (str): Identifier of the token subject.

    Returns:
        encoded_jwt (str): Encoded JWT access token.
    """
    issued_at = datetime.now(UTC)
    expire = issued_at + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": issued_at,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt
