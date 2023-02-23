from functools import partial
from pathlib import Path
from typing import Union

from . import control_center as GLOBAL
from . import querying
from .inspection import code_for, complete_config
from .metadata import record_metadata
from .observation import Observation
from .pretty import pretty_instance
from .version_control import get_or_create_backend_for


def experiment(
    experiment_fn=None,
    *,
    backend: str = "yaml",
    root: str = None,
    absolute_root: Union[str, Path] = None
):
    """
    decorator to record an experiment
    """
    if experiment_fn is None:
        return partial(
            experiment, backend=backend, root=root, absolute_root=absolute_root
        )

    # get the directory of the file where the experiment is defined
    # and where <root> should be relative to
    expmt_file = Path(experiment_fn.__code__.co_filename).parent
    if "ipykernel" in str(expmt_file):
        expmt_file = Path(".")

    if absolute_root is None and root is None:
        final_root = (
            expmt_file.resolve() / "experiments" / experiment_fn.__name__
        )
    elif absolute_root:
        assert root is None, "Cannot specify both root and absolute_root"
        final_root = Path(absolute_root).resolve()
    else:
        final_root = expmt_file.resolve() / root

    return Experiment(experiment_fn, backend, final_root)


class Experiment:
    def __init__(
        self,
        experiment: callable,
        backend: str,
        root: Path,
    ):
        self._experiment = experiment
        self._backend = get_or_create_backend_for(
            root, code_for(experiment), backend
        )

    def run(self, args: list, kwargs: dict):
        if not GLOBAL.should_record():
            return self._experiment(*args, **kwargs)

        config = complete_config(self._experiment, args, kwargs)

        with self._backend.unique_run() as run, GLOBAL.recording_run(run):
            id = run.id
            metadata, result = record_metadata(self._experiment, args, kwargs)

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
            self._experiment.__name__,
            observations=len(self.observations),
        )
