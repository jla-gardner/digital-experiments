import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import List

from digital_experiments.util import merge_dicts

# GLOBAL STATE to de/activate experiment recording
__RECORDING: bool = True


@contextlib.contextmanager
def dont_record():
    global __RECORDING
    __RECORDING = False
    yield
    __RECORDING = True


def should_record():
    return __RECORDING


@dataclass
class Run:
    id: str
    directory: Path
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


__CURRENTLY_RUNNING: List[Run] = []
__METADATA_CONTEXTS: List[dict] = []


def current_run():
    """
    get the currently running experiment
    """
    if len(__CURRENTLY_RUNNING) == 0:
        raise Exception("No experiment is currently running")
    return __CURRENTLY_RUNNING[-1]


def current_directory():
    """
    get the directory assigned to the currently running experiment
    """
    current_run().directory


@contextlib.contextmanager
def additional_metadata(metadata: dict):
    """
    call outside of an experiment to register additional metadata

    Example:
    --------
    >>> with additional_metadata({"foo": "bar"}):
    ...     my_experiment()
    >>> observation = my_experiment.observations[-1]
    >>> observation.metadata["foo"]
    "bar"
    """

    __METADATA_CONTEXTS.append(metadata)
    yield  # experiments happen here
    __METADATA_CONTEXTS.pop()


def add_metadata(metadata: dict):
    """
    call inside of an experiment to add to metadata

    Example:
    --------
    >>> @experiment
    >>> def my_experiment():
    ...     add_metadata({"foo": "bar"})
    ...     return 42
    >>> my_experiment()
    42
    >>> observation = my_experiment.observations[-1]
    >>> observation.metadata["foo"]
    "bar"
    """

    if len(__CURRENTLY_RUNNING) == 0:
        raise RuntimeError("add_metadata called outside of an experiment")
    run = __CURRENTLY_RUNNING[-1]
    current_metadata = run.metadata
    run.metadata = merge_dicts(current_metadata, metadata)


def start_run(id: str, directory: Path):
    """
    start a new run with the given id and directory

    gather all currently active metadata contexts
    and merge them into the run's metadata
    """
    metadata = {}
    for context in __METADATA_CONTEXTS:
        metadata = merge_dicts(metadata, context)

    run = Run(id, directory, metadata)
    __CURRENTLY_RUNNING.append(run)


def end_run():
    if len(__CURRENTLY_RUNNING) == 0:
        raise RuntimeError("end_run called when no experiment is running")
    return __CURRENTLY_RUNNING.pop()
