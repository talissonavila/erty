import secrets
import string
from datetime import UTC, datetime

from app.models.url import URL
from app.repositories.url_repository import URLRepository, URLShortCodeConflictError


class URLCodeGenerationError(Exception):
    """Raised when a unique short code cannot be generated."""


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

    def create_url(self, original_url: str) -> URL:
        """Create and persist a shortened URL.

        Args:
            original_url (str): Original URL to be shortened.

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
