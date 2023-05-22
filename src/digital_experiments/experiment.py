import inspect
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Type, Union

from digital_experiments.util import get_passed_kwargs, interpret

from . import control_center as ControlCenter
from . import querying, timing
from .inspection import complete_config
from .observation import Observation
from .pretty import pretty_instance
from .save_and_load.backend import Backend, backend_type_from_name
from .save_and_load.home import Home


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

    home = Home(final_root)
    backend_type = backend_type_from_name(backend)
    return Experiment(experiment_fn, home, backend_type, verbose, cache)


class Experiment:
    def __init__(
        self,
        experiment_fn: Callable,
        home: Home,
        backend_type: Type[Backend],
        verbose: bool = False,
        cache: bool = True,
    ):
        self._experiment_fn = experiment_fn
        self._home = home
        self._backend_type = backend_type
        self.verbose = verbose
        self.cache = cache

    def run(self, args: list, kwargs: dict):
        """
        run the experiment with the given arguments and save the result
        """

        config = complete_config(self._experiment_fn, args, kwargs)
        backend = self.get_backend()

        # check if we've run this experiment before
        previous_observations = backend._observations_for_(config)
        if self.cache and len(previous_observations) > 0:
            previous_observation = previous_observations[0]
            return previous_observation.result

        # if we're not recording, just run the experiment
        if not ControlCenter.should_record():
            return self._experiment_fn(*args, **kwargs)

        # otherwise, run the experiment and record the result
        id, directory = backend.unique_run()
        ControlCenter.start_run(id, directory)
        self._log(f"Running experiment {id} with config: {config}")
        timing.mark("start")
        result = self._experiment_fn(*args, **kwargs)
        timing.mark("end")
        self._log(f"Finished experiment {id} with result: {result}")
        finished_run = ControlCenter.end_run()
        backend.clean_up(id)

        observation = Observation(id, config, result, finished_run.metadata)
        backend.save(observation)

        return result

    def get_backend(self):
        return self._home.backend_for(self._experiment_fn, self._backend_type)

    def __call__(self, *args, **kwargs):
        return self.run(args, kwargs)

    def _log(self, msg):
        if self.verbose:
            print(f"digital-experiments: {self._experiment_fn.__name__}: {msg}")

    @property
    def observations(self):
        return self.get_backend().all_observations()

    def observation_for(self, config: Dict):
        """
        return the observation for the given config
        """
        observations = self.get_backend()._observations_for_(config)
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
        include_id=False,
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
            self._experiment_fn.__name__,
            observations=len(self.observations),
        )


def get_passed_kwargs_for(experiment: Experiment):
    kwargs: Dict[str, str] = get_passed_kwargs()

    relevant_kwargs = {}
    signature = inspect.signature(experiment._experiment_fn)
    for k, v in kwargs.items():
        if k in signature.parameters:
            relevant_kwargs[k] = interpret(v, signature.parameters[k])

    return relevant_kwargs
