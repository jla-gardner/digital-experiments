"""
`Suggester`s take a search `Space` and list of previous `Steps`,
and suggests new `Point`s to evaluate.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Union

import numpy as np

from digital_experiments.search.space import (
    Categorical,
    Distribution,
    Grid,
    Space,
    to_space,
)

Point = Mapping[str, Any]
UnitPoint = Mapping[str, float]  # a point in the unit hypercube


@dataclass
class Step:
    point: Point
    observation: float


class Suggester(ABC):
    def __init__(
        self,
        space: Union[Dict[str, Distribution], Space],
        previous_steps: List[Step] = None,
    ):
        space = to_space(space)
        self.space = space

        previous_steps = previous_steps or []
        previous_steps = filter(self.is_valid_step, previous_steps)
        self.previous_steps = list(previous_steps)

    @abstractmethod
    def suggest(self) -> Point:
        raise NotImplementedError()

    def suggest_many(self, n=2):
        return [self.suggest() for _ in range(n)]

    def is_valid_step(self, step: Step):
        return self.is_valid_point(step.point)

    def is_valid_point(self, point: Point):
        return self.space.contains(point)

    def previous_points(self) -> List[Point]:
        return [step.point for step in self.previous_steps]

    def previous_unit_points(self):
        return [self.space.inverse_transform(p) for p in self.previous_points()]

    def tell(self, point: Point, observation: float):
        if not self.is_valid_point(point):
            warnings.warn(f"Point {point} is not in this suggester's space ({self}).")
        else:
            self.previous_steps.append(Step(point, observation))


class RandomSuggester(Suggester):
    def __init__(
        self,
        space: Union[Dict[str, Distribution], Space],
        previous_steps: List[Step] = None,
        seed: int = 42,
    ):
        super().__init__(space, previous_steps)
        self.random = np.random.RandomState(seed=seed).random

    def suggest(self, n=1):
        return self.space.random_sample(n=n, generator=self.random)


class GridSuggester(Suggester):
    def __init__(
        self,
        space: Grid,
        previous_steps: List[Step] = None,
    ):
        if not isinstance(space, Grid):
            raise ValueError(f"GridSuggester only works with Grid spaces, not {space}.")

        super().__init__(space, previous_steps)

        self.total_points = np.prod([len(dist.options) for dist in space.values()])

        self.sampled = [False] * self.total_points
        for step in self.previous_steps:
            idx = self._point_to_idx(step.point)
            self.sampled[idx] = True

    def suggest(self) -> Point:
        # get first unsampled point
        idx = self.sampled.index(False)
        return self._idx_to_point(idx)

    def tell(self, point: Point, observation: float):
        super().tell(point, observation)
        idx = self._point_to_idx(point)
        self.sampled[idx] = True

    def _point_to_idx(self, point: Point):
        """
        convert a point in the grid to a scalar index
        """

        idx = 0
        for name, dist in self.space.items():
            options = dist.options
            idx *= len(options)
            idx += options.index(point[name])

        return idx

    def _idx_to_point(self, idx):
        """
        convert a scalar index to a point in the grid
        """

        point = {}
        for name, dist in self.space.items():
            options = dist.options
            point[name] = options[idx % len(options)]
            idx //= len(options)

        return point
