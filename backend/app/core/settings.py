import tomllib
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


def load_project_version() -> str:
    """Returns the app version from the backend pyproject.toml"""
    pyproject_path = BACKEND_DIR / "pyproject.toml"

    with pyproject_path.open("rb") as file:
        project_data = tomllib.load(file)

    project_version = project_data["project"]["version"]
    if not isinstance(project_version, str):
        raise TypeError("Project version must be a string.")
    return project_version


class Settings(BaseSettings):
    """Centralized application configuration.

    Values are loaded from environment variables or the root .env file.
    Environment variables take precedence over values from the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "ERTY API"
    app_version: str = Field(default_factory=load_project_version)

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "erty"
    postgres_user: str = "erty_user"
    postgres_password: SecretStr


settings = Settings()
