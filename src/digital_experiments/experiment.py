from functools import partial
from pathlib import Path
from typing import Dict, Union

from . import control_center as ControlCenter
from . import querying, timing
from .inspection import code_for, complete_config
from .observation import Observation
from .pretty import pretty_instance
from .version_control import get_or_create_backend_for


def experiment(
    experiment_fn=None,
    *,
    backend: str = "yaml",
    root: str = None,
    absolute_root: Union[str, Path] = None,
    verbose: bool = False,
    cache: bool = False,
):
    """
    decorator to record an experiment
    """
    if experiment_fn is None:
        kwargs = locals()
        kwargs.pop("experiment_fn")
        return partial(experiment, **kwargs)

    # get the directory of the file where the experiment is defined
    # and where <root> should be relative to
    expmt_file = Path(experiment_fn.__code__.co_filename).parent
    if "ipykernel" in str(expmt_file):
        expmt_file = Path(".")

    if absolute_root is None and root is None:
        final_root = expmt_file.resolve() / "experiments" / experiment_fn.__name__
    elif absolute_root:
        assert root is None, "Cannot specify both root and absolute_root"
        final_root = Path(absolute_root).resolve()
    else:
        final_root = expmt_file.resolve() / root

    return Experiment(experiment_fn, backend, final_root, verbose, cache)


class Experiment:
    def __init__(
        self,
        experiment: callable,
        backend: str,
        root: Path,
        verbose: bool = False,
        cache: bool = True,
    ):
        self._experiment = experiment
        self._backend = get_or_create_backend_for(root, code_for(experiment), backend)
        self.verbose = verbose
        self.cache = cache

    def run(self, args: list, kwargs: dict):
        """
        run the experiment with the given arguments and save the result
        """

        config = complete_config(self._experiment, args, kwargs)

        # check if we've run this experiment before
        previous_observations = self._backend._observations_for_(config)
        if self.cache and len(previous_observations) > 0:
            previous_observation = previous_observations[0]
            return previous_observation.result

        # if we're not recording, just run the experiment
        if not ControlCenter.should_record():
            return self._experiment(*args, **kwargs)

        # otherwise, run the experiment and record the result
        id, directory = self._backend.unique_run()
        ControlCenter.start_run(id, directory)
        self._log(f"Running experiment {id} with config: {config}")
        timing.mark("start")
        result = self._experiment(*args, **kwargs)
        timing.mark("end")
        self._log(f"Finished experiment {id} with result: {result}")
        finished_run = ControlCenter.end_run()
        self._backend.clean_up(id)

        observation = Observation(id, config, result, finished_run.metadata)
        self._backend.save(observation)

        return result

    def __call__(self, *args, **kwargs):
        return self.run(args, kwargs)

    def _log(self, msg):
        if self.verbose:
            print(f"digital-experiments: {self._experiment.__name__}: {msg}")

    @property
    def observations(self):
        return self._backend.all_observations()

    def observation_for(self, config: Dict):
        """
        return the observation for the given config
        """
        observations = self._backend._observations_for_(config)
        if len(observations) == 0:
            return None

        if len(observations) > 1:
            raise Exception(
                f"Found multiple observations for config {config}: {observations}"
            )
        return observations[0]

    def to_dataframe(
        self,
        include_metadata=False,
        include_id=True,
        config=None,
        metadata=None,
        result=None,
    ):
        filtered_observations = querying.filtered_observations(
            self.observations, config, metadata, result
        )
        return querying.to_dataframe(
            filtered_observations, include_id, include_metadata
        )

    def __repr__(self):
        return pretty_instance(
            "Experiment",
            self._experiment.__name__,
            observations=len(self.observations),
        )
