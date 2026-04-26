from pydantic import BaseModel
from typing import Optional

class FlightPositionCanonical(BaseModel):
    source: str
    source_record_id: str
    callsign: Optional[str]
    origin_country: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    baro_altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]
    vertical_rate: Optional[float]
    on_ground: Optional[bool]
    last_contact: Optional[int]  # Unix timestamp
