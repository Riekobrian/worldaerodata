from __future__ import annotations

from typing import Optional

from mappers.base import Mapper
from models.canonical import AirportCanonical


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return float(value)


class OurAirportsAirportMapper(Mapper):
    def map_record(self, source_name: str, raw: dict) -> AirportCanonical:
        return AirportCanonical(
            source=source_name,
            source_record_id=str(raw.get("id", "")),
            ident=raw.get("ident", "") or "",
            iata_code=raw.get("iata_code") or None,
            icao_code=raw.get("icao_code") or None,
            airport_name=raw.get("name", "") or "",
            municipality=raw.get("municipality") or None,
            country_code=raw.get("iso_country") or None,
            latitude_deg=_to_float(raw.get("latitude_deg")),
            longitude_deg=_to_float(raw.get("longitude_deg")),
        )
