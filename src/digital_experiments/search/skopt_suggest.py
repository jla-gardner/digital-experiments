from typing import Dict, List, Union

import numpy as np
from pandas import Categorical
from skopt import Optimizer as SKOptimizer
from skopt import space as SK

from digital_experiments.search.space import (
    Categorical,
    Distribution,
    LogUniform,
    Space,
    Uniform,
    to_space,
)
from digital_experiments.search.suggest import Point, Step, Suggester


class SKSuggester(Suggester):
    def __init__(
        self,
        space: Union[Dict[str, Distribution], Space],
        previous_steps: List[Step] = None,
        n_explore_steps: int = 10,
        seed: int = 42,
    ) -> None:

        super().__init__(space, previous_steps)

        self.tells_since_suggest = len(self.previous_steps)
        self.n_explore_steps = n_explore_steps
        self.random = np.random.RandomState(seed=seed).random

        _skopt_dimensions = to_skopt_dims(space)
        self.optimizer = SKOptimizer(
            dimensions=_skopt_dimensions,
            base_estimator="GP",
            n_initial_points=1,
            random_state=seed,
        )

    def tell(self, point: Point, observation: float):
        super().tell(point, observation)
        self.tells_since_suggest += 1

    def suggest(self) -> Point:
        self._fit_if_necessary()
        n_points_so_far = len(self.previous_steps)
        if n_points_so_far < self.n_explore_steps:
            return self.explore_step()
        else:
            return self.exploit_step()

    def explore_step(self) -> Point:
        return self.space.random_sample(n=1, generator=self.random)

    def exploit_step(self) -> Point:
        values = self.optimizer.ask()
        return {key: value for key, value in zip(self.space.keys(), values)}

    def _fit_if_necessary(self):
        if self.tells_since_suggest == 0:
            return

        for i, step in enumerate(
            self.previous_steps[-self.tells_since_suggest :]
        ):
            values = list(step.point.values())
            observation = step.observation

            # only fit the underlying model on the last step
            fit_model = i == self.tells_since_suggest - 1
            self.optimizer.tell(values, observation, fit=fit_model)

        self.tells_since_suggest = 0


def to_skopt_dims(my_space: Union[Dict[str, Distribution], Space]):
    my_space = to_space(my_space)

    dimensions = []
    for name, dist in my_space.items():
        dim = to_skopt_dimension(dist)
        dim.name = name
        dimensions.append(dim)

    return dimensions


def to_skopt_dimension(dist: Distribution):
    if isinstance(dist, Uniform):
        return SK.Real(dist.low, dist.high)
    elif isinstance(dist, Categorical):
        return SK.Categorical(dist.options)
    elif isinstance(dist, LogUniform):
        return SK.Real(dist.low, dist.high, prior="log-uniform")
    else:
        raise ValueError(f"Unsupported distribution: {dist}")
