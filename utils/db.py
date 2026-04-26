from __future__ import annotations

import contextlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg import Connection

from utils.env import load_dotenv


DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"


@dataclass
class Database:
    dsn: str
    _conn: Connection | None = None

    @classmethod
    def from_env(cls) -> "Database":
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env")
        return cls(dsn=os.getenv("FLIGHT_PIPELINE_DB_DSN", DEFAULT_DSN))

    @contextlib.contextmanager
    def session(self):
        self.connect()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
        finally:
            self.close()

    def connect(self) -> None:
        if self._conn is None:
            self._conn = psycopg.connect(self.dsn, autocommit=False)

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn is not None:
            self._conn.rollback()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute_schema_file(self, schema_path: Path) -> None:
        sql = schema_path.read_text(encoding="utf-8")
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)

    def insert_run_start(self, source_name: str, dry_run: bool) -> int:
        query = """
            INSERT INTO pipeline_runs (source_name, status, dry_run)
            VALUES (%s, 'running', %s)
            RETURNING id
        """
        with self._conn.cursor() as cursor:
            cursor.execute(query, (source_name, dry_run))
            return int(cursor.fetchone()[0])

    def update_run_end(
        self,
        run_id: int,
        status: str,
        records_in: int,
        records_ok: int,
        records_failed: int,
        message: str | None = None,
    ) -> None:
        query = """
            UPDATE pipeline_runs
            SET status = %s,
                records_in = %s,
                records_ok = %s,
                records_failed = %s,
                finished_at = now(),
                message = %s
            WHERE id = %s
        """
        with self._conn.cursor() as cursor:
            cursor.execute(
                query,
                (status, records_in, records_ok, records_failed, message, run_id),
            )

    def insert_quarantine(
        self,
        run_id: int,
        source_name: str,
        source_record_id: str,
        raw_payload: dict[str, Any],
        error_reason: str,
    ) -> None:
        self.bulk_insert_quarantine(
            [
                {
                    "run_id": run_id,
                    "source_name": source_name,
                    "source_record_id": source_record_id,
                    "raw_payload": raw_payload,
                    "error_reason": error_reason,
                }
            ]
        )

    def bulk_insert_quarantine(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        query = """
            INSERT INTO quarantine_records
                (run_id, source_name, source_record_id, raw_payload, error_reason)
            VALUES (%(run_id)s, %(source_name)s, %(source_record_id)s, %(raw_payload)s::jsonb, %(error_reason)s)
        """
        payloads = []
        for item in records:
            payloads.append(
                {
                    "run_id": item["run_id"],
                    "source_name": item["source_name"],
                    "source_record_id": item["source_record_id"],
                    "raw_payload": json.dumps(item["raw_payload"]),
                    "error_reason": item["error_reason"],
                }
            )
        self._execute_many(query, payloads)

    def bulk_upsert_airports(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        query = """
            INSERT INTO airports
                (source, source_record_id, ident, iata_code, icao_code, airport_name, municipality, country_code, latitude_deg, longitude_deg, ingested_at)
            VALUES
                (%(source)s, %(source_record_id)s, %(ident)s, %(iata_code)s, %(icao_code)s, %(airport_name)s, %(municipality)s, %(country_code)s, %(latitude_deg)s, %(longitude_deg)s, %(ingested_at)s)
            ON CONFLICT (source, source_record_id)
            DO UPDATE SET
                ident = EXCLUDED.ident,
                iata_code = EXCLUDED.iata_code,
                icao_code = EXCLUDED.icao_code,
                airport_name = EXCLUDED.airport_name,
                municipality = EXCLUDED.municipality,
                country_code = EXCLUDED.country_code,
                latitude_deg = EXCLUDED.latitude_deg,
                longitude_deg = EXCLUDED.longitude_deg,
                ingested_at = EXCLUDED.ingested_at
        """
        self._execute_many(query, records)

    def bulk_upsert_airlines(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        query = """
            INSERT INTO airlines
                (source, source_record_id, airline_name, iata_code, icao_code, callsign, country_name, active, ingested_at)
            VALUES
                (%(source)s, %(source_record_id)s, %(airline_name)s, %(iata_code)s, %(icao_code)s, %(callsign)s, %(country_name)s, %(active)s, %(ingested_at)s)
            ON CONFLICT (source, source_record_id)
            DO UPDATE SET
                airline_name = EXCLUDED.airline_name,
                iata_code = EXCLUDED.iata_code,
                icao_code = EXCLUDED.icao_code,
                callsign = EXCLUDED.callsign,
                country_name = EXCLUDED.country_name,
                active = EXCLUDED.active,
                ingested_at = EXCLUDED.ingested_at
        """
        self._execute_many(query, records)

    def bulk_upsert_routes(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        query = """
            INSERT INTO routes
                (source, source_record_id, airline_code, source_airport_code, destination_airport_code, stops, equipment, codeshare, ingested_at)
            VALUES
                (%(source)s, %(source_record_id)s, %(airline_code)s, %(source_airport_code)s, %(destination_airport_code)s, %(stops)s, %(equipment)s, %(codeshare)s, %(ingested_at)s)
            ON CONFLICT (source, source_record_id)
            DO UPDATE SET
                airline_code = EXCLUDED.airline_code,
                source_airport_code = EXCLUDED.source_airport_code,
                destination_airport_code = EXCLUDED.destination_airport_code,
                stops = EXCLUDED.stops,
                equipment = EXCLUDED.equipment,
                codeshare = EXCLUDED.codeshare,
                ingested_at = EXCLUDED.ingested_at
        """
        self._execute_many(query, records)

    def bulk_upsert_flight_offers(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        query = """
            INSERT INTO flight_offers
                (source, source_record_id, offer_id, origin, destination, departure_at, total_price, currency, ingested_at)
            VALUES
                (%(source)s, %(source_record_id)s, %(offer_id)s, %(origin)s, %(destination)s, %(departure_at)s, %(total_price)s, %(currency)s, %(ingested_at)s)
            ON CONFLICT (source, source_record_id)
            DO UPDATE SET
                offer_id = EXCLUDED.offer_id,
                origin = EXCLUDED.origin,
                destination = EXCLUDED.destination,
                departure_at = EXCLUDED.departure_at,
                total_price = EXCLUDED.total_price,
                currency = EXCLUDED.currency,
                ingested_at = EXCLUDED.ingested_at
        """
        self._execute_many(query, records)

    def _execute_many(self, query: str, rows: list[dict[str, Any]]) -> None:
        with self._conn.cursor() as cursor:
            cursor.executemany(query, rows)
