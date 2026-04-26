from __future__ import annotations

from abc import ABC, abstractmethod


class Mapper(ABC):
    @abstractmethod
    def map_record(self, source_name: str, raw: dict):
        raise NotImplementedError
