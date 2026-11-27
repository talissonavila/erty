from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.constants import DEFAULT_URL_LIMIT_VALUE, DEFAULT_URL_OFFSET_VALUE
from app.db.session import get_db
from app.models.user import User
from app.repositories.url_repository import URLRepository
from app.schemas.url import (
    URLCreate,
    URLListResponse,
    URLResponse,
    URLUpdate,
)
from app.services.url_service import (
    URLCodeGenerationError,
    URLNotFoundError,
    URLService,
    URLUpdateData,
)

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
    payload: URLCreate,
    service: Annotated[URLService, Depends(get_url_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> URLResponse:
    """Create a shortened URL.

    Args:
        payload (URLCreate): Schema for creating a shortened URL.
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.
        current_user (Annotated[User, Depends(get_current_user)]): Authenticated user
        who owns the shortened URL.

    Returns:
        URLResponse: Schema for returning a shortened URL.

    Raises:
        HTTPException: Raised when a unique short code cannot be generated.
    """
    try:
        url = service.create_url(
            original_url=str(payload.original_url),
            user_id=current_user.id,
        )
        return URLResponse.model_validate(url)
    except URLCodeGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a unique short code.",
        ) from error


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(
    url_id: Annotated[int, Path(gt=0)],
    service: Annotated[URLService, Depends(get_url_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a URL that was shortened.

    Args:
        url_id (Annotated[int, Path(gt=0)]): ID of URL.
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.
        current_user (Annotated[User, Depends(get_current_user)]): Authenticated user
        who owns the shortened URL.

    Raises:
        HTTPException: Raised when the URL does not exist or does not belong to
        the authenticated user.
    """
    try:
        service.delete_url(
            url_id=url_id,
            user_id=current_user.id,
        )
    except URLNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message,
        ) from error


@router.get(
    "",
    response_model=URLListResponse,
    status_code=status.HTTP_200_OK,
)
def list_urls(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[URLService, Depends(get_url_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = DEFAULT_URL_LIMIT_VALUE,
    offset: Annotated[int, Query(ge=0)] = DEFAULT_URL_OFFSET_VALUE,
) -> URLListResponse:
    """List the URLs created by the authenticated user

    Args:
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.
        current_user (Annotated[User, Depends(get_current_user)]): Authenticated user
        who owns the shortened URL.
        limit (Annotated[int, Query(ge=1, le=100)]): Maximum number of URLs to return
        per request (1-100). Defaults to DEFAULT_URL_LIMIT_VALUE.
        offset (Annotated[int, Query(ge=0)]): Number of URLs to skip before retrieving
        the results. Defaults to DEFAULT_URL_OFFSET_VALUE.

    Returns:
        URLListResponse: Paginated list of the user's shortened URLs, including
        the applied limit and offset.
    """
    urls = service.list_urls(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return URLListResponse(
        urls=[URLResponse.model_validate(url) for url in urls],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{url_id}",
    response_model=URLResponse,
    status_code=status.HTTP_200_OK,
)
def get_url(
    url_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[URLService, Depends(get_url_service)],
) -> URLResponse:
    """Retrieve a shortened URL owned by the authenticated user.

    Args:
        url_id (Annotated[int, Path(gt=0)]): ID of the URL.
        current_user (Annotated[User, Depends(get_current_user)]): Authenticated
        user requesting the URL.
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.

    Returns:
        URLResponse: Requested shortened URL.

    Raises:
        HTTPException: Raised when the URL does not exist or does not belong to
        the authenticated user.
    """
    try:
        url = service.get_url(
            user_id=current_user.id,
            url_id=url_id,
        )
        return URLResponse.model_validate(url)
    except URLNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message,
        ) from error


@router.patch(
    "/{url_id}",
    response_model=URLResponse,
    status_code=status.HTTP_200_OK,
)
def update_url(
    payload: URLUpdate,
    url_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[URLService, Depends(get_url_service)],
) -> URLResponse:
    """Update an existing shortened URL owned by the authenticated user.

    Args:
        payload (URLUpdate): Request data containing the URL fields to be updated.
        url_id (Annotated[int, Path(gt=0)]): ID of the URL.
        current_user (Annotated[User, Depends(get_current_user)]): Authenticated
        user requesting the update.
        service (Annotated[URLService, Depends(get_url_service)]): Handle business
        logic for shortened URLs.

    Returns:
        URLResponse: Updated shortened URL.

    Raises:
        HTTPException: Raised when the URL does not exist or does not belong
        to the authenticated user.
    """
    try:
        updates = cast(
            URLUpdateData,
            payload.model_dump(exclude_unset=True),
        )

        if "original_url" in updates:
            updates["original_url"] = str(updates["original_url"])

        url = service.update_url(
            url_id=url_id,
            user_id=current_user.id,
            updates=updates,
        )

        return URLResponse.model_validate(url)
    except URLNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=error.message
        ) from error
