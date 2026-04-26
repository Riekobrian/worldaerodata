from __future__ import annotations

from mappers.base import Mapper
from models.canonical import AirlineCanonical, RouteCanonical


class OpenFlightsAirlineMapper(Mapper):
    def map_record(self, source_name: str, raw: dict) -> AirlineCanonical:
        active_flag = (raw.get("active") or "Y").strip().upper()
        return AirlineCanonical(
            source=source_name,
            source_record_id=str(raw.get("airline_id", "")),
            airline_name=(raw.get("name") or "").strip(),
            iata_code=self._normalize_nullable(raw.get("iata")),
            icao_code=self._normalize_nullable(raw.get("icao")),
            callsign=self._normalize_nullable(raw.get("callsign")),
            country_name=self._normalize_nullable(raw.get("country")),
            active=active_flag == "Y",
        )

    @staticmethod
    def _normalize_nullable(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or value == r"\N":
            return None
        return value


class OpenFlightsRouteMapper(Mapper):
    def map_record(self, source_name: str, raw: dict) -> RouteCanonical:
        source_airport = self._normalize_code(raw.get("source_airport"))
        destination_airport = self._normalize_code(raw.get("destination_airport"))
        if source_airport is None or destination_airport is None:
            raise ValueError("Route missing source or destination airport code")

        stops_raw = (raw.get("stops") or "0").strip()
        stops = int(stops_raw) if stops_raw.isdigit() else 0

        return RouteCanonical(
            source=source_name,
            source_record_id=self._route_source_id(raw),
            airline_code=self._normalize_code(raw.get("airline")),
            source_airport_code=source_airport,
            destination_airport_code=destination_airport,
            stops=stops,
            equipment=self._normalize_nullable(raw.get("equipment")),
            codeshare=((raw.get("codeshare") or "").strip().upper() == "Y"),
        )

    @staticmethod
    def _route_source_id(raw: dict) -> str:
        airline = (raw.get("airline") or "NA").strip()
        src = (raw.get("source_airport") or "NA").strip()
        dst = (raw.get("destination_airport") or "NA").strip()
        return f"{airline}:{src}:{dst}"

    @staticmethod
    def _normalize_code(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or value == r"\N":
            return None
        return value.upper()

    @staticmethod
    def _normalize_nullable(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or value == r"\N":
            return None
        return value
