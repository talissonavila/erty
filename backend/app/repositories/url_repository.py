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

    def get_all_by_user_id(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[URL]:
        """Retrieve URLs beloging to a user with pagination.

        Args:
            user_id (int): ID of the user whose URLs should be retrieved.
            limit (int): Maximum number of URLs to retrieve.
            offset (int): Number of URLs to skip before retrieving results.

        Returns:
            list[URL]: List of URLs belonging to the specified user.
        """
        statement = (
            select(URL)
            .where(URL.user_id == user_id)
            .order_by(URL.created_at.desc(), URL.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())

    def get_by_id_and_user_id(
        self,
        url_id: int,
        user_id: int,
    ) -> URL | None:
        """Retrieve a URL only if it belongs to the specific user.

        Args:
            url_id (int): ID of the URL to retrieve.
            user_id (int): ID of the user who must own the URL.

        Returns:
            URL | None: The URL if it exists and belongs to the specified user.
            None, otherwise.
        """
        statement = select(URL).where(
            URL.id == url_id,
            URL.user_id == user_id,
        )
        return self.session.scalar(statement)

    def delete(self, url: URL) -> None:
        """Delete a URL.

        Args:
            url (URL): URL instance to be deleted.
        """
        self.session.delete(url)
        self.session.flush()

    def update(self, url: URL) -> URL:
        """Persist changes to an existing URL.

        Args:
            url (URL): URL instance containing the updated values.

        Retuens:
            URL: Updated URL instance
        """
        self.session.add(url)
        self.session.flush()
        return url
