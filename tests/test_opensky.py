import unittest
from unittest.mock import patch, MagicMock
from connectors.opensky import OpenSkyConnector
from mappers.opensky import OpenSkyStateMapper
from models.flight_position import FlightPositionCanonical

class TestOpenSkyConnector(unittest.TestCase):
    @patch("connectors.opensky.requests.get")
    def test_fetch_states(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"states": [["123", "CALLSIGN", "USA", None, 1650912345, -77.0364, 38.8951, 1000, False, 250, 180, 0]]}
        mock_get.return_value = mock_response

        connector = OpenSkyConnector("client_id", "client_secret")
        states = connector.fetch_states()

        self.assertEqual(len(states), 1)
        self.assertEqual(states[0][0], "123")

class TestOpenSkyStateMapper(unittest.TestCase):
    def test_map(self):
        state = ["123", "CALLSIGN", "USA", None, 1650912345, -77.0364, 38.8951, 1000, False, 250, 180, 0]
        mapped = OpenSkyStateMapper.map(state, "opensky")

        self.assertIsInstance(mapped, FlightPositionCanonical)
        self.assertEqual(mapped.source, "opensky")
        self.assertEqual(mapped.callsign, "CALLSIGN")
        self.assertEqual(mapped.longitude, -77.0364)
        self.assertEqual(mapped.latitude, 38.8951)

if __name__ == "__main__":
    unittest.main()
