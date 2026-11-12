from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.url import URL


class URLRepository:
    """Handle database operations for shortened URLs."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): database session.
        """
        self.session = session

    def create(self, url: URL) -> URL:
        """Add a URL to the current database transaction.

        Args:
            url (URL): URL to be shortened.

        Returns:
            url (URL): URL to be shortened.
        """
        self.session.add(url)
        self.session.flush()

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
