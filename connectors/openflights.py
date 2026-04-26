from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable

import requests

from connectors.base import Connector


OPENFLIGHTS_AIRLINE_HEADERS = [
    "airline_id",
    "name",
    "alias",
    "iata",
    "icao",
    "callsign",
    "country",
    "active",
]

OPENFLIGHTS_ROUTE_HEADERS = [
    "airline",
    "airline_id",
    "source_airport",
    "source_airport_id",
    "destination_airport",
    "destination_airport_id",
    "codeshare",
    "stops",
    "equipment",
]


class OpenFlightsConnector(Connector):
    def fetch(self, source_config: dict) -> Iterable[dict]:
        url = source_config["dataset_url"]
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        headers = self._select_headers(url)
        reader = csv.DictReader(StringIO(response.text), fieldnames=headers)
        for row in reader:
            yield row

    @staticmethod
    def _select_headers(url: str) -> list[str]:
        if "airlines.dat" in url:
            return OPENFLIGHTS_AIRLINE_HEADERS
        if "routes.dat" in url:
            return OPENFLIGHTS_ROUTE_HEADERS
        raise ValueError(f"Unsupported OpenFlights dataset URL: {url}")
