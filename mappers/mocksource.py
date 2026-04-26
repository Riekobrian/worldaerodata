from __future__ import annotations

from datetime import datetime

from mappers.base import Mapper
from models.canonical import FlightOfferCanonical


class MockSourceOfferMapper(Mapper):
    def map_record(self, source_name: str, raw: dict) -> FlightOfferCanonical:
        return FlightOfferCanonical(
            source=source_name,
            source_record_id=str(raw.get("record_id")),
            offer_id=str(raw.get("offer_id")),
            origin=str(raw.get("origin", "")).upper(),
            destination=str(raw.get("destination", "")).upper(),
            departure_at=datetime.fromisoformat(str(raw.get("departure_at"))),
            total_price=float(raw.get("total_price")),
            currency=str(raw.get("currency", "USD")).upper(),
        )
