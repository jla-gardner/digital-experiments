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
    core_files = []

    def __init__(self, root: Path):
        self.root = root

    @abstractmethod
    def save(self, id, config, result, metadata):
        pass

    @abstractmethod
    def all_experiments(self) -> pd.DataFrame:
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
    core_files = ["config.json", "results.json", "metadata.json"]

    def save(self, id, config, result, metadata):
        root = self.root / id
        root.mkdir(parents=True, exist_ok=True)

        (root / "config.json").write_text(pretty_json(config))
        (root / "results.json").write_text(pretty_json(result))
        (root / "metadata.json").write_text(pretty_json(metadata))

    def all_experiments(self, metadata=False) -> pd.DataFrame:
        experiments = []
        for id in sorted(self.root.iterdir()):
            if not id.is_dir():
                continue
            config = json.loads((id / "config.json").read_text())
            result = json.loads((id / "results.json").read_text())
            if not isinstance(result, dict):
                result = {"result": result}
            if metadata:
                metadata = json.loads((id / "metadata.json").read_text())
            else:
                metadata = {}
            experiments.append({"id": id.name, **config, **result, **metadata})

        return pd.DataFrame([flatten(e) for e in experiments])


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

    def all_experiments(self, metadata=False):

        df = pd.read_csv(self.root / "results.csv")
        if metadata:
            return df

        key_map = json.loads((self.root / "headers.map").read_text())
        config = key_map["config"]
        result = key_map["result"]
        return df[["id"] + config + result]


def get_backend(root: str, backend: str = None):
    if backend is None:
        if (Path(root) / Files.BACKEND).exists():
            backend = (Path(root) / Files.BACKEND).read_text()
        else:
            backend = "json"

    if backend == "json":
        return JSONBackend(root)
    elif backend == "csv":
        return CSVBackend(root)
    else:
        raise ValueError(f"Unknown backend {backend}")
