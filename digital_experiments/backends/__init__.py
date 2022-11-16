import json
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class Backend(ABC):
    @abstractmethod
    def save(self, id, config, result, metadata):
        pass


np_types = {
    "bool_": bool,
    "integer": int,
    "floating": float,
    "ndarray": list,
}


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        for np_type in np_types:
            if isinstance(obj, getattr(np, np_type)):
                return np_types[np_type](obj)
        return json.JSONEncoder.default(self, obj)


def pretty_json(thing):
    return json.dumps(thing, indent=4, cls=NpEncoder)


class JSONBackend(Backend):
    def __init__(self, root: str):
        self.root = Path(root)

    def save(self, id, config, result, metadata):
        root = self.root / id
        root.mkdir(parents=True, exist_ok=True)

        (root / "config.json").write_text(pretty_json(config))
        (root / "results.json").write_text(pretty_json(result))
        (root / "metadata.json").write_text(pretty_json(metadata))

    def load(self, id):
        root = self.root / id
        if not root.exists():
            raise FileNotFoundError(f"Experiment {id} not found")

        config = json.loads((root / "config.json").read_text())
        result = json.loads((root / "results.json").read_text())
        metadata = json.loads((root / "metadata.json").read_text())

        return config, result, metadata
