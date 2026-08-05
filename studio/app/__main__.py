"""Run the service on the configured host and port.

``uvicorn app.main:app`` takes its host and port from the command line and ignores
configuration, so ``APP_HOST`` and ``APP_PORT`` were declared in ``Settings``,
documented in the local runbook's environment template, and read by nothing. Setting
them did exactly nothing, which is worse than not offering them.

    python -m app

The runbook's ``--reload`` form is still the right thing for development; this exists
so the documented deployment configuration is true.
"""

from __future__ import annotations

import uvicorn

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
