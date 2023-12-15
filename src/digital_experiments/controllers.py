from __future__ import annotations

from typing import Any

from .core import Controller, Experiment

# TODO implement:
# - an sklearn controller / bayeseopt controller
# - a random controller (can be sklearn under the hood)
# - an optuna controller


class RandomSearch(Controller):
    """
    Controller that suggests experiments based on a random search

    Parameters
    ----------
    param_grid : dict[str, list[Any]]
        A dictionary mapping parameter names to collections or
        distributions to randomly sample from.

    Example
    -------

    .. code-block:: python

        from digital_experiments import experiment, RandomSearch
        from scipy.stats import uniform

        @experiment
        def example(a, b):
            return (2 * a - 1) * b

        controller = RandomSearch(a=uniform(-1, 1), b=[1, 2, 3])
        controller.control(example, n=10)
    """

    def __init__(self, **param_grid):
        self.param_grid = param_grid

    def suggest(self, experiment: Experiment) -> dict[str, Any]:
        from sklearn.model_selection import ParameterSampler

        return next(iter(ParameterSampler(self.param_grid, 1)))


# class GridSearch(Controller):
#     """
#     Controller that suggests experiments based on a random grid search
#     """

#     from sklearn.model_selection import ParameterGrid, ParameterSampler

#     def __init__(self, random=False, **param_grid):
#         self.random = random
#         self.param_grid = param_grid

#     def suggest(self, experiment: Experiment) -> dict[str, Any]:
#         if self.random:
#             return next(self.ParameterSampler(self.param_grid, 1))
#         else:
#             return next(self.ParameterGrid(self.param_grid))
