from connectors.opensky import OpenSkyConnector
from models.flight_position import FlightPositionCanonical

class OpenSkyStateMapper:
    """
    Mapper for transforming OpenSky API data into canonical flight position models.
    """

    @staticmethod
    def map(state: list, source: str) -> FlightPositionCanonical:
        return FlightPositionCanonical(
            source=source,
            source_record_id=str(state[0]),
            callsign=state[1],
            origin_country=state[2],
            longitude=state[5],
            latitude=state[6],
            baro_altitude=state[7],
            velocity=state[9],
            heading=state[10],
            vertical_rate=state[11],
            on_ground=state[8],
            last_contact=state[4],
        )
