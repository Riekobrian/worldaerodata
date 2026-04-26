from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from connectors.mocksource import MockSourceConnector
from connectors.openflights import OpenFlightsConnector
from connectors.opensky import OpenSkyConnector
from connectors.ourairports import OurAirportsConnector
from mappers.mocksource import MockSourceOfferMapper
from mappers.openflights import OpenFlightsAirlineMapper, OpenFlightsRouteMapper
from mappers.opensky import OpenSkyStateMapper
from mappers.ourairports import OurAirportsAirportMapper
from models.canonical import (
    AirlineCanonical,
    AirportCanonical,
    FlightOfferCanonical,
    RouteCanonical,
)
from utils.db import Database
from utils.generate_dashboard import fetch_pipeline_runs, generate_html_dashboard


CONNECTORS = {
    "ourairports": OurAirportsConnector(),
    "openflights": OpenFlightsConnector(),
    "mocksource": MockSourceConnector(),
}

MAPPERS = {
    "ourairports_airport": OurAirportsAirportMapper(),
    "openflights_airline": OpenFlightsAirlineMapper(),
    "openflights_route": OpenFlightsRouteMapper(),
    "mocksource_offer": MockSourceOfferMapper(),
    "opensky_state": OpenSkyStateMapper(),
}


def load_sources(registry_path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    return loaded["sources"]


def run_single_source(
    source_name: str,
    source_config: dict[str, Any],
    db: Database,
    dry_run: bool,
    batch_size: int,
    log_every: int,
) -> dict[str, Any]:
    logger = logging.getLogger("flight_pipeline")
    
    # Handle OpenSky connector which requires credentials
    connector_name = source_config["connector"]
    if connector_name == "opensky":
        credentials = source_config.get("credentials", {})
        connector = OpenSkyConnector(
            client_id=credentials.get("client_id"),
            client_secret=credentials.get("client_secret"),
        )
    else:
        connector = CONNECTORS[connector_name]
    
    mapper = MAPPERS[source_config["mapper"]]

    run_id = -1
    if not dry_run:
        run_id = db.insert_run_start(source_name=source_name, dry_run=dry_run)

    records_in = 0
    records_ok = 0
    records_failed = 0
    started = time.monotonic()
    buffers = {
        "airports": [],
        "airlines": [],
        "routes": [],
        "flight_offers": [],
        "quarantine": [],
    }

    retry_cfg = source_config.get("retry", {})
    max_attempts = int(retry_cfg.get("max_attempts", 1))
    backoff_seconds = int(retry_cfg.get("backoff_seconds", 0))

    try:
        records = _fetch_with_retry(
            connector=connector,
            source_config=source_config,
            max_attempts=max_attempts,
            backoff_seconds=backoff_seconds,
        )
        for raw in records:
            records_in += 1
            try:
                canonical = mapper.map_record(source_name, raw)
                _apply_business_rules(canonical)
                if not dry_run:
                    _buffer_canonical(buffers, canonical)
                    if _buffer_size(buffers) >= batch_size:
                        _flush_buffers(db, source_name, run_id, buffers)
                records_ok += 1
            except (ValidationError, ValueError, TypeError) as error:
                records_failed += 1
                if not dry_run:
                    buffers["quarantine"].append(
                        {
                            "run_id": run_id,
                            "source_name": source_name,
                            "source_record_id": _safe_source_record_id(raw),
                            "raw_payload": raw,
                            "error_reason": str(error),
                        }
                    )
                    if len(buffers["quarantine"]) >= batch_size:
                        _flush_buffers(db, source_name, run_id, buffers)

            if records_in % log_every == 0:
                elapsed = time.monotonic() - started
                logger.info(
                    "source=%s processed=%s ok=%s failed=%s elapsed=%.1fs",
                    source_name,
                    records_in,
                    records_ok,
                    records_failed,
                    elapsed,
                )

        if not dry_run:
            _flush_buffers(db, source_name, run_id, buffers)
        status = "success" if records_failed == 0 else "partial_success"
        if not dry_run:
            db.update_run_end(
                run_id=run_id,
                status=status,
                records_in=records_in,
                records_ok=records_ok,
                records_failed=records_failed,
            )
        elapsed = time.monotonic() - started
        logger.info(
            "source=%s done status=%s in=%s ok=%s failed=%s elapsed=%.1fs",
            source_name,
            status,
            records_in,
            records_ok,
            records_failed,
            elapsed,
        )
        return {
            "source_name": source_name,
            "status": status,
            "records_in": records_in,
            "records_ok": records_ok,
            "records_failed": records_failed,
        }
    except Exception as error:  # pragma: no cover - runtime protection
        if not dry_run:
            db.update_run_end(
                run_id=run_id,
                status="failed",
                records_in=records_in,
                records_ok=records_ok,
                records_failed=records_failed,
                message=str(error),
            )
        raise


def _fetch_with_retry(
    connector: Any,
    source_config: dict[str, Any],
    max_attempts: int,
    backoff_seconds: int,
):
    attempt = 0
    while True:
        attempt += 1
        try:
            return connector.fetch(source_config)
        except Exception:
            if attempt >= max_attempts:
                raise
            time.sleep(backoff_seconds * attempt)


def _safe_source_record_id(raw: dict[str, Any]) -> str:
    value = raw.get("id") or raw.get("record_id") or raw.get("airline_id") or ""
    return str(value)


def _apply_business_rules(canonical: Any) -> None:
    if isinstance(canonical, RouteCanonical):
        if canonical.source_airport_code == canonical.destination_airport_code:
            raise ValueError("Route source and destination cannot be the same")
    if isinstance(canonical, FlightOfferCanonical):
        if canonical.origin == canonical.destination:
            raise ValueError("Offer origin and destination cannot be the same")


def _buffer_canonical(buffers: dict[str, list[dict[str, Any]]], canonical: Any) -> None:
    payload = canonical.model_dump()
    if isinstance(canonical, AirportCanonical):
        buffers["airports"].append(payload)
    elif isinstance(canonical, AirlineCanonical):
        buffers["airlines"].append(payload)
    elif isinstance(canonical, RouteCanonical):
        buffers["routes"].append(payload)
    elif isinstance(canonical, FlightOfferCanonical):
        buffers["flight_offers"].append(payload)
    else:
        raise TypeError(f"Unsupported canonical type: {type(canonical)}")


def _buffer_size(buffers: dict[str, list[dict[str, Any]]]) -> int:
    return (
        len(buffers["airports"])
        + len(buffers["airlines"])
        + len(buffers["routes"])
        + len(buffers["flight_offers"])
        + len(buffers["quarantine"])
    )


def _flush_buffers(
    db: Database,
    source_name: str,
    run_id: int,
    buffers: dict[str, list[dict[str, Any]]],
) -> None:
    logger = logging.getLogger("flight_pipeline")
    airports = buffers["airports"]
    airlines = buffers["airlines"]
    routes = buffers["routes"]
    offers = buffers["flight_offers"]
    quarantine = buffers["quarantine"]

    if airports:
        db.bulk_upsert_airports(airports)
        logger.debug("source=%s run_id=%s flushed airports=%s", source_name, run_id, len(airports))
        airports.clear()
    if airlines:
        db.bulk_upsert_airlines(airlines)
        logger.debug("source=%s run_id=%s flushed airlines=%s", source_name, run_id, len(airlines))
        airlines.clear()
    if routes:
        db.bulk_upsert_routes(routes)
        logger.debug("source=%s run_id=%s flushed routes=%s", source_name, run_id, len(routes))
        routes.clear()
    if offers:
        db.bulk_upsert_flight_offers(offers)
        logger.debug("source=%s run_id=%s flushed offers=%s", source_name, run_id, len(offers))
        offers.clear()
    if quarantine:
        db.bulk_insert_quarantine(quarantine)
        logger.debug("source=%s run_id=%s flushed quarantine=%s", source_name, run_id, len(quarantine))
        quarantine.clear()

    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run declarative flight data ingestion.")
    parser.add_argument("--source", default="all", help="Source key from sources.yaml or 'all'")
    parser.add_argument("--registry", default="registry/sources.yaml", help="Registry path")
    parser.add_argument("--dry-run", action="store_true", help="Run without DB writes")
    parser.add_argument("--init-db", action="store_true", help="Create DB tables from sql/schema.sql")
    parser.add_argument("--batch-size", type=int, default=2000, help="DB write batch size")
    parser.add_argument("--log-every", type=int, default=5000, help="Progress log interval")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger("flight_pipeline")

    root = ROOT
    registry_path = root / args.registry
    sources = load_sources(registry_path)

    db = Database.from_env()
    if args.init_db:
        db.execute_schema_file(root / "sql/schema.sql")
        print("Schema initialized.")
        return

    selected: list[tuple[str, dict[str, Any]]] = []
    if args.source == "all":
        selected = [(name, cfg) for name, cfg in sources.items() if cfg.get("enabled", True)]
    else:
        if args.source not in sources:
            raise ValueError(f"Unknown source: {args.source}")
        selected = [(args.source, sources[args.source])]

    results = []
    if args.dry_run:
        for source_name, source_config in selected:
            logger.info("starting source=%s dry_run=true", source_name)
            result = run_single_source(
                source_name=source_name,
                source_config=source_config,
                db=db,
                dry_run=True,
                batch_size=args.batch_size,
                log_every=args.log_every,
            )
            results.append(result)
            print(json.dumps(result))
    else:
        with db.session():
            for source_name, source_config in selected:
                logger.info("starting source=%s dry_run=false", source_name)
                result = run_single_source(
                    source_name=source_name,
                    source_config=source_config,
                    db=db,
                    dry_run=False,
                    batch_size=args.batch_size,
                    log_every=args.log_every,
                )
                results.append(result)
                print(json.dumps(result))

    total_in = sum(item["records_in"] for item in results)
    total_ok = sum(item["records_ok"] for item in results)
    total_failed = sum(item["records_failed"] for item in results)
    print(
        json.dumps(
            {
                "summary": {
                    "sources": len(results),
                    "records_in": total_in,
                    "records_ok": total_ok,
                    "records_failed": total_failed,
                }
            }
        )
    )

    # Generate dashboard if database is available and not dry-run
    if not args.dry_run:
        try:
            runs = fetch_pipeline_runs(limit=20)
            if runs:
                html = generate_html_dashboard(runs)
                dashboard_path = root / "dashboard.html"
                dashboard_path.write_text(html)
                logger.info(f"Dashboard generated: {dashboard_path}")
        except Exception as e:
            logger.debug(f"Dashboard generation skipped: {e}")


if __name__ == "__main__":
    main()
