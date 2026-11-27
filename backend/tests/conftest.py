from collections.abc import Callable, Generator
from typing import cast
from unittest.mock import create_autospec

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.db.session import SessionLocal, engine, get_db
from app.main import app
from app.models.url import URL
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated database session for integration tests."""
    connection = engine.connect()
    transaction = connection.begin()

    session = SessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_dependency() -> Generator[Session, None, None]:
    """Provide a session through the get_db dependency."""
    yield from get_db()


@pytest.fixture
def url_factory() -> Callable[[], URL]:
    """Provide a factory for generating fake URL instances.

    Returns:
        build_url (Callable[[], URL]): Fake instance of URL.
    """
    fake = Faker()

    def build_url(user: User) -> URL:
        return URL(
            user_id=user.id,
            original_url=fake.url(),
            short_code=fake.unique.bothify(text="????????"),
        )

    return build_url


@pytest.fixture
def client_with_db(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Provide a test client connected to the test database.

    Args:
        client (TestClient): The test client.
        db_session (Session): Fixture instance for database.
        monkeypatch (pytest.MonkeyPatch): Used to replace short code generation method.

    Returns:
        client (TestClient): The test client configured with the database override.
    """

    def override_get_db() -> Generator[Session, None, None]:
        """Yield the test database session."""
        yield db_session

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    return client


@pytest.fixture
def password() -> str:
    """Returns a plain password."""
    return "mysecretpassword"


@pytest.fixture
def user(db_session: Session, password: str) -> User:
    """Returns a user.

    Args:
        db_session (Session): Fixture instance for database.
        password (str): A plain password.
    """
    user = User(
        email="user_erty@email.com",
        hashed_password=get_password_hash(password),
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def another_user(db_session: Session, password: str) -> User:
    """Returns another user.

    Args:
        db_session (Session): Fixture instance for database.
        password (str): A plain password.
    """
    user = User(
        email="user2_erty@email.com",
        hashed_password=get_password_hash(password),
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def repository() -> UserRepository:
    """Returns a mocked UserRepository instance."""
    return cast(
        UserRepository,
        create_autospec(UserRepository, instance=True, spec_set=True),
    )


@pytest.fixture
def service(repository: UserRepository) -> AuthService:
    """Returns a AuthService with a mocked repository.

    Args:
        repository (UserRepository): The mocked UserRepository instance.
    """
    return AuthService(repository)


@pytest.fixture
def mock_user(password: str) -> User:
    """Returns a mocked User.

    Args:
        password (str): A plain password fixture.
    """
    return User(
        id=1,
        email="user_by_id@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
    )


@pytest.fixture
def authenticated_service(
    service: AuthService,
    repository: UserRepository,
    mock_user: User,
) -> AuthService:
    """Returns an AuthService configured with a valid user.

    Args:
        service (AuthService): A AuthService with a mocked repository.
        repository (UserRepository): A mocked UserRepository instance.
        mock_user (User): A mocked user.
    """
    repository.get_by_email.return_value = mock_user
    return service


@pytest.fixture
def plain_password() -> str:
    """Provide a plain password for testing.

    Returns:
        str: A plain password to use in tests.
    """
    return "mysecretpassword"


@pytest.fixture
def access_token(user: User) -> str:
    """Returns a valid access token for an existing user."

    Args:
        user (User):  A user stored in test database.
    """
    return create_access_token(subject=str(user.id))
