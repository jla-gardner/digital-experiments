from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, NamedTuple

from digital_experiments.util import complete_config, source_code


class Experiment:
    def __init__(
        self,
        function: Callable,
        backend: Backend,
        callbacks: list[Callback],
        cache: bool,
    ):
        self.function = function
        self.backend = backend
        self.callbacks = callbacks
        self.cache = cache

    def __repr__(self):
        return f"Experiment({self.function.__name__})"

    def __call__(self, *args, **kwargs):
        id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        config = complete_config(self.function, args, kwargs)
        metadata = {}

        if self.cache:
            for observation in self.observations(current_code_only=True):
                if observation.config == config:
                    return observation.result

        for callback in self.callbacks:
            callback.start(id, config)

        result = self.function(*args, **kwargs)

        observation = Observation(id, config, result, metadata)
        for callback in self.callbacks:
            callback.end(observation)

        self.backend.record(observation)
        return result

    def observations(self, current_code_only: bool = True) -> list[Observation]:
        observations = self.backend.load_all()
        if current_code_only:
            observations = [
                obs
                for obs in observations
                if obs.metadata.get("code") == source_code(self.function)
            ]
        return observations


class Observation(NamedTuple):
    id: str
    config: dict[str, Any]
    result: Any
    metadata: dict[str, Any]

    def __repr__(self):
        return f"Observation({self.id}, {self.config} → {self.result})"


class Callback:
    """
    Abstract base class for callbacks

    Subclass this class and override any of the hook methods
    to implement relevant, custom behaviour.
    """

    def setup(self, function: Callable) -> None:
        """Called when an `Experiment` is first created"""

    def start(self, id: str, config: dict[str, Any]) -> None:
        """Called at the start of each run of an `Experiment`"""

    def end(self, observation: Observation) -> None:
        """Called at the end of each run of an `Experiment`"""


class Backend(ABC):
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root

    @abstractmethod
    def record(self, observation: Observation) -> None:
        """Record an `Observation`"""

    @abstractmethod
    def load(self, id: str) -> Observation:
        """Load an `Observation` by its id"""

    @abstractmethod
    def all_ids(self) -> list[str]:
        """Return a list of all ids"""

    def load_all(self) -> list[Observation]:
        return [self.load(id) for id in self.all_ids()]
