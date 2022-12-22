import json
from abc import ABC, abstractclassmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

import pandas as pd

from digital_experiments.experiment import Experiment
from digital_experiments.util import flatten, pretty_json, unflatten


class Files:
    CODE = "code.py"
    BACKEND = ".backend"


class Backend(ABC):
    """
    Abstract Base Class for backends

    A backend is responsible for saving and loading experiments
    Implementations should subclass this class and implement the abstract methods
    Any core files (e.g. config.json) should be returned by the `core_files`
    """

    @abstractclassmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        pass

    @abstractclassmethod
    def _load_all_experiments(cls, root: Path) -> Iterable[Experiment]:
        pass

    @classmethod
    def core_files(self):
        return []

    @classmethod
    def all_experiments(cls, root: Path) -> List[Experiment]:
        experiments = cls._load_all_experiments(root)
        return sorted(experiments, key=lambda e: e.metadata["timing"]["start"])


class JSONBackend(Backend):
    @classmethod
    def core_files(cls):
        return ["config.json", "results.json", "metadata.json"]

    @classmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        (exmpt_dir / "config.json").write_text(pretty_json(config))
        (exmpt_dir / "results.json").write_text(pretty_json(result))
        (exmpt_dir / "metadata.json").write_text(pretty_json(metadata))

    @classmethod
    def _load_all_experiments(cls, root) -> List[Experiment]:
        def experiment_from(dir: Path):
            return Experiment(
                id=dir.name,
                config=json.loads((dir / "config.json").read_text()),
                result=json.loads((dir / "results.json").read_text()),
                metadata=json.loads((dir / "metadata.json").read_text()),
            )

        return [experiment_from(dir) for dir in root.iterdir() if dir.is_dir()]


class CSVBackend(Backend):
    @classmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        file = exmpt_dir.parent / "results.csv"
        previous_experiments = pd.read_csv(file) if file.exists() else pd.DataFrame()

        entry = flatten(
            {
                "id": exmpt_dir.name,
                "config": config,
                "result": result,
                "metadata": metadata,
            }
        )
        df = pd.concat((previous_experiments, pd.DataFrame([entry])))
        df.to_csv(file, index=False)

    @classmethod
    def _load_all_experiments(cls, root) -> pd.DataFrame:
        df = pd.read_csv(root / "results.csv")
        rows = [unflatten(row) for _, row in df.iterrows()]
        return [Experiment(**row) for row in rows]


__available_backends = {"json": JSONBackend, "csv": CSVBackend}


def register_backend(id: str, backend: Backend):
    if id in __available_backends:
        raise ValueError(f"Backend id already registered: {id}")
    __available_backends[id] = backend


def get_backend(backend_type: str) -> Backend:
    if backend_type in __available_backends:
        return __available_backends[backend_type]
    raise ValueError(f"Unknown backend id: {backend_type}")


def backend_used_for(root: Path):
    return get_backend((root / Files.BACKEND).read_text())


def id_for(backend: Backend) -> str:
    for id, b in __available_backends.items():
        if b == backend:
            return id
    raise ValueError(f"Unknown backend: {backend}")
