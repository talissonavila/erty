from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.routes.url import get_url_service
from app.services.url_service import URLService

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
def redirect_url(
    short_code: str, service: Annotated[URLService, Depends(get_url_service)]
) -> RedirectResponse:
    """Redirect to the original URL associated with a short code.

    Args:
        short_code (str): Short code identifying the original URL.
        service (Annotated[URLService, Depends(get_url_service)]): URL businesss logic.

    Returns:
        RedirectResponse: HTTP redirect to the original URL.

    Raises:
        HTTPException: Raised if the shortened URL does not exist or is invalid.
    """
    original_url = service.get_original_url(short_code)

    if original_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found."
        )

    return RedirectResponse(
        url=original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
