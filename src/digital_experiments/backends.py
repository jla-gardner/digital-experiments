from __future__ import annotations

import json
import pickle
from pathlib import Path

import yaml

from .core import Backend, Observation

# Global state is isolated here:
_ALL_BACKENDS: dict[str, type[Backend]] = {}


def register_backend(name: str):
    """
    Use this decorator (along with subclassing :class:`Backend`) to register
    a new custom backend.

    Example
    -------
    .. code-block:: python

        from digital_experiments import register_backend, Backend

        @register_backend("my-backend")
        class MyBackend(Backend):
            ...

        @experiment(backend="my-backend")
        def my_experiment():
            ...
    """

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


@register_backend("pickle")
class PickleBackend(Backend):
    """
    The default backend for storing results.

    Each observation is stored in ``<root>/<id>.pkl``. The result and
    configuration of each observation can be (almost) any python object,
    provided it can be pickled.
    """

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


@register_backend("json")
class JSONBackend(Backend):
    """
    Each observation is stored in ``<root>/<id>.json``. The result and
    configuration of each observation must be JSON-serializable to
    use this backend.

    Select this backed using ``@experiment(backend="json")``.
    """

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


def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)


@register_backend("yaml")
class YAMLBackend(Backend):
    """
    Each observation is stored in ``<root>/<id>.yaml``. The result and
    configuration of each observation must be YAML-serializable to
    use this backend.

    Select this backed using ``@experiment(backend="yaml")``.
    """

    def record(self, observation: Observation) -> None:
        path = self.root / f"{observation.id}.yaml"
        with open(path, "w") as f:
            yaml.dump(observation._asdict(), f, indent=2)

    def load(self, id: str) -> Observation:
        path = self.root / f"{id}.yaml"
        with open(path) as f:
            return Observation(**yaml.load(f, Loader=yaml.Loader))

    def all_ids(self) -> list[str]:
        return [path.stem for path in self.root.glob("*.yaml")]
