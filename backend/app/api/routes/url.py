from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.url_repository import URLRepository
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import URLCodeGenerationError, URLService

router = APIRouter(prefix="/urls", tags=["urls"])


def get_url_service(session: Annotated[Session, Depends(get_db)]) -> URLService:
    """Provide a URLService instance with its repository dependency.

    Args:
        session (Annotated[Session, Depends(get_db)]): database session.

    Returns:
        URLService: Configured URLService instance.
    """
    repository = URLRepository(session)
    return URLService(repository)


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_url(
    payload: URLCreate, service: Annotated[URLService, Depends(get_url_service)]
) -> URLResponse:
    """Create a shortened URL.

    Args:
        payload (URLCreate): Schema for creating a shortened URL.
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.

    Returns:
        URLResponse: Schema for returning a shortened URL.

    Raises:
        URLCodeGenerationError: Raised when a unique short code cannot be generated.
    """
    try:
        url = service.create_url(str(payload.original_url))
        return URLResponse.model_validate(url)
    except URLCodeGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a unique short code.",
        ) from error
