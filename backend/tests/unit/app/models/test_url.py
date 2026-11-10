from app.db.base import Base
from app.models.url import URL


def test_url_model_is_registered() -> None:
    """Ensure URL model is registered in SQLAlchemy metadata."""
    assert URL.__tablename__ == "urls"
    assert "urls" in Base.metadata.tables


def test_url_model_constraints() -> None:
    """Ensure URL model columns have expected constraints."""
    columns = URL.__table__.columns

    assert columns["short_code"].unique is True
    assert columns["short_code"].nullable is False
    assert columns["original_url"].nullable is False
    assert columns["expires_at"].nullable is True


def test_url_model_defaults() -> None:
    """Ensure URL model has expected default values."""
    columns = URL.__table__.columns

    assert columns["is_active"].default.arg is True
    assert columns["is_active"].server_default is not None
    assert columns["created_at"].server_default is not None
