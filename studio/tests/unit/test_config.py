"""Settings behaviour."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import PROJECT_ROOT, AssetStoreKind, Settings

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_defaults_match_the_documented_deployment_recommendation() -> None:
    settings = _settings()

    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 10
    assert settings.db_pool_timeout_seconds == 30
    assert settings.db_pool_recycle_seconds == 1800
    assert settings.db_sslmode == "require"
    assert settings.openai_timeout_seconds == 180
    assert settings.openai_image_size == "1536x1024"
    assert settings.openai_image_quality == "high"
    assert settings.asset_store is AssetStoreKind.FILESYSTEM
    assert settings.git_enabled is True
    assert settings.debug is False


def test_binds_to_localhost_by_default() -> None:
    assert _settings().app_host == "127.0.0.1"


def test_openai_model_names_have_no_default() -> None:
    """A guessed model name can cost money, so nothing is assumed."""
    settings = _settings()

    assert settings.openai_text_model == ""
    assert settings.openai_review_model == ""
    assert settings.openai_image_model == ""


def test_api_key_is_absent_by_default_and_not_repeated_in_output() -> None:
    settings = _settings()
    assert settings.openai_api_key is None

    with_key = _settings(openai_api_key="sk-should-never-be-printed")
    assert with_key.openai_api_key is not None
    assert with_key.openai_api_key.get_secret_value() == "sk-should-never-be-printed"
    assert "sk-should-never-be-printed" not in repr(with_key)


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://app:secret@db.example:5432/shirtfaced_studio",
        "postgresql+psycopg2://app:secret@db.example:5432/shirtfaced_studio",
        "sqlite:///./local.sqlite3",
    ],
)
def test_database_url_must_use_psycopg_3(url: str) -> None:
    """SQLite is not a production target, and psycopg 2 is not the chosen driver."""
    with pytest.raises(ValidationError, match="psycopg 3"):
        _settings(database_url=url)


def test_relative_storage_paths_resolve_against_the_project_root() -> None:
    settings = _settings(worlds_root="worlds", assets_root="var/assets")

    assert settings.worlds_root_resolved == (PROJECT_ROOT / "worlds").resolve()
    assert settings.assets_root_resolved == (PROJECT_ROOT / "var" / "assets").resolve()


def test_absolute_storage_paths_are_left_alone() -> None:
    absolute = PROJECT_ROOT / "elsewhere" / "assets"
    assert _settings(assets_root=absolute).assets_root_resolved == absolute


def test_environment_variables_populate_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The keys in .env.example are the keys the application reads."""
    monkeypatch.setenv("DATABASE_URL", VALID_URL)
    monkeypatch.setenv("DB_POOL_SIZE", "9")
    monkeypatch.setenv("DB_SSLMODE", "disable")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "an-image-model")
    monkeypatch.setenv("APP_PORT", "9001")
    monkeypatch.setenv("GIT_ENABLED", "false")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.db_pool_size == 9
    assert settings.db_sslmode == "disable"
    assert settings.openai_image_model == "an-image-model"
    assert settings.app_port == 9001
    assert settings.git_enabled is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("db_pool_size", 0),
        ("db_max_overflow", -1),
        ("db_pool_timeout_seconds", 0),
        ("openai_timeout_seconds", 0),
        ("app_port", 0),
        ("app_port", 70000),
        ("db_sslmode", "sometimes"),
        ("asset_store", "oracle-object-storage"),
    ],
)
def test_invalid_values_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        _settings(**{field: value})
