from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.url import URL


class URLShortCodeConflictError(Exception):
    """Raised when a short code violates its unique constraints."""


class URLRepository:
    """Handle database operations for shortened URLs."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): database session.
        """
        self.session = session

    def create(self, url: URL) -> URL:
        """Add a URL within a savepoint in the current transaction.

        Args:
            url (URL): URL to be shortened.

        Returns:
            url (URL): URL to be shortened.

        Raises:
            URLShortCodeConflictError: Raised when short code already exists.
            IntegrityError: Raised when another database integrity constraint fails.
        """
        try:
            with self.session.begin_nested():
                self.session.add(url)
                self.session.flush()
        except IntegrityError as error:
            if (
                isinstance(error.orig, UniqueViolation)
                and error.orig.diag.constraint_name == "ix_urls_short_code"
            ):
                raise URLShortCodeConflictError(
                    "The short code already exists."
                ) from error
            raise
        return url

    def get_by_short_code(self, short_code: str) -> URL | None:
        """Retrieve a URL using its short code.

        Args:
            short_code (str): The short_code to search the long URL on database.

        Returns:
            The URL object case its registered in database. None, otherwise.
        """
        statement = select(URL).where(URL.short_code == short_code)

        return self.session.scalar(statement)
