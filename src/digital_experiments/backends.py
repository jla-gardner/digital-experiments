from __future__ import annotations

import json
import pickle
from pathlib import Path

from .core import Backend, Observation

# Global state is isolated here:
_ALL_BACKENDS: dict[str, type[Backend]] = {}


def register_backend(name: str):
    def decorator(cls: type[Backend]):
        _ALL_BACKENDS[name] = cls
        return cls

    return decorator


def instantiate_backend(name: str, root: Path) -> Backend:
    if name not in _ALL_BACKENDS:
        raise ValueError(
            f"Unknown backend type {name}. "
            f"Available backends are: {list(_ALL_BACKENDS.keys())}. "
            "Did you forget to register your backend using @register_backend?"
        )
    return _ALL_BACKENDS[name](root)


@register_backend("json")
class JSONBackend(Backend):
    def record(self, observation: Observation) -> None:
        path = self.root / f"{observation.id}.json"
        with open(path, "w") as f:
            json.dump(observation._asdict(), f, indent=2)

    def load(self, id: str) -> Observation:
        path = self.root / f"{id}.json"
        with open(path) as f:
            return Observation(**json.load(f))

    def all_ids(self) -> list[str]:
        return [path.stem for path in self.root.glob("*.json")]


@register_backend("pickle")
class PickleBackend(Backend):
    def record(self, observation: Observation) -> None:
        path = self.root / f"{observation.id}.pkl"
        with open(path, "wb") as f:
            pickle.dump(observation, f)

    def load(self, id: str) -> Observation:
        path = self.root / f"{id}.pkl"
        with open(path, "rb") as f:
            return pickle.load(f)

    def all_ids(self) -> list[str]:
        return [path.stem for path in self.root.glob("*.pkl")]
