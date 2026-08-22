
from fastapi import FastAPI
from app.api.router import router
from app.core.settings import settings


APP_DESCRIPTION = "API for ERTY project"


app =  FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=APP_DESCRIPTION
)

app.include_router(router)
