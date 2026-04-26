import unittest
from models.canonical import AirlineCanonical, RouteCanonical, AirportCanonical, FlightOfferCanonical
from datetime import datetime
from pydantic import ValidationError

class TestCanonicalValidation(unittest.TestCase):
    def test_airline_canonical_valid(self):
        obj = AirlineCanonical(
            source="openflights",
            source_record_id="1",
            airline_name="Test Airline",
            iata_code="TA",
            icao_code="TST",
            callsign="TEST",
            country_name="Testland",
            active=True
        )
        self.assertEqual(obj.iata_code, "TA")

    def test_airline_canonical_invalid(self):
        with self.assertRaises(ValidationError):
            AirlineCanonical(
                source=None,
                source_record_id=None,
                airline_name=None,
                iata_code=None,
                icao_code=None,
                callsign=None,
                country_name=None,
                active=None
            )

    def test_route_canonical_valid(self):
        obj = RouteCanonical(
            source="openflights",
            source_record_id="1",
            airline_code="TA",
            source_airport_code="JFK",
            destination_airport_code="LHR",
            stops=0,
            equipment="777",
            codeshare=False
        )
        self.assertEqual(obj.source_airport_code, "JFK")

    def test_route_canonical_invalid(self):
        with self.assertRaises(ValidationError):
            RouteCanonical(
                source=None,
                source_record_id=None,
                airline_code=None,
                source_airport_code=None,
                destination_airport_code=None,
                stops=None,
                equipment=None,
                codeshare=None
            )

    def test_airport_canonical_valid(self):
        obj = AirportCanonical(
            source="ourairports",
            source_record_id="1",
            ident="TEST",
            iata_code="TST",
            icao_code="TEST",
            airport_name="Test Airport",
            municipality="Testville",
            country_code="TL",
            latitude_deg=1.23,
            longitude_deg=4.56
        )
        self.assertEqual(obj.airport_name, "Test Airport")

    def test_airport_canonical_invalid(self):
        with self.assertRaises(ValidationError):
            AirportCanonical(
                source=None,
                source_record_id=None,
                ident=None,
                iata_code=None,
                icao_code=None,
                airport_name=None,
                municipality=None,
                country_code=None,
                latitude_deg=None,
                longitude_deg=None
            )

    def test_flight_offer_canonical_valid(self):
        obj = FlightOfferCanonical(
            source="mocksource",
            source_record_id="1",
            offer_id="OFFER1",
            origin="JFK",
            destination="LHR",
            departure_at=datetime(2026, 5, 1, 10, 0, 0),
            total_price=500.0,
            currency="USD"
        )
        self.assertEqual(obj.origin, "JFK")

    def test_flight_offer_canonical_invalid(self):
        with self.assertRaises(ValidationError):
            FlightOfferCanonical(
                source=None,
                source_record_id=None,
                offer_id=None,
                origin=None,
                destination=None,
                departure_at=None,
                total_price=None,
                currency=None
            )

if __name__ == "__main__":
    unittest.main()
