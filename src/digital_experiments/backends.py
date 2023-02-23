import contextlib
import shutil
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

from .control_center import Run
from .observation import Observation
from .util import flatten, generate_id, unflatten

__BACKENDS: Dict[str, "Backend"] = {}


def register_backend(name: str, cls: "Backend"):
    __BACKENDS[name] = cls
    cls.name = name
    return cls


def this_is_a_backend(name: str):
    return partial(register_backend, name)


def backend_from_type(backend_type: str):
    if backend_type not in __BACKENDS:
        raise ValueError(
            f"Unknown backend type {backend_type}. "
            f"Available backends are: {list(__BACKENDS.keys())}. "
            "Did you forget to register your backend using @this_is_a_backend?"
        )
    return __BACKENDS[backend_type]


class Backend(ABC):
    """
    Base class for a backend.

    A backend is repsponsible for saving and loading observations to
    a specific directory on disk.

    To implement a new backend, subclass this class and decorate it with
    @this_is_a_backend(<name>). You need to implement the following methods:
    - save
    - all_observations

    Any additional setup you want to do when the file structure for this
    backend is created, you can do in the create_new class method.

    The default structure of the file system in a backend is as follows:
    <home>
    ├── .code
    ├── .backend
    ├── observations.<format>
    └─── runs
        ├── <run_id>
        │   ├── <artefacts>
        │   ├── <artefacts>
        │   └── <artefacts>
        └── ...

    The .code file contains the experiment's code.
    The .backend file contains the name of the backend serves this directoty.
    """

    name: str

    def __init__(self, home: Path):
        if not hasattr(self, "name"):
            raise ValueError(
                "Ooops! You must decorate your backend "
                "class with @this_is_a_backend(<name>)"
            )
        assert home.exists(), f"{home} doesn't exist"
        assert (home / Files.BACKEND).read_text() == self.name, "wrong backend"
        self.home = home

    @abstractmethod
    def save(self, obs: Observation):
        """
        save an observation object to the backend
        """
        pass

    @abstractmethod
    def all_observations(self) -> List[Observation]:
        """
        load all observations from the backend
        """
        pass

    @classmethod
    def create_new(cls, location: Path, code: str):
        """
        Create a new backend at the given location.
        """
        assert not location.exists(), f"{location} already exists"
        location.mkdir(parents=True)
        (location / Files.RUNS).mkdir()
        (location / Files.BACKEND).write_text(cls.name)
        (location / Files.CODE).write_text(code)
        return cls(location)

    @contextlib.contextmanager
    def unique_run(self):
        id = generate_id()
        directory = self.home / Files.RUNS / id
        directory.mkdir(parents=True, exist_ok=False)

        run = Run(id, directory)
        yield run  # experiments happen while this is yielded
        if not any(run.directory.iterdir()):
            shutil.rmtree(run.directory)


@this_is_a_backend("yaml")
class YAMLBackend(Backend):
    @property
    def yaml_file(self):
        return self.home / "observations.yaml"

    def save(self, obs: Observation):
        with open(self.yaml_file, "a") as f:
            yaml.dump([obs], f, indent=2)

    def all_observations(self) -> List[Observation]:
        if not self.yaml_file.exists():
            return []
        with open(self.yaml_file) as f:
            return yaml.load(f, Loader=ObservationLoader)


class ObservationLoader(yaml.Loader):
    def construct_observation(self, node):
        data = self.construct_mapping(node)
        return Observation(**data)


@this_is_a_backend("csv")
class CSVBackend(Backend):
    SEPARATOR = "|"

    @property
    def csv_file(self):
        return self.home / "observations.csv"

    def save(self, obs: Observation):
        existing_observations = self.all_observations()
        existing_observations.append(obs)

        df = pd.DataFrame(
            [
                flatten(o.as_dict(), self.SEPARATOR)
                for o in existing_observations
            ],
        )
        df.to_csv(self.csv_file, index=False)

    def all_observations(self) -> List[Observation]:
        if not self.csv_file.exists():
            return []

        df = pd.read_csv(self.csv_file, dtype={"id": str})
        return [
            Observation(**unflatten(row, self.SEPARATOR))
            for _, row in df.iterrows()
        ]


class Files:
    CODE = ".code"
    BACKEND = ".backend"
    RUNS = "runs"
