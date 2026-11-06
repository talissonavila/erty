from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


def test_session_can_execute_query(db_session: Session) -> None:
    """Ensure a database session can execute SQL queries."""
    result = db_session.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_get_db_returns_session(db_dependency: Session) -> None:
    """Ensure get_db provides a valid databae session."""
    assert isinstance(db_dependency, Session)

    result = db_dependency.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_get_db_closes_session(monkeypatch) -> None:
    """Ensure get_db closes the session after generator completion."""
    closed = False
    original_close = Session.close

    def track_close(self: Session) -> None:
        nonlocal closed
        closed = True
        original_close(self)

    monkeypatch.setattr(Session, "close", track_close)

    generator = get_db()
    next(generator)
    generator.close()

    assert closed
