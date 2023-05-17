import pickle
import shutil
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

from .observation import Observation
from .util import dict_equality, exclusive_file_access, flatten, generate_id, unflatten

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


def available_backends():
    return list(__BACKENDS.keys())


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
    backend is created, you can do by extending the create_new class method.

    The default structure of the file system in a backend is as follows:
    <home>
    ├── .digital-experiment
    ├── observations.<format>
    └─── runs
        ├── <run_id>
        │   ├── <artefacts>
        │   ├── <artefacts>
        │   └── <artefacts>
        └── ...

    The .digital-experiment file labels this directory as containing a digital
    experiment. It contains the name of the backend that is used to store
    the experiment's data, and the code of the experiment.
    """

    name: str

    def __init__(self, home: Path):
        if not hasattr(self, "name"):
            raise ValueError(
                "Ooops! You must decorate your backend "
                "class with @this_is_a_backend(<name>)"
            )
        self.home = home

    @abstractmethod
    def save(self, obs: Observation):
        """
        save an observation object to the backend
        """

    @abstractmethod
    def all_observations(self) -> List[Observation]:
        """
        load all observations from the backend
        """

    @classmethod
    def create_new(cls, location: Path, code: str):
        """
        Create a new backend at the given location.
        """
        assert not location.exists(), f"{location} already exists"
        location.mkdir(parents=True)

        # label this directory as a digital experiment
        # and store various required metadata
        HomeLabel.create_new(location, cls.name, code)

        return cls(location)

    def unique_run(self):
        """
        Create a new unique run.
        """

        id = generate_id()
        directory = self.home / Files.RUNS / id
        directory.mkdir(parents=True, exist_ok=False)

        return id, directory

    def clean_up(self, id):
        """
        clean up after the run with the given id has finished
        """

        directory = self.home / Files.RUNS / id
        if not any(directory.iterdir()):
            shutil.rmtree(directory)

    @staticmethod
    def from_existing(home: Path):
        """
        Load an existing backend from the given location.
        """

        label = HomeLabel.from_existing(home)
        return backend_from_type(label.backend_name)(home)

    def _observations_for_(self, config):
        return [
            obs for obs in self.all_observations() if dict_equality(obs.config, config)
        ]


@this_is_a_backend("yaml")
class YAMLBackend(Backend):
    @property
    def yaml_file(self):
        return self.home / "observations.yaml"

    def save(self, obs: Observation):
        # append to the yaml file
        with exclusive_file_access(self.yaml_file, "a") as f:
            yaml.dump([obs], f, indent=2)

    def all_observations(self) -> List[Observation]:
        if not self.yaml_file.exists():
            return []
        with exclusive_file_access(self.yaml_file) as f:
            return yaml.load(f, Loader=yaml.Loader)


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
            [flatten(o.as_dict(), self.SEPARATOR) for o in existing_observations],
        )
        with exclusive_file_access(self.csv_file):
            df.to_csv(self.csv_file, index=False)

    def all_observations(self) -> List[Observation]:
        if not self.csv_file.exists():
            return []

        with exclusive_file_access(self.csv_file):
            df = pd.read_csv(self.csv_file, dtype={"id": str})

        return [
            Observation(**unflatten(row, self.SEPARATOR)) for _, row in df.iterrows()
        ]


@this_is_a_backend("pickle")
class PickleBackend(Backend):
    @property
    def observations_dir(self):
        return self.home / "observations"

    def save(self, obs: Observation):
        file = self.observations_dir / f"{obs.id}.pickle"
        file.parent.mkdir(parents=True, exist_ok=True)

        with exclusive_file_access(file, "wb") as f:
            pickle.dump(obs, f)

    def all_observations(self) -> List[Observation]:
        files = sorted(self.observations_dir.glob("*.pickle"))
        observations = []
        for f in files:
            with exclusive_file_access(f, "rb") as f:
                observations.append(pickle.load(f))
        return observations


class Files:
    LABEL = ".digital-experiment"
    RUNS = "runs"


@dataclass
class HomeLabel:
    """
    A class to label a directory as containing the results of a digital
    experiment.
    """

    backend_name: str
    code: str

    @classmethod
    def file_path(cls, home: Path):
        return home / Files.LABEL

    def save_to(self, home: Path):
        namespace = asdict(self)

        with open(self.file_path(home), "w") as f:
            yaml.dump(namespace, f, default_style="|")

    @classmethod
    def from_existing(cls, home: Path):
        with open(cls.file_path(home)) as f:
            namespace = yaml.safe_load(f)

        return cls(**namespace)

    @classmethod
    def create_new(cls, home: Path, backend_name: str, code: str):
        label = cls(backend_name, code)
        label.save_to(home)
        return label
