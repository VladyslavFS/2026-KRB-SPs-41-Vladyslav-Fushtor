from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.warehouse.pg import PostgresRepository


@dataclass(frozen=True)
class BuildBIMartsJob:
    repo: PostgresRepository

    def run(self) -> None:
        """
        Rebuilds BI marts in Postgres by executing sql/004_bi_marts.sql.
        Uses TRUNCATE+INSERT inside SQL to be idempotent.
        """
        sql_path = Path("sql") / "004_bi_marts.sql"
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        sql = sql_path.read_text(encoding="utf-8")

        self.repo.execute(sql)
