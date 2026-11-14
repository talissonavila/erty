from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.url import router as url_router

router = APIRouter()

router.include_router(health_router)
router.include_router(url_router)
