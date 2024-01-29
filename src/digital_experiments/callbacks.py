from __future__ import annotations

import contextlib
import functools
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypedDict

from .core import Callback, Observation
from .util import artefact_location, source_code

# Global state is isolated here:
_RUNNING_IDS: list[str] = []
_CURRENT_ROOT: list[Path] = []
_TIMING_BLOCKS: list[dict[str, TimingBlock]] = []


class GlobalStateNotifier(Callback):
    """
    Responsible for updating the global state used for accessing information
    about the currently running experiment
    """

    def __init__(self, root: Path):
        self.root = root

    def start(self, id: str, config: dict[str, Any]):
        _RUNNING_IDS.append(id)
        _CURRENT_ROOT.append(self.root)

    def end(self, observation: Observation):
        _RUNNING_IDS.pop()
        _CURRENT_ROOT.pop()


def current_id() -> str:
    """
    Get the id of the currently running experiment.

    Example
    -------

    .. code-block:: python

            from digital_experiments import experiment, current_id

            @experiment
            def example():
                print(current_id())

            example() # prints something like "2021-01-01_12:00:00.000000"
    """

    if len(_RUNNING_IDS) == 0:
        raise RuntimeError(
            "No experiment running - this function only works "
            "inside an experiment context"
        )
    return _RUNNING_IDS[-1]


def current_dir() -> Path:
    """
    Get the directory of the currently running experiment.

    Use this function within an experiment to get a unique directory
    per experiment run to store results in. Anything stored in this
    directory can be accessed later using the
    :meth:`artefacts <digital_experiments.core.Experiment.artefacts>` method.

    Example
    -------

    .. code-block:: python

        from digital_experiments import experiment, current_dir

        @experiment
        def example():
            (current_dir() / "results.txt").write_text("hello world")

        example()
        id = example.observations()[-1].id
        example.artefacts(id) # returns [Path("<some>/<path>/<id>/results.txt")]
    """

    if len(_CURRENT_ROOT) == 0:
        raise RuntimeError(
            "No experiment running - this function only works "
            "inside an experiment context"
        )
    root = _CURRENT_ROOT[-1]
    id = current_id()
    dir = artefact_location(root, id)
    dir.mkdir(parents=True, exist_ok=True)
    return dir


class Logging(Callback):
    """Responsible for (optional) logging of experiments"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def start(self, id: str, config: dict[str, Any]):
        if self.verbose:
            print(f"starting experiment {id} with config {config}")

    def end(self, observation: Observation):
        if not self.verbose:
            return

        value = str(observation.result)
        if len(value) > 100:
            value = value[:50] + "..." + value[-50:]
        print(f"finished experiment {observation.id} with result {value}")


class CodeVersioning(Callback):
    """Responsible for recording the code of the experiment"""

    def setup(self, function: Callable) -> None:
        self.code = source_code(function)

    def end(self, observation: Observation):
        observation.metadata["code"] = self.code


class TimingBlock(TypedDict):
    start: str
    end: str
    duration: float


def _timing_block(start: datetime, end: datetime) -> TimingBlock:
    return TimingBlock(
        start=start.strftime("%Y-%m-%d %H:%M:%S"),
        end=end.strftime("%Y-%m-%d %H:%M:%S"),
        duration=(end - start).total_seconds(),
    )


class Timing(Callback):
    """Responsible for timing (portions of) experiments"""

    def start(self, id: str, config: dict[str, Any]):
        self.start_time = datetime.now()
        _TIMING_BLOCKS.append({})

    def end(self, observation: Observation):
        end_time = datetime.now()
        blocks = _TIMING_BLOCKS.pop()
        blocks["total"] = _timing_block(self.start_time, end_time)

        observation.metadata["timing"] = blocks


@contextlib.contextmanager
def time_block(name: str):
    """
    Time the code that runs inside this context manager.

    The start, end and duration are added into ``metadata["timing"][name]``
    of the currently active experiment.

    Parameters
    ----------
    name : str
        The name of the timing block

    Example
    -------

    .. code-block:: python

        import time
        from digital_experiments import experiment, time_block

        @experiment
        def example():
            with time_block("custom-block"):
                time.sleep(1)

        example()
        example.observations[-1].metadata["timing"]["custom-block"]
        # returns something like:
        # {
        #     "start": "2021-01-01 12:00:00",
        #     "end": "2021-01-01 12:00:01",
        #     "duration": 1.0,
        # }
    """

    if len(_TIMING_BLOCKS) == 0:
        raise RuntimeError(
            "No experiment running - this function only works "
            "inside an experiment context"
        )

    start = datetime.now()
    yield
    end = datetime.now()
    _TIMING_BLOCKS[-1][name] = _timing_block(start, end)


class Tee:
    def __init__(self, file: Path):
        self.file = open(file, "w")  # noqa: SIM115
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()


class SaveLogs(Callback):
    """
    Responsible for saving logs to file

    Parameters
    ----------
    name : str, optional
        The name of the file to save logs to. Defaults to ``logs.txt``.

    Example
    -------

    .. code-block:: python

        from digital_experiments import experiment, SaveLogs

        @experiment(callbacks=[SaveLogs("my-logs")])
        def example():
            print("hello world")

        example()
        id = example.observations()[-1].id
        artefacts = example.artefacts(id)
        # returns [Path("<some>/<path>/<id>/my-logs")]
        artefacts[0].read_text()
        # returns 'hello world\\n'

    """

    def __init__(self, name: str = "logs.txt"):
        self.name = name

    def start(self, id: str, config: dict[str, Any]) -> None:
        self.tee = Tee(current_dir() / self.name)
        sys.stdout = self.tee

    def end(self, observation: Observation) -> None:
        sys.stdout = sys.__stdout__
        del self.tee


def _command_output(command: str) -> str:
    """Run a subprocess command and return the output as a string"""
    return (
        subprocess.run(
            command.split(" "),
            capture_output=True,
            check=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )


def _in_git_repo() -> bool:
    """Check if the current directory is inside a git repo"""
    try:
        return _command_output("git rev-parse --is-inside-work-tree") == "true"
    except subprocess.CalledProcessError:
        return False


@functools.lru_cache
def _git_information() -> dict[str, str]:
    """Get information about the current git repo"""
    return {
        "branch": _command_output("git rev-parse --abbrev-ref HEAD"),
        "commit": _command_output("git rev-parse HEAD"),
        "remote": _command_output("git config --get remote.origin.url"),
    }


class GitInfo(Callback):
    """Responsible for recording git information about the experiment"""

    def end(self, observation: Observation) -> None:
        if _in_git_repo():
            observation.metadata["git"] = _git_information()


@functools.lru_cache
def _pip_freeze() -> str:
    """Get the pip freeze of the current python environment"""
    return _command_output(f"{sys.executable} -m pip freeze")


class PipFreeze(Callback):
    """Responsible for recording the pip freeze of the experiment"""

    def end(self, observation: Observation) -> None:
        observation.metadata["pip_freeze"] = _pip_freeze()


class SystemInfo(Callback):
    """Responsible for recording system information about the experiment"""

    def end(self, observation: Observation) -> None:
        observation.metadata["system"] = dict(
            platform=platform.platform(),
            machine=platform.machine(),
            processor=platform.processor(),
            system=platform.system(),
            python_version=platform.python_version(),
            pwd=os.getcwd(),
        )
