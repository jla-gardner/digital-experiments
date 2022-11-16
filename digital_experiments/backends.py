import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from digital_experiments.util import first, flatten, unflatten


class Files:
    CODE = "code.py"
    BACKEND = ".backend"


class Backend(ABC):
    def __init__(self, root: Path):
        self.root = root

    @abstractmethod
    def core_files(self, id: str) -> List[Path]:
        pass

    @abstractmethod
    def save(self, id, config, result, metadata):
        pass

    @abstractmethod
    def load(self, id):
        pass

    @abstractmethod
    def all_ids(self):
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

    def all_ids(self):
        return sorted(f.name for f in self.root.iterdir() if f.is_dir())

    def core_files(self, id):
        return [
            self.root / id / f for f in ["config.json", "results.json", "metadata.json"]
        ]


class CSVBackend(Backend):
    def save(self, id, config, result, metadata):
        file = self.root / "results.csv"
        if not isinstance(result, dict):
            result = {"result": result}
        entry = dict(id=id, **config, **result, **metadata)
        entry = flatten(entry)

        if not file.exists():
            file.write_text(",".join(entry.keys()) + "\n")
            (self.root / "headers.map").write_text(
                pretty_json(
                    {
                        "config": list(flatten(config).keys()),
                        "result": list(flatten(result).keys()),
                        "metadata": list(flatten(metadata).keys()),
                    }
                )
            )
        with open(file, "a") as f:
            f.write(",".join(map(str, entry.values())) + "\n")

    def load(self, id):
        key_map = json.loads((self.root / "headers.map").read_text())

        df = pd.read_csv(self.root / "results.csv")
        entry = dict(df[df["id"] == id].iloc[0])

        config = {key: entry[key] for key in key_map["config"]}
        result = {key: entry[key] for key in key_map["result"]}
        if key_map["result"] == ["result"]:
            result = result["result"]
        metadata = {key: entry[key] for key in key_map["metadata"]}
        return unflatten(config), unflatten(result), unflatten(metadata)

    def all_ids(self):
        lines = (self.root / "results.csv").read_text().splitlines()
        return [line.split(",")[0] for line in lines[1:]]

    def core_files(self, id):
        return [self.root / "results.csv", self.root / "headers.map"]


def get_backend(root: str, backend: str = "json"):
    if backend == "json":
        return JSONBackend(root)
    elif backend == "csv":
        return CSVBackend(root)
    else:
        raise ValueError(f"Unknown backend {backend}")
