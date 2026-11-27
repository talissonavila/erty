from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.url import URL
from app.schemas.url import (
    URLCreate,
    URLListResponse,
    URLResponse,
    URLUpdate,
)


@pytest.mark.parametrize(
    "original_url",
    [
        "https://example.com",
        "http://example.com",
        "https://www.example.com/path?query=value",
    ],
)
def test_url_create_accepts_valid_urls(original_url: str) -> None:
    """Should accept valid HTTP and HTTPS URLs."""
    schema = URLCreate(original_url=original_url)

    assert str(schema.original_url).startswith(original_url.split("://")[0])


@pytest.mark.parametrize(
    "original_url",
    [
        "not-a-url",
        "ftp://example.com",
        "example.com",
        "",
    ],
)
def test_url_create_rejects_invalid_urls(original_url: str) -> None:
    """Should reject invalid URLs."""
    with pytest.raises(ValidationError):
        URLCreate(original_url=original_url)


def test_url_create_requires_original_url() -> None:
    """Should require the original_url field."""
    with pytest.raises(ValidationError):
        URLCreate.model_validate({})


def test_url_response_accepts_valid_data() -> None:
    """Should accept valid URL response data."""
    created_at = datetime.now(UTC)

    schema = URLResponse(
        id=1,
        original_url="https://example.com",
        short_code="abc123",
        created_at=created_at,
        expires_at=None,
        is_active=True,
    )

    assert schema.id == 1
    assert schema.original_url == "https://example.com"
    assert schema.short_code == "abc123"
    assert schema.created_at == created_at
    assert schema.expires_at is None
    assert schema.is_active is True


def test_url_response_from_sqlalchemy_model() -> None:
    """Should create a response schema from a SQLAlchemy model."""
    created_at = datetime.now(UTC)

    url = URL(
        id=1,
        original_url="https://example.com",
        short_code="abc123",
        created_at=created_at,
        expires_at=None,
        is_active=True,
    )

    schema = URLResponse.model_validate(url)

    assert schema.id == url.id
    assert schema.original_url == url.original_url
    assert schema.short_code == url.short_code
    assert schema.created_at == url.created_at
    assert schema.expires_at == url.expires_at
    assert schema.is_active == url.is_active


def test_url_response_requires_mandatory_fields() -> None:
    """Should reject response data with missing required fields."""
    with pytest.raises(ValidationError):
        URLResponse.model_validate(
            {
                "id": 1,
                "original_url": "https://example.com",
                "short_code": "abc123",
                "created_at": datetime.now(UTC),
            }
        )


def test_url_update_accepts_partial_data() -> None:
    """Tests if URLUpdate accept a partial URL update."""
    schema = URLUpdate(original_url="https://example.com")

    assert str(schema.original_url) == "https://example.com/"
    assert schema.model_fields_set == {"original_url"}


def test_url_update_accepts_multiple_fields() -> None:
    """Tests if URLUpdate accept multiple fields for updating."""
    schema = URLUpdate(
        original_url="https://example.com",
        is_active=False,
    )

    assert str(schema.original_url) == "https://example.com/"
    assert schema.is_active is False


def test_url_update_accepts_null_expiration() -> None:
    """Tests if URLUpdate allow removing the URL expiration date."""
    schema = URLUpdate(expires_at=None)

    assert schema.expires_at is None
    assert schema.model_fields_set == {"expires_at"}


def test_url_update_rejects_empty_payload() -> None:
    """Tests if URLUpdate reject an update without provided fields."""
    with pytest.raises(ValidationError):
        URLUpdate.model_validate({})


@pytest.mark.parametrize(
    "payload",
    [
        {"original_url": None},
        {"is_active": None},
    ],
)
def test_url_update_rejects_invalid_null_values(
    payload: dict[str, object],
) -> None:
    """Tests if URLUpdate reject null values for fields that cannot be null."""
    with pytest.raises(ValidationError):
        URLUpdate.model_validate(payload)


def test_url_update_preserves_unset_fields() -> None:
    """Tests if URLUpdate disting omitted fields from explicitly provided null
    values."""
    schema = URLUpdate(expires_at=None)

    updates = schema.model_dump(exclude_unset=True)

    assert updates == {"expires_at": None}


def test_url_list_response_accepts_valid_data() -> None:
    """Tests if URLListResponse accept a paginated list of URLs."""
    created_at = datetime.now(UTC)

    url = URLResponse(
        id=1,
        original_url="https://example.com",
        short_code="abc123",
        created_at=created_at,
        expires_at=None,
        is_active=True,
    )

    schema = URLListResponse(
        urls=[url],
        limit=20,
        offset=0,
    )

    assert len(schema.urls) == 1
    assert schema.urls[0].id == 1
    assert schema.limit == 20
    assert schema.offset == 0


def test_url_list_response_accepts_empty_list() -> None:
    """Tests if URLListResponse accept an empty list of URLs."""
    schema = URLListResponse(
        urls=[],
        limit=20,
        offset=0,
    )

    assert schema.urls == []
