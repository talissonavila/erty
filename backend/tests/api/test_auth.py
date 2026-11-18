from http import HTTPStatus

from fastapi.testclient import TestClient

from app.models.user import User

LOGIN_URL = "/auth/login"


def test_login_url_returns_200(
    client_with_db: TestClient, user: User, password: str
) -> None:
    """Tests if login route returns 200 status code if schema is correct.

    Args:
    client_with_db (TestClient): A test client connected to the test database.
    user (User): A user stored in test database.
    password (str): A plain password.
    """
    response = client_with_db.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_with_incorrect_password_returns_401(
    client_with_db: TestClient,
    user: User,
) -> None:
    """Tests if login route returns 401 status code if password is incorrect.

    Args:
    client_with_db (TestClient): A test client connected to the test database.
    user (User): A user stored in test database.
    """
    response = client_with_db.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "User credentials invalid."}


def test_login_with_nonexistent_user_returns_401(
    client_with_db: TestClient, password: str
) -> None:
    """Tests if login route returns 401 status code if user do not exist.

    Args:
    client_with_db (TestClient): A test client connected to the test database.
    password (str): A plain password.
    """
    response = client_with_db.post(
        LOGIN_URL,
        json={
            "email": "invalid_email@email.com",
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "User credentials invalid."}


def test_login_with_inactive_user_returns_401(
    client_with_db: TestClient, user: User, password: str
) -> None:
    """Tests if login route returns 401 status code if user is inactive.

    Args:
    client_with_db (TestClient): A test client connected to the test database.
    user (User): A user stored in test database.
    password (str): A plain password.
    """
    user.is_active = False
    response = client_with_db.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
