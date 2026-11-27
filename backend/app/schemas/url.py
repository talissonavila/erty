from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator


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


class URLUpdate(BaseModel):
    """Schema for updating an existing shortened URL."""

    original_url: HttpUrl | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "URLUpdate":
        """Ensure at least one valid field was provided for updating."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        if "original_url" in self.model_fields_set and self.original_url is None:
            raise ValueError("original_url cannot be null.")

        if "is_active" in self.model_fields_set and self.is_active is None:
            raise ValueError("is_active cannot be null.")

        return self


class URLListResponse(BaseModel):
    """Schema for returning a paginated list of URLs."""

    urls: list[URLResponse]
    limit: int
    offset: int
