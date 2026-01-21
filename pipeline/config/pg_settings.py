from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    db: str
    user: str
    password: str

    @staticmethod
    def from_env() -> PostgresSettings:
        return PostgresSettings(
            host=os.getenv("DWH_HOST", "localhost"),
            port=int(os.getenv("DWH_PORT", "5432")),
            db=os.getenv("DWH_DB", "earthquake"),
            user=os.getenv("DWH_USER", "postgres"),
            password=os.getenv("DWH_PASSWORD", "postgres"),
        )