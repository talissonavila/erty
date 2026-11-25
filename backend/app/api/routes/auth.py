from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse
from app.services.auth_service import AuthService, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(session: Annotated[Session, Depends(get_db)]) -> AuthService:
    """Provide a AuthService instance with its repository dependency.

    Args:
        session (Annotated[Session, Depends(get_db)]): database session.

    Returns:
        AuthService: Configured AuthService instance.
    """
    repository = UserRepository(session)
    return AuthService(repository)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Authenticate user and return an access token.

    Args:
        form_data (Annotated[OAuth2PasswordRequestForm, Depends()]): User email
        and password.
        service (Annotated[AuthService, Depends(get_auth_service)]): Handle business
        logic for users.

    Returns:
        AuthResponse: Generated access token.

    Raises:
        HTTPException: Raised when InvalidCredentialsError is raised.
    """
    try:
        user = service.authenticate(
            email=form_data.username,
            password=form_data.password,
        )
        return AuthResponse(access_token=user)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
        ) from error
