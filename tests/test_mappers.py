import unittest
from mappers.base import Mapper
from mappers.mocksource import MockSourceOfferMapper
from mappers.openflights import OpenFlightsAirlineMapper, OpenFlightsRouteMapper
from mappers.ourairports import OurAirportsAirportMapper


class TestMappers(unittest.TestCase):

    def test_mocksource_offer_mapper(self):
        mapper = MockSourceOfferMapper()
        sample_data = {
            "record_id": "1",
            "offer_id": "OFFER1",
            "origin": "JFK",
            "destination": "LHR",
            "departure_at": "2026-05-01T10:00:00",
            "total_price": 500,
            "currency": "USD"
        }
        result = mapper.map_record("mocksource", sample_data)
        self.assertEqual(result.origin, "JFK")
        self.assertEqual(result.destination, "LHR")

    def test_openflights_airline_mapper(self):
        mapper = OpenFlightsAirlineMapper()
        sample_data = {
            "airline_id": "123",
            "name": "Test Airline",
            "iata": "TA",
            "icao": "TST",
            "callsign": "TEST",
            "country": "Testland",
            "active": "Y"
        }
        result = mapper.map_record("openflights", sample_data)
        self.assertEqual(result.airline_name, "Test Airline")
        self.assertEqual(result.iata_code, "TA")

    def test_openflights_route_mapper(self):
        mapper = OpenFlightsRouteMapper()
        sample_data = {
            "airline": "TA",
            "source_airport": "JFK",
            "destination_airport": "LHR",
            "stops": "0",
            "equipment": "777",
            "codeshare": "N"
        }
        result = mapper.map_record("openflights", sample_data)
        self.assertEqual(result.source_airport_code, "JFK")
        self.assertEqual(result.destination_airport_code, "LHR")

    def test_ourairports_airport_mapper(self):
        mapper = OurAirportsAirportMapper()
        sample_data = {
            "id": "789",
            "ident": "TEST",
            "iata_code": "TST",
            "icao_code": "TEST",
            "name": "Test Airport",
            "municipality": "Testville",
            "iso_country": "TL",
            "latitude_deg": "1.23",
            "longitude_deg": "4.56"
        }
        result = mapper.map_record("ourairports", sample_data)
        self.assertEqual(result.airport_name, "Test Airport")
        self.assertEqual(result.iata_code, "TST")

if __name__ == "__main__":
    unittest.main()