from __future__ import annotations

import random
from itertools import product
from typing import Any, Callable, Iterable, Protocol, Sequence, Union

from .core import Controller, Experiment

# TODO implement:
# - an sklearn controller / bayeseopt controller
# - an optuna controller

__all__ = ["RandomSearch", "GridSearch"]


class RandomSearch(Controller):
    """
    Controller that suggests experiments based on a random search

    Parameters
    ----------
    dimensions: dict[str, Sequence | RVS]
        a mapping from parameter names to random dimensions. A random
        dimension can be a sequence of values, a scipy.stats distribution or
        any object with an rvs method

    Example
    -------

    .. code-block:: python

        from digital_experiments import experiment
        from digital_experiments.controllers import RandomSearch
        from scipy.stats import uniform

        @experiment
        def example(a, b):
            return (2 * a - 1) * b

        RandomSearch(a=uniform(-1, 1), b=[1, 2, 3]).control(example, n=10)
    """

    class RVS(Protocol):
        """
        A protocol for scipy.stats distributions, or any
        object with an rvs method
        """

        rvs: Callable[..., Any]

    RandomDimension = Union[Sequence, RVS]

    def __init__(self, **dimensions: RandomSearch.RandomDimension):
        self.dimensions = dimensions

    def suggest(self, experiment: Experiment) -> dict[str, Any]:
        def choose(dim: RandomSearch.RandomDimension) -> Any:
            if isinstance(dim, Sequence):
                return random.choice(dim)
            elif hasattr(dim, "rvs"):
                return dim.rvs()
            else:
                raise TypeError(
                    f"Invalid dimension type: {type(dim)}. Expected a "
                    "sequence, scipy.stats distribution, or any object "
                    "with an rvs method."
                )

        return {name: choose(dim) for name, dim in self.dimensions.items()}


class GridSearch(Controller):
    """
    Controller that suggests experiments based on an exhaustive grid search

    Parameters
    ----------
    dimensions : dict[str, Iterable]
        a mapping from parameter names to sequences of values

    Example
    -------

    .. code-block:: python

        from digital_experiments import experiment
        from digital_experiments.controllers import GridSearch

        @experiment
        def example(a, b):
            return (2 * a - 1) * b

        GridSearch(a=[0, 1], b=range(3)).control(example, n=6)
    """

    def __init__(self, **dimensions: Iterable):
        # check that all dimensions are iterables
        for dim in dimensions.values():
            if not isinstance(dim, Iterable):
                raise TypeError(
                    f"Invalid dimension type: {type(dim)}. Expected an "
                    "iterable."
                )

        self.dimensions = dimensions

    def suggest(self, experiment: Experiment) -> dict[str, Any] | None:
        # get existing configs
        configs = [obs.config for obs in experiment.observations()]

        # loop through grid and return first config that hasn't been tried
        for config in self._grid_iter():
            if config not in configs:
                return config

        # if all configs have been tried, return None
        return None

    def _grid_iter(self):
        for config in product(*self.dimensions.values()):
            yield dict(zip(self.dimensions.keys(), config))
