from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    """Raised when user credentials are invalid.

    Attributes:
        message (str): Description of the authentication error.
    """

    def __init__(
        self,
        message: str = "User credentials invalid.",
    ) -> None:
        """Initialize the exception with an error message.

        Args:
            message (str): Description of the authentication error.
            Defaults to "User credentials invalid."
        """
        self.message = message
        super().__init__(message)


class AuthService:
    """Handle business logic to users."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a User repository.

        Args:
            repository (UserRepository): Handle database operations for users.
        """
        self.repository = repository

    def authenticate(self, email: str, password: str) -> str:
        """Handle access token to authenticated users.

        Args:
            email (str): user email.
            password (str): user password.

        Returns:
            str: Access token.

        Raises:
            InvalidCredentialsError: Raised when user credentials are invalid.
        """
        user: User | None = self.repository.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(
                plain_password=password,
                hashed_password=user.hashed_password,
            )
        ):
            raise InvalidCredentialsError("User credentials invalid.")
        return create_access_token(str(user.id))
