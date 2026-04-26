from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class Connector(ABC):
    @abstractmethod
    def fetch(self, source_config: dict) -> Iterable[dict]:
        raise NotImplementedError
