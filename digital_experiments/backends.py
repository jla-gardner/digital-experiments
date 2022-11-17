import json
from abc import ABC, abstractclassmethod, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

from digital_experiments.util import first, flatten, unflatten


class Files:
    CODE = "code.py"
    BACKEND = ".backend"


class Backend(ABC):
    core_files = []

    @property
    @abstractclassmethod
    def rep(cls) -> str:
        pass

    @abstractclassmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        pass

    @abstractmethod
    def all_experiments(self, root: Path, metadata: bool) -> pd.DataFrame:
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
    rep = "json"

    @classmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        exmpt_dir.mkdir(parents=True, exist_ok=True)
        (exmpt_dir / "config.json").write_text(pretty_json(config))
        (exmpt_dir / "results.json").write_text(pretty_json(result))
        (exmpt_dir / "metadata.json").write_text(pretty_json(metadata))

    @classmethod
    def all_experiments(cls, root, metadata=False) -> pd.DataFrame:
        experiments = []
        for id in sorted(root.iterdir()):
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
            experiments.append(
                {
                    "id": id.name,
                    "config": config,
                    "results": result,
                    "metadata": metadata,
                }
            )

        return pd.DataFrame([flatten(e) for e in experiments])


class CSVBackend(Backend):
    rep = "csv"

    @classmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        file = exmpt_dir.parent / "results.csv"
        if not isinstance(result, dict):
            result = {"result": result}
        entry = dict(
            id=exmpt_dir.name, config=config, results=result, metadata=metadata
        )
        entry = flatten(entry)

        if not file.exists():
            file.write_text(",".join(entry.keys()) + "\n")

        with open(file, "a") as f:
            f.write(",".join(map(str, entry.values())) + "\n")

    @classmethod
    def all_experiments(cls, root, metadata=False) -> pd.DataFrame:

        df = pd.read_csv(root / "results.csv")
        if metadata:
            return df

        return df.filter(regex="^(?!metadata)")


__available_backends = {b.rep: b for b in [JSONBackend, CSVBackend]}


def register_backend(backend: Backend):
    __available_backends[backend.rep()] = backend


def get_backend(backend_type: str) -> Backend:
    if backend_type in __available_backends:
        return __available_backends[backend_type]
    raise ValueError(f"Unknown backend {backend_type}")


def backend_used_for(root: Path):
    return get_backend((root / Files.BACKEND).read_text())
