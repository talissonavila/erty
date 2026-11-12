from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class URLCreate(BaseModel):
    """Schema for creating a shortened URL."""

    original_url: HttpUrl


class URLResponse(BaseModel):
    """Schema for returning a shortened URL."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: datetime | None
    is_active: bool
