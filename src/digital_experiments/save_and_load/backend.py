import pickle
import shutil
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Type

import pandas as pd
import yaml

from digital_experiments.inspection import code_for
from digital_experiments.observation import Observation
from digital_experiments.util import ExistingPath

from ..observation import Observation
from ..util import dict_equality, exclusive_file_access, flatten, generate_id, unflatten

__BACKENDS: Dict[str, "Backend"] = {}


def register_backend(name: str, cls: "Backend"):
    __BACKENDS[name] = cls
    cls.name = name
    return cls


def this_is_a_backend(name: str):
    return partial(register_backend, name)


def backend_type_from_name(backend_type: str) -> Type["Backend"]:
    if backend_type not in __BACKENDS:
        raise ValueError(
            f"Unknown backend type {backend_type}. "
            f"Available backends are: {list(__BACKENDS.keys())}. "
            "Did you forget to register your backend using @this_is_a_backend?"
        )
    return __BACKENDS[backend_type]


def _available_backends():
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

    LABEL = ".digital-experiment"
    RUNS = "runs"

    def __init__(self, location: ExistingPath, code: str):
        if not hasattr(self, "name"):
            raise ValueError(
                "Ooops! You must decorate your backend "
                "class with @this_is_a_backend(<name>)"
            )
        self._location = location
        self._code = code
        self.__post_init__()

    def __post_init__(self):
        """
        This method is called after the backend has been initialized.

        Any additional setup you want to do when the file structure for this
        backend is created, you can do by extending this method.
        """

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
    def is_backend(cls, directory: Path) -> bool:
        """
        Check if the directory contains a digital experiment
        """

        # do this by checking if the directory contains a
        # .digital-experiment file
        return (directory / cls.LABEL).exists()

    @classmethod
    def create_new(cls, directory: Path, function: Callable):
        """
        Create a new backend in the given directory
        """

        # create the directory if it does not exist
        directory.mkdir(parents=True, exist_ok=True)

        code = code_for(function)

        # create the metadata
        metadata = BackendMetadata(code, cls.name)
        metadata.save_to_file(directory / cls.LABEL)

        # call the post init method
        return cls(directory, code)

    @classmethod
    def from_existing(cls, directory: ExistingPath):
        """
        Create a backend from an existing directory
        """

        if not cls.is_backend(directory):
            raise ValueError(
                f"The directory {directory} does not contain a digital experiment"
            )

        # load the metadata
        metadata = BackendMetadata.load_from_file(directory / cls.LABEL)

        # create the backend
        subclass = backend_type_from_name(metadata.backend_name)
        return subclass(directory, metadata.code)

    def is_for(self, function: Callable) -> bool:
        """
        Check if this backend is for a specific function
        """
        return self._code == code_for(function)

    def _observations_for_(self, config):
        return [
            obs for obs in self.all_observations() if dict_equality(obs.config, config)
        ]

    def unique_run(self):
        """
        Create a new unique run.
        """

        id = generate_id()
        directory = self._location / self.RUNS / id
        directory.mkdir(parents=True, exist_ok=False)

        return id, directory

    def clean_up(self, id):
        """
        clean up after the run with the given id has finished
        """

        directory = self._location / self.RUNS / id
        if not any(directory.iterdir()):
            shutil.rmtree(directory)


@dataclass
class BackendMetadata:
    code: str
    backend_name: str

    def save_to_file(self, path: Path):
        with open(path, "w") as f:
            yaml.dump(asdict(self), f, default_style="|")

    @classmethod
    def load_from_file(cls, path: ExistingPath) -> "BackendMetadata":
        with open(path, "r") as f:
            return cls(**yaml.safe_load(f))


@this_is_a_backend("yaml")
class YAMLBackend(Backend):
    @property
    def yaml_file(self):
        return self._location / "observations.yaml"

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
        return self._location / "observations.csv"

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
        return self._location / "observations"

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
