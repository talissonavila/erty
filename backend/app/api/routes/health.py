from fastapi import APIRouter

from app.core.settings import settings
from app.schemas.health_schema import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health_check():
    """Return the current health status of the service."""
    return HealthResponse(
        status="healthy", service="erty-backend", version=settings.app_version
    )
