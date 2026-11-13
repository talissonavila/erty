from typing import cast
from unittest.mock import create_autospec

import pytest

from app.models.url import URL
from app.repositories.url_repository import URLRepository, URLShortCodeConflictError
from app.services.url_service import URLCodeGenerationError, URLService


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests whether a unique short code is generated and the URL is persisted.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.
    """
    monkeypatch.setattr(
        service,
        "_generate_short_code",
        lambda: "abc12345",
    )
    repository.get_by_short_code.return_value = None

    expected_url = URL(original_url="https://example.com", short_code="abc12345")
    repository.create.return_value = expected_url

    result = service.create_url("https://example.com")

    assert result is expected_url
    repository.get_by_short_code.assert_called_once_with("abc12345")
    repository.create.assert_called_once()

    persisted_url = cast(URL, repository.create.call_args.args[0])

    assert persisted_url.original_url == "https://example.com"
    assert persisted_url.short_code == "abc12345"


def test_create_url_retries_when_code_already_exists(
    service: URLService,
    repository: URLRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests whether a new short code is generated when a collision occurs.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.
    """
    existing_url = URL(original_url="https://existing.com", short_code="taken123")

    repository.get_by_short_code.side_effect = [existing_url, None]

    generated_codes = iter(["taken123", "newcode1"])

    monkeypatch.setattr(service, "_generate_short_code", lambda: next(generated_codes))

    expected_url = URL(original_url="https://example.com", short_code="newcode1")
    repository.create.return_value = expected_url

    result = service.create_url("https://example.com")

    assert result is expected_url
    assert repository.get_by_short_code.call_count == 2
    repository.create.assert_called_once()

    persisted_url = cast(URL, repository.create.call_args.args[0])

    assert persisted_url.short_code == "newcode1"


def test_create_url_raises_error_after_max_attempts(
    service: URLService,
    repository: URLRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests whether an error is raised after all generation attempts fail.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.
    """
    existing_url = URL(
        original_url="https://existing.com",
        short_code="taken123",
    )

    repository.get_by_short_code.return_value = existing_url

    monkeypatch.setattr(
        service,
        "_generate_short_code",
        lambda: "taken123",
    )

    with pytest.raises(URLCodeGenerationError):
        service.create_url("https://example.com")

    assert repository.get_by_short_code.call_count == URLService.MAX_ATTEMPTS
    repository.create.assert_not_called()


def test_create_url_retries_after_concurrent_collision(
    service: URLService,
    repository: URLRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should retry when another request inserts the same code.

    Args:
        service (URLService): The URLService instance.
        repository (URLRepository): The mocked URLRepository instance.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.
    """
    generated_codes = iter(["abc12345", "def67890"])

    monkeypatch.setattr(
        service,
        "_generate_short_code",
        lambda: next(generated_codes),
    )

    repository.get_by_short_code.return_value = None

    expected_url = URL(
        original_url="http://example.com",
        short_code="def67890",
    )

    repository.create.side_effect = [
        URLShortCodeConflictError("The short code already exists."),
        expected_url,
    ]

    result = service.create_url("https://example.com")

    assert result is expected_url
    assert repository.get_by_short_code.call_count == 2
    assert repository.create.call_count == 2
