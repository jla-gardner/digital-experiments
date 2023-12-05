from __future__ import annotations

import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypedDict

from .core import Callback, Observation
from .util import source_code

# Global state is isolated here:
_RUNNING_IDS: list[str] = []
_CURRENT_DIR: list[Path] = []
_TIMING_BLOCKS: list[dict[str, TimingBlock]] = []


class GlobalStateNotifier(Callback):
    def __init__(self, root: Path):
        self.root = root

    def start(self, id: str, config: dict[str, Any]):
        _RUNNING_IDS.append(id)
        dir = self.root / "storage" / id
        dir.mkdir(parents=True, exist_ok=True)
        _CURRENT_DIR.append(dir)

    def end(self, observation: Observation):
        _RUNNING_IDS.pop()
        dir = _CURRENT_DIR.pop()
        # clean up if empty
        if len(list(dir.glob("*"))) == 0:
            dir.rmdir()


def current_id() -> str:
    if len(_RUNNING_IDS) == 0:
        raise RuntimeError(
            "No experiment running - this function only works "
            "inside an experiment context"
        )
    return _RUNNING_IDS[-1]


def current_dir() -> Path:
    if len(_CURRENT_DIR) == 0:
        raise RuntimeError(
            "No experiment running - this function only works "
            "inside an experiment context"
        )
    return _CURRENT_DIR[-1]


class Logging(Callback):
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
    start = datetime.now()
    yield
    end = datetime.now()
    _TIMING_BLOCKS[-1][name] = _timing_block(start, end)
