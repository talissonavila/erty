from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.db.session import get_db


def test_get_db_rollbacks_transaction_when_exception_occurs() -> None:
    """Rollback the transaction when an exception occurs."""

    error = RuntimeError("Database operation failed")
    session = MagicMock(spec=Session)

    with patch("app.db.session.SessionLocal") as session_factory:
        session_factory.return_value.__enter__.return_value = session

        with pytest.raises(RuntimeError, match="Database operation failed"):
            with contextmanager(get_db)() as db_session:
                assert db_session is session
                raise error

    session.commit.assert_not_called()
    session.rollback.assert_called_once()


def test_get_db_commits_transaction_when_no_exception_occurs() -> None:
    """Commit the transaction when no exception occurs."""

    session = MagicMock(spec=Session)

    with patch("app.db.session.SessionLocal") as session_factory:
        session_factory.return_value.__enter__.return_value = session

        with contextmanager(get_db)() as db_session:
            assert db_session is session

    session.commit.assert_called_once()
    session.rollback.assert_not_called()
