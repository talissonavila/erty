import tomllib

from pathlib import Path

class Settings:
    def __init__(self) -> None:
        self.app_name = "ERTY API"
        self.app_version = self._load_project_version()

    def _load_project_version(self) -> str:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"

        with pyproject.open("rb") as f:
            data = tomllib.load(f)

        return data["project"]["version"]


settings = Settings()
