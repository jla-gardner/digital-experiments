from __future__ import annotations

import os
from functools import partial, update_wrapper
from pathlib import Path
from typing import Callable, overload

from .backends import instantiate_backend
from .callbacks import (
    CodeVersioning,
    GlobalStateNotifier,
    Logging,
    Timing,
)
from .core import Callback, Experiment

ExperimentDecorator = Callable[[Callable], Experiment]


@overload
def experiment(
    *,
    root: Path | None = None,
    verbose: bool = False,
    backend: str = "json",
    cache: bool = False,
) -> ExperimentDecorator:
    ...


@overload
def experiment(
    function: Callable,
    *,
    root: Path | None = None,
    verbose: bool = False,
    backend: str = "json",
    cache: bool = False,
) -> Experiment:
    ...


def experiment(
    function: Callable | None = None,
    *,
    root: Path | None = None,
    verbose: bool = False,
    backend: str = "pickle",
    cache: bool = False,
) -> Experiment | ExperimentDecorator:
    """
    Decorator to record experiments.
    """
    if function is None:
        kwargs = locals()
        kwargs.pop("function")
        return partial(experiment, **kwargs)  # type: ignore

    if root is None:
        env_root = os.environ.get("DE_ROOT")
        if env_root is not None:
            root = Path(env_root)
        else:
            root = Path(f"experiments/{function.__name__}")

    callbacks: list[Callback] = [
        Logging(verbose),
        Timing(),
        CodeVersioning(),
        GlobalStateNotifier(root),
    ]
    for callback in callbacks:
        callback.setup(function)

    e = Experiment(
        function,
        instantiate_backend(backend, root),
        callbacks,
        cache,
    )
    update_wrapper(e, function)
    return e
