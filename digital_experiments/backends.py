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

    A backend is responsible for saving and loading experiments. 
    Implementations should subclass this class and implement the abstract methods
    """

    @abstractclassmethod
    def save(
        cls,
        exmpt_dir: Path,
        config: Dict[str, Any],
        result: Union[Any, Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """
        Save an experiment to the given directory
        """
        pass

    @abstractclassmethod
    def load_all_experiments(cls, root: Path) -> Iterable[Experiment]:
        """
        Load all experiments from the given directory
        """
        pass

    @classmethod
    def core_files(cls):
        """
        Files created by this backend that should be ignored
        when querying artefacts etc.
        """
        return []

    @classmethod
    def all_experiments(cls, root: Path) -> List[Experiment]:
        experiments = cls.load_all_experiments(root)
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
        for name, content in {
            "config": config,
            "results": result,
            "metadata": metadata,
        }.items():
            (exmpt_dir / f"{name}.json").write_text(pretty_json(content))

    @classmethod
    def load_all_experiments(cls, root) -> List[Experiment]:
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
        previous_experiments = cls._previous_experiments(file.parent)

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
    def load_all_experiments(cls, root) -> pd.DataFrame:
        if not (root / "results.csv").exists():
            return []
        df = pd.read_csv(root / "results.csv")
        rows = [unflatten(row) for _, row in df.iterrows()]
        return [Experiment(**row) for row in rows]

    @classmethod
    def _previous_experiments(cls, root: Path) -> pd.DataFrame:
        file = root / "results.csv"
        if file.exists():
            return pd.read_csv(file)
        return pd.DataFrame()


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
