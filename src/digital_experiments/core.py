from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, NamedTuple

from .util import artefact_location, complete_config, source_code


class Experiment:
    r"""
    An Experiment object wraps a function and records its results.

    The resulting object can be called identically to the original function,
    but has the additional `observations` method, which returns a list of
    `Observation` objects corresponding to previous runs of the function,
    in this (and previous) Python sessions.

    See :func:`@experiment <digital_experiments.experiment>` for the intended
    entry point to this class.
    """

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
        for callback in reversed(self.callbacks):
            callback.end(observation)

        self.backend.record(observation)
        return result

    def observations(self, current_code_only: bool = True) -> list[Observation]:
        """
        Get a list of all previous observations of this experiment. By default,
        this will include observations from previous Python sessions.

        Parameters
        ----------
        current_code_only : bool
            Whether to only return observations from the current
            version of the code. Defaults to True.

        Example
        -------

        .. code-block:: python

            @experiment
            def example(a, b=2):
               return a + b

            example(1)  # returns 3

            example.observations()
            # returns [Observation(<id>, {'a': 1, 'b': 2} → 3)]

        """

        observations = self.backend.load_all()
        if current_code_only:
            observations = [
                obs
                for obs in observations
                if obs.metadata.get("code") == source_code(self.function)
            ]
        return observations

    def artefacts(self, id: str) -> list[Path]:
        """
        Get a list of artefacts associated with a particular observation.

        Add artefacts to an experiment run by writing any and all files
        to the path returned by
        :meth:`current_dir <digital_experiments.current_dir>`

        Parameters
        ----------
        id : str
            The id of the observation to get artefacts for

        Example
        -------

        .. code-block:: python

            from digital_experiments import experiment, current_dir

            @experiment
            def example():
               (current_dir() / "results.txt").write_text("hello world")

            example()
            id = example.observations()[-1].id
            example.artefacts(id)
            # returns [Path("<some>/<path>/<id>/results.txt")]
        """

        return self.backend.artefacts(id)

    def to_dataframe(
        self,
        current_code_only: bool = True,
        include_metadata: bool = False,
        normalising_sep: str = ".",
    ):
        """
        Get a pandas DataFrame containing all observations of this experiment.

        The resulting DataFrame is in "long" format, with one row per
        observation, and "normalised" (see :func:`pandas.json_normalize`) so
        that nested dict-like objects (including config, results and metadata)
        are flattened and cast into multiple columns.

        Parameters
        ----------
        current_code_only : bool
            Whether to only return observations from the current
            version of the code. Defaults to True.
        include_metadata : bool
            Whether to include metadata in the DataFrame. Defaults to False.
        normalising_sep : str
            The separator to use when normalising nested dictionaries.
            Defaults to ".".

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing all observations of this experiment.
            If pandas is not installed, this will raise an ImportError.

        Example
        -------
        .. code-block:: python

            >>> @experiment
            ... def example(a, b=2):
            ...    return a + b

            >>> example(1)
            3
            >>> example.to_dataframe()
               id  config.a  config.b  result
            0   1         1         2       3
        """

        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "Please install pandas to use this method."
            ) from e

        observations = self.observations(current_code_only)
        if not observations:
            return pd.DataFrame()

        dicts = [obs._asdict() for obs in observations]
        if not include_metadata:
            for d in dicts:
                d.pop("metadata")

        return pd.json_normalize(dicts, sep=normalising_sep)


class Observation(NamedTuple):
    """
    Container for a single observation of an `Experiment`.

    Each observation is composed of a unique id, the complete configuration
    (args, kwargs and defaults) used to run the experiment, the returned
    result, and a dictionary of metadata.

    Parameters
    ----------
    id : str
        A unique identifier for this observation
    config : dict[str, Any]
        The configuration passed to the experiment to produce this
        observation
    result : Any
        The result of the experiment
    metadata : dict[str, Any]
        A dictionary of metadata about the observation
    """

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
        """Called when an experiment is first created."""

    def start(self, id: str, config: dict[str, Any]) -> None:
        """Called at the start of each run of an experiment."""

    def end(self, observation: Observation) -> None:
        """
        Called at the end of each run of an experiment. Callbacks typically
        modify ``observation.metadata`` to record additional information.
        """


class Backend(ABC):
    """
    Abstract base class for backends.

    A backend is responsible for recording and loading
    :class:`Observation <digital_experiments.core.Observation>` objects.
    All subclasses must override the :meth:`record`, :meth:`load`, and
    :meth:`all_ids` methods.

    Other methods are optional, but can be overridden to provide
    further custom behaviour.
    """

    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root

    @abstractmethod
    def record(self, observation: Observation) -> None:
        """
        Record an :class:`Observation <digital_experiments.core.Observation>`
        """

    @abstractmethod
    def load(self, id: str) -> Observation:
        """
        Load an :class:`Observation <digital_experiments.core.Observation>`
        by its id
        """

    @abstractmethod
    def all_ids(self) -> list[str]:
        """Return a list of all ids currently stored in this backend"""

    def load_all(self) -> list[Observation]:
        """
        Load all :class:`Observation <digital_experiments.core.Observation>`
        objects currently stored in this backend, sorted by id.
        """

        observations = [self.load(id) for id in self.all_ids()]
        return sorted(observations, key=lambda obs: obs.id)

    def artefacts(self, id: str) -> list[Path]:
        """
        Get a list of artefacts associated with a particular observation.

        Parameters
        ----------
        id : str
            The id of the observation to get artefacts for
        """

        dir = artefact_location(self.root, id)
        if not dir.exists():
            return []
        return list(dir.glob("*"))


class Controller(ABC):
    """
    Abstract base class for experiment controllers.

    A controller is responsible for:

    - suggesting experiments to run next
    - running them

    Subclasses must override the :meth:`suggest` method.
    """

    @abstractmethod
    def suggest(self, experiment: Experiment) -> dict[str, Any] | None:
        """
        Suggest a configuration for the next experiment to run.

        Parameters
        ----------
        experiment : Experiment
            The experiment to suggest a configuration for

        Returns
        -------
        dict[str, Any] | None
            The suggested configuration, or None if no further experiments
            are required.
        """

    def control(self, experiment: Experiment, n: int = 1, **overloads) -> None:
        """
        Run an experiment using this controller.

        Parameters
        ----------
        experiment : Experiment
            The experiment to run
        n : int
            The number of experiments to run. Defaults to 1.
        overloads : dict[str, Any]
            A dictionary of additional keyword arguments to pass to
            each experiment.
        """

        for _ in range(n):
            config = self.suggest(experiment)
            if config is None:
                break
            config.update(overloads)
            experiment(**config)
