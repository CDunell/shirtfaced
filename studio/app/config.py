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

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _garments_dir() -> Path:
    """Where the garment SVGs are, in a checkout and on the box."""
    deployed = PROJECT_ROOT / "assets" / "garments"
    if deployed.is_dir():
        return deployed
    return PROJECT_ROOT.parent / "assets" / "garments"


GARMENTS_DIR = _garments_dir()


class AssetStoreKind(StrEnum):
    """Supported asset store back ends."""

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

    openai_api_key: SecretStr | None = None
    openai_text_model: str = ""
    openai_review_model: str = ""
    openai_image_model: str = ""
    openai_image_draft_model: str = ""
    openai_image_size: str = "1536x1024"
    openai_image_quality: str = "high"
    reference_image_limit: int = Field(default=4, ge=0, le=16)
    openai_timeout_seconds: float = Field(default=180.0, gt=0)

    # Google renderer. It is deliberately disabled until both the feature switch
    # and key are present. Model names are explicit so a provider change can never
    # silently move production onto a more expensive model.
    google_media_enabled: bool = False
    gemini_api_key: SecretStr | None = None
    google_image_model: str = "gemini-3.1-flash-image"
    google_video_model: str = "veo-3.1-fast-generate-preview"
    # 1K on a 9:16 frame is 768x1376, which is under the 1080x1920 a Veo first
    # frame wants and was being upscaled into it.
    google_image_size: str = "2K"

    # Where the Veo trigger gets committed. The box is an rsync target with no
    # git remote and no GitHub credential, and the workflow only starts on a
    # push, so Studio cannot fire it — it can only hand the operator a
    # pre-filled commit. Overridable so a fork is not asking somebody else to
    # commit to this repository.
    github_repository: str = "CDunell/shirtfaced"
    github_branch: str = "main"
    # A contact sheet is nine images in one file, so a size that is generous for
    # a single frame is a thumbnail for each panel. The first sheet came back
    # 1376x768: nine cells of roughly 459x256, and the extraction was then asked
    # to reproduce a postage stamp as a full frame.
    google_sheet_image_size: str = "4K"
    google_video_resolution: str = "1080p"
    google_video_poll_seconds: float = Field(default=10.0, ge=1.0)
    google_video_timeout_seconds: float = Field(default=900.0, ge=30.0)

    # Economic guardrails. These are workflow budgets, not provider price claims.
    # They cap what Studio is allowed to initiate without an explicit override.
    renderer_scene_budget_usd: float = Field(default=12.0, ge=0.0)
    renderer_validation_budget_usd: float = Field(default=100.0, ge=0.0)
    renderer_monthly_budget_usd: float = Field(default=250.0, ge=0.0)
    renderer_seed_candidates: int = Field(default=3, ge=1, le=8)
    renderer_video_candidates: int = Field(default=2, ge=1, le=6)

    database_url: str
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: float = Field(default=30.0, gt=0)
    db_pool_recycle_seconds: int = Field(default=1800, ge=-1)
    db_sslmode: SslMode = "require"

    worlds_root: Path = PROJECT_ROOT / "worlds"
    assets_root: Path = PROJECT_ROOT / "var" / "assets"
    asset_store: AssetStoreKind = AssetStoreKind.FILESYSTEM

    reference_active_limit: int = Field(default=16, ge=1, le=100)

    social_publishing_enabled: bool = False
    social_publisher_mode: Literal["disabled", "fake", "platform"] = "disabled"
    social_max_attempts: int = Field(default=5, ge=1, le=20)
    social_retry_base_seconds: int = Field(default=60, ge=5, le=86400)

    email_delivery_enabled: bool = False
    email_adapter_mode: Literal["disabled", "local", "provider"] = "disabled"
    email_from_transactional: str = "orders@mail.shirtfaced.wtf"
    email_from_marketing: str = "hello@news.shirtfaced.wtf"
    email_reply_to: str = "hello@shirtfaced.wtf"
    email_preview_root: Path = PROJECT_ROOT / "var" / "email-previews"

    web_dist_root: Path = PROJECT_ROOT / "web" / "dist"

    git_enabled: bool = True
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

    @field_validator("database_url")
    @classmethod
    def _require_psycopg_driver(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL must use the psycopg 3 driver, "
                "for example postgresql+psycopg://user:password@host:5432/shirtfaced_studio"
            )
        return value

    @property
    def google_media_live(self) -> bool:
        return bool(self.google_media_enabled and self.gemini_api_key)

    @property
    def worlds_root_resolved(self) -> Path:
        return self._resolve(self.worlds_root)

    @property
    def assets_root_resolved(self) -> Path:
        return self._resolve(self.assets_root)

    @property
    def email_preview_root_resolved(self) -> Path:
        return self._resolve(self.email_preview_root)

    @property
    def web_dist_root_resolved(self) -> Path:
        return self._resolve(self.web_dist_root)

    @staticmethod
    def _resolve(path: Path) -> Path:
        return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
