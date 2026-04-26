from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable

import requests

from connectors.base import Connector


class OurAirportsConnector(Connector):
    def fetch(self, source_config: dict) -> Iterable[dict]:
        url = source_config["dataset_url"]
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            yield row
