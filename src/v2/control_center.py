import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import List

# isolate all global state here
__CURRENTLY_RUNNING: List["Run"] = []
__RECORDING: bool = True


@dataclass
class Run:
    id: str
    directory: Path


@contextlib.contextmanager
def recording_run(run: Run):
    __CURRENTLY_RUNNING.append(run)
    yield
    __CURRENTLY_RUNNING.pop()


@contextlib.contextmanager
def dont_record():
    global __RECORDING
    __RECORDING = False
    yield
    __RECORDING = True


def currently_running():
    return __CURRENTLY_RUNNING[-1]


def current_directory():
    return currently_running().directory.resolve()


def should_record():
    return __RECORDING
