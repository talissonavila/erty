import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.url import URL


def test_url_can_be_persisted(db_session: Session) -> None:
    """Ensure a URL can be persisted and retrieved from the database."""
    input = {"original_url": "https://www.python.org/", "short_code": "python123"}
    url = URL(
        original_url=input["original_url"],
        short_code=input["short_code"],
    )

    db_session.add(url)
    db_session.flush()

    assert url.id is not None

    persisted_url = db_session.execute(
        select(URL).where(URL.short_code == input["short_code"])
    ).scalar_one()

    assert persisted_url.original_url == input["original_url"]
    assert persisted_url.short_code == input["short_code"]


def test_short_code_must_be_unique(db_session: Session) -> None:
    """Ensure duplicate short codes are rejected by the database."""
    input1 = {"original_url": "https://www.python.org/", "short_code": "erty123"}
    input2 = {"original_url": "https://www.djangoproject.com/", "short_code": "erty123"}

    first_url = URL(
        original_url=input1["original_url"],
        short_code=input1["short_code"],
    )

    second_url = URL(
        original_url=input2["original_url"],
        short_code=input2["short_code"],
    )

    db_session.add(first_url)
    db_session.flush()

    db_session.add(second_url)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_applies_url_default_values(db_session: Session) -> None:
    """Ensure PostgreSQL applies default values when inserting a URL."""
    result = db_session.execute(
        text(
            """
            INSERT INTO urls (original_url, short_code)
            VALUES (:original_url, :short_code)
            RETURNING created_at, is_active
            """
        ),
        {
            "original_url": "https://www.python.org/",
            "short_code": "defaults123",
        },
    ).one()

    assert result.created_at is not None
    assert result.is_active is True
