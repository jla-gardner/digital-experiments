"""
`Suggester`s take a search `Space` and list of previous `Steps`,
and suggests new `Point`s to evaluate.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Union

import numpy as np

from digital_experiments.search.space import Distribution, Space, to_space

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
        self.space = to_space(space)
        previous_steps = previous_steps or []

        self.previous_steps = []
        for step in previous_steps:
            self.tell(step.point, step.observation)

    @abstractmethod
    def suggest(self) -> Point:
        raise NotImplementedError()

    def suggest_many(self, n=2):
        return [self.suggest() for _ in range(n)]

    def is_valid_step(self, step: Step):
        return self.is_valid_point(step.point)

    def is_valid_point(self, point: Point):
        return self.space.contains(point)

    def previous_points(self):
        return [step.point for step in self.previous_steps]

    def previous_unit_points(self):
        return [
            self.space.inverse_transform(p) for p in self.previous_points()
        ]

    def tell(self, point: Point, observation: float):
        if not self.is_valid_point(point):
            warnings.warn(
                f"Point {point} is not in this suggester's space ({self})."
            )
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
