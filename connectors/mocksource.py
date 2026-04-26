from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from connectors.base import Connector


class MockSourceConnector(Connector):
    def fetch(self, source_config: dict) -> Iterable[dict]:
        path = Path(source_config["file_path"])
        with path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
