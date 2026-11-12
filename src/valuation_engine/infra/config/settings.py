from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings.

    Environment variables are used for configuration to keep
    the codebase environment-agnostic (local / docker / aws).
    """

    DB_URL: str = os.getenv(
        "DB_URL",
        "mysql+pymysql://root:sometime@127.0.0.1:3306/basedata?charset=utf8mb4",
    )

    APP_ENV: str = os.getenv("APP_ENV", "local")


settings = Settings()