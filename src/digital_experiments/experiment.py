from __future__ import annotations

import os
from functools import partial, update_wrapper
from pathlib import Path
from typing import Callable, overload

from .backends import instantiate_backend
from .callbacks import (
    CodeVersioning,
    GitInfo,
    GlobalStateNotifier,
    Logging,
    PipFreeze,
    SystemInfo,
    Timing,
)
from .core import Callback, Experiment

ExperimentDecorator = Callable[[Callable], Experiment]


@overload
def experiment(function: Callable) -> Experiment:
    ...


@overload
def experiment(
    *,
    root: Path | None = None,
    verbose: bool = False,
    backend: str = "json",
    cache: bool = False,
    callbacks: list[Callback] | None = None,
) -> ExperimentDecorator:
    ...


def experiment(
    function: Callable | None = None,
    *,
    root: Path | None = None,
    verbose: bool = False,
    backend: str = "pickle",
    cache: bool = False,
    callbacks: list[Callback] | None = None,
) -> Experiment | ExperimentDecorator:
    """
    Decorator to automate the recording of experiments.

    Examples
    --------
    As a simple decorator, using all defaults:

    .. code-block:: python

        @experiment
        def add(a, b):
            return a + b

        add(1, 2)
        # 3

        add.observations() # returns a list of observations
        # [Observation(<id1>, {'a': 1, 'b': 2} → 3})]


    As a decorator with some custom options specified:

    .. code-block:: python

        @experiment(root="my-experiments", verbose=True, backend="json")
        def add(a, b):
            return a + b

    Parameters
    ----------
    function
        The function to wrap
    root
        The root directory for storing results. If not specified, the
        environment variable ``DE_ROOT`` is used, or the default
        ``./experiments/<function_name>`` is used.
    verbose
        Whether to print progress to stdout
    backend
        The type of backend to use for storing results. See
        :doc:`the backends page <backends-api>` for more details.
    cache
        Whether to use cached results if available
    callbacks
        A list of optional callbacks to use. See
        :doc:`the callbacks page <callbacks-api>` for more details.
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

    # callbacks are `enter`ed in the following order,
    # and `exit`ed in reverse order
    # hence, the order of the list below is important
    # - GlobalStateNotifier is set to be first in and last out
    #     so that current_dir() etc. are available to other callbacks

    all_callbacks: list[Callback] = [
        GlobalStateNotifier(root),
        Logging(verbose),
        CodeVersioning(),
        Timing(),
        GitInfo(),
        PipFreeze(),
        SystemInfo(),
    ] + (callbacks or [])
    for callback in all_callbacks:
        callback.setup(function)

    e = Experiment(
        function,
        instantiate_backend(backend, root),
        all_callbacks,
        cache,
    )
    update_wrapper(e, function)
    return e
