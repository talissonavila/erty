from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import InvalidCredentialsError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Get current user based on JWT token.

    Args:
        token (Annotated[str, Depends(oauth2_scheme)]): JWT token.

    Returns:
        user (User): When user is returned with success.
        session (Annotated[Session, Depends(get_db)]): Database session.

    Raises:
        HTTPException: Raised when get_current_user has an error during process.
    """
    try:
        payload = decode_access_token(token)
        if not payload:
            raise InvalidCredentialsError()

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise InvalidCredentialsError()

        try:
            user_id = int(subject)
        except ValueError:
            raise InvalidCredentialsError() from None

        repository = UserRepository(session)
        user = repository.get_by_id(user_id)

        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        return user
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
