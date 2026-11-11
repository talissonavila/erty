import pytest

from app.core import settings as settings_module


def test_load_project_version_raises_type_error_for_non_string(
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure project version must be a string."""
    pyproject_path = tmp_path / "pyproject.toml"

    pyproject_path.write_text("[project]\nversion = 123\n", encoding="utf-8")

    monkeypatch.setattr(settings_module, "BACKEND_DIR", tmp_path)

    with pytest.raises(TypeError, match="Project version must be a string."):
        settings_module.load_project_version()
