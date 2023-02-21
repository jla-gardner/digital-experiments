from functools import partial
from pathlib import Path
from typing import Union

from . import control_center as GLOBAL
from . import querying
from .backends import backend_for
from .inspection import code_for, complete_config
from .metadata import record_metadata
from .observation import Observation
from .pretty import pretty_instance


def experiment(experiment_fn=None, *, backend: str = "yaml"):
    """
    decorator to record an experiment
    """
    if experiment_fn is None:
        return partial(experiment, backend=backend)
    return Experiment(experiment_fn, backend)


class Experiment:
    def __init__(
        self,
        experiment: callable,
        backend: str = "yaml",
        root: Union[str, Path] = None,
    ):
        self.experiment = experiment
        self._backend = backend_for(backend, experiment, root)

    def run(self, args: list, kwargs: dict):
        if not GLOBAL.should_record():
            return self.experiment(*args, **kwargs)

        config = complete_config(self.experiment, args, kwargs)

        with self._backend.unique_run() as run, GLOBAL.recording_run(run):
            id = run.id
            metadata, result = record_metadata(self.experiment, args, kwargs)

        observation = Observation(id, config, result, metadata)
        self._backend.save(observation)

        return result

    def __call__(self, *args, **kwargs):
        return self.run(args, kwargs)

    @property
    def observations(self):
        return self._backend.all_observations()

    def to_dataframe(self, *args, **kwargs):
        return querying.to_dataframe(self.observations, *args, **kwargs)

    def __repr__(self):
        return pretty_instance(
            "Experiment",
            self.experiment.__name__,
            observations=len(self.observations),
        )
