from dataclasses import dataclass
from typing import Any

from .pretty import pretty_instance


@dataclass
class Observation:
    id: str
    config: dict
    result: Any
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def as_dict(self):
        return {
            "id": self.id,
            "config": self.config,
            "result": self.result,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return pretty_instance(
            "Observation",
            config=self.config,
            result=self.result,
        )
