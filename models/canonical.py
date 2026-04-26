from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AirportCanonical(BaseModel):
    source: str
    source_record_id: str
    ident: str = Field(min_length=1, max_length=12)
    iata_code: Optional[str] = Field(default=None, min_length=3, max_length=3)
    icao_code: Optional[str] = Field(default=None, min_length=4, max_length=4)
    airport_name: str = Field(min_length=1)
    municipality: Optional[str] = None
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    latitude_deg: Optional[float] = None
    longitude_deg: Optional[float] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("iata_code", "icao_code", "country_code")
    @classmethod
    def normalize_upper(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None


class AirlineCanonical(BaseModel):
    source: str
    source_record_id: str
    airline_name: str = Field(min_length=1)
    iata_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    icao_code: Optional[str] = Field(default=None, min_length=3, max_length=3)
    callsign: Optional[str] = None
    country_name: Optional[str] = None
    active: bool = True
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class RouteCanonical(BaseModel):
    source: str
    source_record_id: str
    airline_code: Optional[str] = None
    source_airport_code: str = Field(min_length=3, max_length=4)
    destination_airport_code: str = Field(min_length=3, max_length=4)
    stops: int = Field(ge=0, le=6)
    equipment: Optional[str] = None
    codeshare: bool = False
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("source_airport_code", "destination_airport_code", "airline_code")
    @classmethod
    def normalize_codes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None


class FlightStateCanonical(BaseModel):
    source: str
    source_record_id: str
    callsign: Optional[str] = None
    icao24: Optional[str] = None
    latitude_deg: Optional[float] = None
    longitude_deg: Optional[float] = None
    baro_altitude_m: Optional[float] = None
    velocity_m_s: Optional[float] = None
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class FlightOfferCanonical(BaseModel):
    source: str
    source_record_id: str
    offer_id: str = Field(min_length=1)
    origin: str = Field(min_length=3, max_length=4)
    destination: str = Field(min_length=3, max_length=4)
    departure_at: datetime
    total_price: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
