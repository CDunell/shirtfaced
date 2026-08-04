"""Application settings.

Every key here corresponds to a key in ``.env.example``. Settings are read from the
process environment first and from a local ``.env`` file second, so a deployment can
supply values through Oracle Cloud Vault or a protected service environment file
without a ``.env`` ever existing on disk.

Secrets are never given defaults and are never logged.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The project root is the directory containing ``pyproject.toml``.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AssetStoreKind(StrEnum):
    """Supported asset store back ends.

    Only ``filesystem`` is implemented in Version 1. Oracle Object Storage is
    introduced later behind the same ``AssetStore`` interface.
    """

    FILESYSTEM = "filesystem"


SslMode = Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]


class Settings(BaseSettings):
    """Runtime configuration for Shirtfaced Studio."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- OpenAI -----------------------------------------------------------------
    # Model names deliberately have no defaults. Guessing a model name can cause
    # unexpected cost, so the services that need one fail loudly when it is unset.
    openai_api_key: SecretStr | None = None
    openai_text_model: str = ""
    openai_review_model: str = ""
    openai_image_model: str = ""
    openai_image_size: str = "1536x1024"
    openai_image_quality: str = "high"
    openai_timeout_seconds: float = Field(default=180.0, gt=0)

    # --- PostgreSQL -------------------------------------------------------------
    # No default: the database must always be chosen explicitly.
    database_url: str
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: float = Field(default=30.0, gt=0)
    db_pool_recycle_seconds: int = Field(default=1800, ge=-1)
    db_sslmode: SslMode = "require"

    # --- Storage ----------------------------------------------------------------
    worlds_root: Path = PROJECT_ROOT / "worlds"
    assets_root: Path = PROJECT_ROOT / "var" / "assets"
    asset_store: AssetStoreKind = AssetStoreKind.FILESYSTEM

    # --- Interface --------------------------------------------------------------
    # Built Base Web assets. In development the Vite dev server serves these instead
    # and proxies the API, so this directory may not exist.
    web_dist_root: Path = PROJECT_ROOT / "web" / "dist"

    # --- Application ------------------------------------------------------------
    git_enabled: bool = True
    # Bind to localhost by default; deployments put a reverse proxy in front and
    # override this with the interface the proxy can reach.
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

    @field_validator("database_url")
    @classmethod
    def _require_psycopg_driver(cls, value: str) -> str:
        """Reject connection strings that would silently select another driver."""
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL must use the psycopg 3 driver, "
                "for example postgresql+psycopg://user:password@host:5432/shirtfaced_studio"
            )
        return value

    @property
    def worlds_root_resolved(self) -> Path:
        """Absolute worlds directory, resolved against the project root."""
        return self._resolve(self.worlds_root)

    @property
    def assets_root_resolved(self) -> Path:
        """Absolute assets directory, resolved against the project root."""
        return self._resolve(self.assets_root)

    @property
    def web_dist_root_resolved(self) -> Path:
        """Absolute built-interface directory, resolved against the project root."""
        return self._resolve(self.web_dist_root)

    @staticmethod
    def _resolve(path: Path) -> Path:
        return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, reading the environment once."""
    return Settings()  # values come from the environment
