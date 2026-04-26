import time
import requests
from typing import Any, Dict, List

class OpenSkyConnector:
    """
    Connector for fetching live flight data from OpenSky Network API.
    """

    BASE_URL = "https://opensky-network.org/api/states/all"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.last_request_time = 0
        self.rate_limit_interval = 10  # OpenSky allows 1 request per 10 seconds for anonymous users

    def fetch_states(self) -> List[Dict[str, Any]]:
        """
        Fetch live flight states from OpenSky API.
        """
        self.rate_limit_guard()
        response = requests.get(self.BASE_URL, auth=(self.client_id, self.client_secret))
        if response.status_code == 200:
            data = response.json()
            return data.get("states", [])
        else:
            response.raise_for_status()

    def rate_limit_guard(self):
        """
        Ensure compliance with OpenSky's rate limiting policy.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_interval:
            time.sleep(self.rate_limit_interval - elapsed)
        self.last_request_time = time.time()
