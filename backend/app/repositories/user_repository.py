from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class UserEmailConflictError(Exception):
    """Raised when a user creation violates its unique constraints."""


class UserRepository:
    """Handle database operations for users."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): database session.
        """
        self.session = session

    def create_user(self, user: User) -> User:
        """Add a User within a savepoint in the current transaction.

        Args:
            user (User): User to be created.

        Returns:
            user (User): Created user.

        Raises:
            UserEmailConflictError: Raised when a user creation violates its unique
            constraints.
        """
        try:
            with self.session.begin_nested():
                self.session.add(user)
                self.session.flush()
        except IntegrityError as error:
            if (
                isinstance(error.orig, UniqueViolation)
                and error.orig.diag.constraint_name == "uq_users_email"
            ):
                raise UserEmailConflictError(
                    "This user email already exists."
                ) from error
            raise
        return user

    def get_by_email(self, user_email: str) -> User | None:
        """Retrieve a User using its email.

        Args:
            user_email (str): The user email to search the User on database.

        Returns:
            User | None: The User object case its in database.
            None, otherwise.
        """
        statement = select(User).where(User.email == user_email)
        return self.session.scalar(statement)

    def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a User using its id.

        Args:
            user_id (int): The user id to search the User on database.

        Returns:
            User | None: The User object case its in database.
            None, otherwise.
        """
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)
