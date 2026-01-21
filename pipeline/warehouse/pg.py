from __future__ import annotations

from dataclasses import dataclass
import os
import psycopg2
from psycopg2.extras import execute_values

from pipeline.config.pg_settings import PostgresSettings


class PostgresRepository:
    def __init__(self, settings: PostgresSettings):
        self._settings = settings

    def _conn(self):
        return psycopg2.connect(
            host=self._settings.host,
            port=self._settings.port,
            dbname=self._settings.db,
            user=self._settings.user,
            password=self._settings.password,
        )
    
    def upsert_earthquakes(self, rows: list[dict]) -> int:
        """
        UPSERT into ods.fct_earthquake_event.
        Only updates if excluded.updated > current.updated.
        Returns number of input rows (Postgres doesn't easily return affected count with execute_values).
        """
        if not rows:
            return 0
        
        cols = [
            "id",
            "time", "updated",
            "latitude", "longitude", "depth",
            "mag", "mag_type",
            "place", "event_type", "status", "net",
            "url", "detail", "tsunami",
            "source_window_start", "source_window_end",
        ]

        values = [[row.get(col) for col in cols] for row in rows]

        sql = f"""
        INSERT INTO ods.fct_earthquake_event ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
          time = EXCLUDED.time,
          updated = EXCLUDED.updated,
          latitude = EXCLUDED.latitude,
          longitude = EXCLUDED.longitude,
          depth = EXCLUDED.depth,
          mag = EXCLUDED.mag,
          mag_type = EXCLUDED.mag_type,
          place = EXCLUDED.place,
          event_type = EXCLUDED.event_type,
          status = EXCLUDED.status,
          net = EXCLUDED.net,
          url = EXCLUDED.url,
          detail = EXCLUDED.detail,
          tsunami = EXCLUDED.tsunami,
          source_window_start = EXCLUDED.source_window_start,
          source_window_end = EXCLUDED.source_window_end,
          ingested_at = now()
        WHERE ods.fct_earthquake_event.updated < EXCLUDED.updated;
        """

        with self._conn() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, sql, values, page_size=2000)
        
        return len(rows)