from pwdlib import PasswordHash

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
