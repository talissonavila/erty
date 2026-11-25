from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import create_autospec

import pytest

from app.models.url import URL
from app.models.user import User
from app.repositories.url_repository import URLRepository, URLShortCodeConflictError
from app.services.url_service import URLCodeGenerationError, URLService

ORIGINAL_URL = "https://www.python.org/"
SHORT_CODE = "abc12345"
NEW_SHORT_CODE = "def67890"


@pytest.fixture
def repository() -> URLRepository:
    """Returns a mocked URLRepository instance."""
    return cast(
        URLRepository,
        create_autospec(URLRepository, instance=True, spec_set=True),
    )


@pytest.fixture
def service(repository: URLRepository) -> URLService:
    """Returns a URLService with a mocked repository.

    Args:
        repository (URLRepository): The mocked URLRepository instance.
    """
    return URLService(repository)


@pytest.fixture
def url_factory() -> Callable[..., URL]:
    """Returns URL instances with customizable attributes."""

    def factory(
        original_url: str = ORIGINAL_URL,
        short_code: str = SHORT_CODE,
        is_active: bool = True,
        expires_at: datetime | None = None,
    ) -> URL:
        """Returns a valid URL.

        Args:
            original_url (str): A valid URL address. Defaults to ORIGINAL_URL const.
            short_code (str): A valid short code. Defaults to SHORT_CODE const.
            is_active (bool): A flag if shortened URL is valid or not. Defaults to True.
            expires_at (datetime | None): A date and time value to expires the
            shortened URL. Defaults to None.
        """
        return URL(
            original_url=original_url,
            short_code=short_code,
            is_active=is_active,
            expires_at=expires_at,
        )

    return factory


@pytest.fixture
def url(url_factory: Callable[..., URL]) -> URL:
    """Returns a default active URL without expiration.

    Args:
       url_factory (Callable[..., URL]):
    """
    return url_factory()


@pytest.fixture
def expired_url(url_factory: Callable[..., URL]) -> URL:
    """Returns an expired URL.

    Args:
       url_factory (Callable[..., URL]): Factory used to create URL instances.
    """
    return url_factory(
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )


@pytest.fixture
def future_expiration_url(url_factory: Callable[..., URL]) -> URL:
    """Returns a URL with a future expiration date.

    Args:
       url_factory (Callable[..., URL]): Factory used to create URL instances.
    """
    return url_factory(
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )


@pytest.fixture
def short_code_generator(
    monkeypatch: pytest.MonkeyPatch,
    service: URLService,
) -> Callable[[list[str]], None]:
    """Allows tests to control generated short codes.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture used to replace the short
        code generator.
        service (URLService): The URLService instance whose code generator is replaced.

    Returns:
        configure (Callable[[list[str]], None]):  Function that configures the short
        codes to be generated.
    """

    def configure(codes: list[str]) -> None:
        """Function that configures the short codes to be generated.

        Args:
            codes (list[str]): Short codes to be returned by the generator.
        """
        generated_codes = iter(codes)

        monkeypatch.setattr(
            service,
            "_generate_short_code",
            lambda: next(generated_codes),
        )

    return configure


def test_generate_short_code_returns_valid_code(service: URLService) -> None:
    """Tests whether a valid short code is generated.

    Args:
        service (URLService): The URLService instance.
    """
    short_code = service._generate_short_code()

    assert len(short_code) == URLService.CODE_LENGTH
    assert all(char in URLService.CODE_CHARACTERS for char in short_code)


def test_create_url_persists_url(
    service: URLService,
    repository: URLRepository,
    short_code_generator: short_code_generator,
    user: User,
) -> None:
    """Tests whether a unique short code is generated and the URL is persisted.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        short_code_generator (short_code_generator): Function used to configure
        the generated short codes.
        user (User): A user stored in test database.
    """
    short_code_generator([SHORT_CODE])
    repository.get_by_short_code.return_value = None

    expected_url = URL(
        original_url="https://example.com",
        short_code=SHORT_CODE,
        user_id=user.id,
    )
    repository.create.return_value = expected_url

    result = service.create_url("https://example.com", user.id)

    assert result is expected_url
    repository.get_by_short_code.assert_called_once_with(SHORT_CODE)
    repository.create.assert_called_once()

    persisted_url = cast(URL, repository.create.call_args.args[0])

    assert persisted_url.original_url == "https://example.com"
    assert persisted_url.short_code == SHORT_CODE


def test_create_url_retries_when_code_already_exists(
    service: URLService,
    repository: URLRepository,
    url_factory: Callable[..., URL],
    short_code_generator: Callable[[list[str]], None],
    user: User,
) -> None:
    """Tests whether a new short code is generated when a collision occurs.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        url_factory (Callable[..., URL]):
        short_code_generator (Callable[[list[str]], None]): Function used to configure
        the generated short codes.
        user (User): A user stored in test database.
    """
    existing_url = url_factory(short_code="taken123")

    repository.get_by_short_code.side_effect = [existing_url, None]
    short_code_generator(["taken123", NEW_SHORT_CODE])

    expected_url = url_factory(
        original_url="https://example.com",
        short_code=NEW_SHORT_CODE,
    )
    repository.create.return_value = expected_url

    result = service.create_url("https://example.com", user.id)

    assert result is expected_url
    assert repository.get_by_short_code.call_count == 2
    repository.create.assert_called_once()

    persisted_url = cast(URL, repository.create.call_args.args[0])

    assert persisted_url.short_code == NEW_SHORT_CODE


def test_create_url_raises_error_after_max_attempts(
    service: URLService,
    repository: URLRepository,
    url_factory: Callable[..., URL],
    short_code_generator: Callable[[list[str]], None],
    user: User,
) -> None:
    """Tests whether an error is raised after all generation attempts fail.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        url_factory (Callable[..., URL]):
        short_code_generator (Callable[[list[str]], None]): Function used to configure
        the generated short codes.
        user (User): A user stored in test database.
    """
    existing_url = url_factory(short_code="taken123")

    repository.get_by_short_code.return_value = existing_url
    short_code_generator(["taken123"] * URLService.MAX_ATTEMPTS)

    with pytest.raises(URLCodeGenerationError):
        service.create_url("https://example.com", user.id)

    assert repository.get_by_short_code.call_count == URLService.MAX_ATTEMPTS
    repository.create.assert_not_called()


def test_create_url_retries_after_concurrent_collision(
    service: URLService,
    repository: URLRepository,
    short_code_generator: Callable[[list[str]], None],
    user: User,
) -> None:
    """Should retry when another request inserts the same code.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        short_code_generator (Callable[[list[str]], None]): Function used to configure
        the generated short codes.
        user (User): A user stored in test database.
    """
    short_code_generator([SHORT_CODE, NEW_SHORT_CODE])
    repository.get_by_short_code.return_value = None

    expected_url = URL(
        original_url="https://example.com",
        short_code=NEW_SHORT_CODE,
        user_id=user.id,
    )

    repository.create.side_effect = [
        URLShortCodeConflictError("The short code already exists."),
        expected_url,
    ]

    result = service.create_url("https://example.com", user.id)

    assert result is expected_url
    assert repository.get_by_short_code.call_count == 2
    assert repository.create.call_count == 2


def test_get_original_url_returns_url_when_active_and_not_expired(
    repository: URLRepository,
    service: URLService,
    url: URL,
) -> None:
    """Returns the original URL when it is active and has no expiration date.

    Args:
        repository (URLRepository): The mocked URLRepository instance.
        service (URLService): The URLService instance.
        url (URL): The active URL instance without an expiration date.
    """
    repository.get_by_short_code.return_value = url

    result = service.get_original_url(SHORT_CODE)

    assert result == ORIGINAL_URL
    repository.get_by_short_code.assert_called_once_with(SHORT_CODE)


def test_get_original_url_returns_none_when_url_does_not_exist(
    service: URLService,
    repository: URLRepository,
) -> None:
    """Returns None when no URL matches the provided short code.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
    """
    repository.get_by_short_code.return_value = None

    result = service.get_original_url("missing123")

    assert result is None
    repository.get_by_short_code.assert_called_once_with("missing123")


def test_get_original_url_returns_none_when_url_is_inactive(
    repository: URLRepository,
    service: URLService,
    url_factory: Callable[..., URL],
) -> None:
    """Returns None when the URL exists but is inactive.

    Args:
        repository (URLRepository): The mocked URLRepository instance.
        service (URLService): The URLService instance.
        url_factory (Callable[..., URL]): Factory used to create URL instances.
    """
    inactive_url = url_factory(is_active=False)
    repository.get_by_short_code.return_value = inactive_url

    result = service.get_original_url(SHORT_CODE)

    assert result is None
    repository.get_by_short_code.assert_called_once_with(SHORT_CODE)


def test_get_original_url_returns_none_when_url_is_expired(
    repository: URLRepository,
    service: URLService,
    expired_url: URL,
) -> None:
    """Returns None when the URL has already expired.

    Args:
        repository (URLRepository): The mocked URLRepository instance.
        service (URLService): The URLService instance.
        expired_url (URL): Fixture that returns an expired URL.
    """
    repository.get_by_short_code.return_value = expired_url

    result = service.get_original_url(SHORT_CODE)

    assert result is None
    repository.get_by_short_code.assert_called_once_with(SHORT_CODE)


def test_get_original_url_returns_url_when_expiration_is_in_future(
    repository: URLRepository, service: URLService, future_expiration_url: URL
) -> None:
    """Returns the original URL when its expiration date is in the future.

    Args:
        repository (URLRepository): The mocked URLRepository instance.
        serivce (URLService): The URLService instance.
        future_expiration_url (URL): Fixture that returns a URL with a future
        expiration date.
    """
    repository.get_by_short_code.return_value = future_expiration_url

    result = service.get_original_url(SHORT_CODE)

    assert result == ORIGINAL_URL
    repository.get_by_short_code.assert_called_once_with(SHORT_CODE)
