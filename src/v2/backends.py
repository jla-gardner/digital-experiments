import contextlib
import shutil
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from typing import Dict, List, Union

import yaml

from .control_center import Run
from .inspection import code_for
from .observation import Observation
from .util import generate_id

__BACKENDS: Dict[str, "Backend"] = {}


def backend_for(
    backend: str, experiment_fn, root: Union[str, Path] = None
) -> "Backend":
    if backend not in __BACKENDS:
        raise ValueError(f"Unknown backend: {backend}")
    return __BACKENDS[backend](experiment_fn, root=root)


def register_backend(name: str, cls: "Backend"):
    __BACKENDS[name] = cls
    cls.name = name
    return cls


def this_is_a_backend(name: str):
    return partial(register_backend, name)


class Backend(ABC):
    """
    To implement a new backend, subclass this class and decorate it with
    @this_is_a_backend(<name>). You need to implement the following methods:
    - save
    - all_observations


    general structure of the file system:

    <root>
    ├── version-1
    │   ├── .code
    │   ├── .backend
    │   ├── observations.<backend>
    │   └── runs
    │       └── 23.02.21-15.09.15-477669
    │           └── <artefacts...>
    └── version-2/...
    """

    name: str

    def __init__(self, experiment_fn, root: Union[str, Path] = None):
        self.root = Path(root or experiment_fn.__name__)
        self.experiment_fn = experiment_fn
        self._currently_running = []
        self._lazy_home = None

    @property
    def home(self) -> Path:
        # lazily creating the home directory ensures that
        # we only add to the file system if we actually record
        if self._lazy_home is None:
            self._lazy_home = self._setup_and_version_control()
        return self._lazy_home

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

    def _setup_and_version_control(self) -> Path:
        """
        if the experiment has never been run before, or the code has changed,
        we create a new version of the experiment.
        this contains .code, .backend, and runs/

        <root>
        ├── version-1
        │   ├── .code
        │   ├── .backend
        │   ├── observations.<backend>
        │   └── runs/...
        └── version-2/... (or another name - this should be editable by a human)
        """

        current_code = code_for(self.experiment_fn)

        def setup(home: Path):
            home.mkdir(parents=True)
            (home / "runs").mkdir()
            (home / Files.CODE).write_text(current_code)
            (home / Files.BACKEND).write_text(self.name)
            return home

        if not self.root.exists():
            return setup(self.root / "version-1")

        existing_versions = [
            file.parent.name for file in self.root.glob(f"**/{Files.CODE}")
        ]

        for version in existing_versions:
            home = self.root / version
            if (home / Files.CODE).read_text() == current_code:
                return home

        version_numbers = [
            int(version.split("-")[-1])
            for version in existing_versions
            if "version-" in version
        ]
        new_number = max(version_numbers, default=0) + 1
        return setup(self.root / f"version-{new_number}")

    def _start_run(self):

        id = generate_id()
        directory = self.home / "runs" / id
        directory.mkdir(parents=True, exist_ok=True)

        run = Run(id, directory)
        self._currently_running.append(run)
        return run

    def _end_run(self, run: Run):
        assert run == self._currently_running[-1]
        self._currently_running.pop()
        if not any(run.directory.iterdir()):
            shutil.rmtree(run.directory)

    @contextlib.contextmanager
    def unique_run(self):
        run = self._start_run()
        yield run
        self._end_run(run)


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


class Files:
    CODE = ".code"
    BACKEND = ".backend"
