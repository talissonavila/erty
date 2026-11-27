import secrets
import string
from datetime import UTC, datetime
from typing import TypedDict

from app.core.constants import DEFAULT_URL_LIMIT_VALUE, DEFAULT_URL_OFFSET_VALUE
from app.models.url import URL
from app.repositories.url_repository import URLRepository, URLShortCodeConflictError


class URLCodeGenerationError(Exception):
    """Raised when a unique short code cannot be generated."""


class URLNotFoundError(Exception):
    """Raised when a URL does not exist or does not belong to the user."""

    def __init__(self, message: str = "URL not found.") -> None:
        """Initialize the exception with an error message.
        Args:
            message (str): Description of the URL error.
            Defaltus to "URL not found."
        """
        self.message = message
        super().__init__(message)


class URLUpdateData(TypedDict, total=False):
    """Fields that can be updated on a URL."""

    original_url: str
    expires_at: datetime | None
    is_active: bool


class URLService:
    """Handle business logic for shortened URLs."""

    CODE_LENGTH = 8
    MAX_ATTEMPTS = 5
    CODE_CHARACTERS = string.ascii_letters + string.digits

    def __init__(self, repository: URLRepository) -> None:
        """Initialize the service with a URL repository.

        Args:
            repository (URLRepository): Handle database operations for shortened URLs.
        """
        self.repository = repository

    def _generate_short_code(self) -> str:
        """Returns a cryptographically secure random short code."""
        return "".join(
            secrets.choice(self.CODE_CHARACTERS) for _ in range(self.CODE_LENGTH)
        )

    def create_url(self, original_url: str, user_id: int) -> URL:
        """Create and persist a shortened URL.

        Args:
            original_url (str): Original URL to be shortened.
            user_id (int): User that is creating the shortened URL.

        Returns:
            The persisted URL model.

        Raises:
            URLCodeGenerationError: Raised when can't generate short code.
            URLShortCodeConflictError: If a short code violates its unique constraints.
        """
        for _ in range(self.MAX_ATTEMPTS):
            short_code = self._generate_short_code()

            existing_url = self.repository.get_by_short_code(short_code)

            if existing_url is not None:
                continue

            url = URL(
                original_url=original_url,
                short_code=short_code,
                user_id=user_id,
            )
            try:
                return self.repository.create(url)
            except URLShortCodeConflictError:
                continue
        raise URLCodeGenerationError("Unable to generate a unique short code.")

    def get_original_url(self, short_code: str) -> str | None:
        """Retrieve the original URL if the shortened URL is valid.

        Args:
            short_code (str): Short code used to identify the URL.

        Returns:
            str | None: Original URL if it exists, is active and has not expired.
            None, otherwise.
        """
        url = self.repository.get_by_short_code(short_code)

        if url is None or not url.is_active:
            return None

        if url.expires_at is not None and url.expires_at <= datetime.now(UTC):
            return None

        return url.original_url

    def list_urls(
        self,
        user_id: int,
        limit: int = DEFAULT_URL_LIMIT_VALUE,
        offset: int = DEFAULT_URL_OFFSET_VALUE,
    ) -> list[URL]:
        """List URLs belonging to a user.

        Args:
            user_id (int): ID of the authenticated user.
            limit (int): Maximum number of URLs to retrieve. Defaults to 20.
            offset (int): Number of URLs to skip. Defaults to 0.

        Returns:
            list[URL]: List of URLs belonging to the specified user.
        """
        return self.repository.get_all_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def get_url(
        self,
        url_id: int,
        user_id: int,
    ) -> URL:
        """Retrieve a URL only if it belongs to the specified user.

        Args:
            url_id (int): ID of the URL.
            user_id (int): ID of the authenticated user.

        Returns:
            URL: The requested URL.

        Raises:
            URLNotFoundError: Raised when the URL does not exist or belongs to another
            user.
        """
        url = self.repository.get_by_id_and_user_id(
            url_id=url_id,
            user_id=user_id,
        )
        if url is None:
            raise URLNotFoundError()
        return url

    def update_url(
        self,
        url_id: int,
        user_id: int,
        updates: URLUpdateData,
    ) -> URL:
        """Update a URL belonging to the specified user.

        Args:
            url_id (int): ID of the URL.
            user_id (int): ID of the authenticated user.
            updates (URLUpdateData): Fields to update.

        Returns:
            URL: Updated URL.

        Raises:
            URLNotFoundError: Raised when the URL does not exist or belongs to another
            user.
        """
        url = self.get_url(url_id=url_id, user_id=user_id)

        for field, value in updates.items():
            setattr(url, field, value)

        return self.repository.update(url)

    def delete_url(self, url_id: int, user_id: int) -> None:
        """Delete a URL belonging to the specified user.

        Args:
            url_id (int): ID of the URL.
            user_id (int): ID of the authenticated user.

        Raises:
            URLNotFoundError: Raised when the URL does not exist or belongs to another
            user.
        """
        url = self.get_url(url_id=url_id, user_id=user_id)
        self.repository.delete(url=url)
