"""
`Suggester`s take a search `Space` and list of previous `Steps`,
and suggests new `Point`s to evaluate.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Union

import numpy as np

from digital_experiments.search.distributions import Categorical, Distribution
from digital_experiments.search.space import Point, Space, to_space


@dataclass
class Step:
    point: Point
    observation: float


class Suggester(ABC):
    """
    A `Suggester` takes a search `Space` and list of previous `Steps`,
    and suggests new `Point`s to evaluate.

    Parameters
    ----------
    space
        The search space.
    previous_steps
        A list of previous steps.

    Methods
    -------
    suggest()
        Suggest a new point to evaluate.
    tell(point, observation)
        Tell the suggester about a new observation.
    """

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
        """
        Suggest a new point to evaluate.
        """

    def tell(self, point: Point, observation: float):
        """
        Tell the suggester about a new observation.
        """
        if not self.is_valid_point(point):
            warnings.warn(f"Point {point} is not in this suggester's space ({self}).")
        else:
            self.previous_steps.append(Step(point, observation))

    def suggest_many(self, n=2):
        return [self.suggest() for _ in range(n)]

    def is_valid_step(self, step: Step):
        return self.is_valid_point(step.point)

    def is_valid_point(self, point: Point):
        return self.space.contains(point)

    def previous_points(self) -> List[Point]:
        return [step.point for step in self.previous_steps]

    def previous_unit_points(self):
        return [self.space.transform_to_unit_range(p) for p in self.previous_points()]


class RandomSuggester(Suggester):
    def __init__(
        self,
        space: Union[Dict[str, Distribution], Space],
        previous_steps: List[Step] = None,
        seed: int = None,
        random_number_generator=None,
    ):
        super().__init__(space, previous_steps)

        if random_number_generator is None:
            random_number_generator = np.random.RandomState(seed=seed).random
        self.random_number_generator = random_number_generator

    def suggest(self) -> Point:
        return self.space.random_sample(self.random_number_generator)


class NamedBooleanGrid:
    """
    a multi-dimensional grid of named things

    Parameters
    ----------
    things
        the named dimensions of the grid
    """

    def __init__(self, things: Dict[str, List]):
        self._things = things
        self._hits = [False] * np.prod([len(thing) for thing in self._things.values()])

    def hit(self, point: Point):
        """
        mark a point as hit
        """
        idx = self._point_to_index(point)
        self._hits[idx] = True

    def first_miss(self):
        """
        find the first point that has not been hit
        """
        for idx, hit in enumerate(self._hits):
            if not hit:
                return self._index_to_point(idx)
        raise ValueError("Grid is full")

    def total_hits(self):
        """
        find the first point that has not been hit
        """
        return sum(self._hits)

    def total_misses(self):
        """
        find the first point that has not been hit
        """
        return len(self._hits) - sum(self._hits)

    def _point_to_index(self, point: Point):
        """
        convert a point to an index in the grid
        """
        idx = 0

        for name, value in reversed(point.items()):
            if name not in self._things:
                raise ValueError(f"Invalid point: unknown name {name}")
            if value not in self._things[name]:
                raise ValueError(f"Invalid point: unknown value {value} for {name}")

            idx *= len(self._things[name])
            idx += self._things[name].index(value)

        return idx

    def _index_to_point(self, idx: int):
        """
        convert an index in the grid to a point
        """

        point = {}
        for name, values in reversed(self._things.items()):
            point[name] = values[idx % len(values)]
            idx //= len(values)

        return point

    def size(self):
        """
        get the size of the grid
        """
        return len(self._hits)


class GridSuggester(Suggester):
    def __init__(
        self,
        space: Union[Dict[str, Distribution], Space],
        previous_steps: List[Step] = None,
    ):
        super().__init__(space, previous_steps)
        for name, dist in self.space.items():
            if not isinstance(dist, Categorical):
                raise ValueError(
                    f"GridSuggester only works with Categorical distributions, not {dist} ({name})."
                )

        self._grid = NamedBooleanGrid(
            {name: dist.options for name, dist in self.space.items()}
        )
        for step in self.previous_steps:
            self._grid.hit(step.point)

    def __len__(self):
        return np.prod([len(dist.options) for dist in self.space.values()])

    def suggest(self) -> Point:
        return self._grid.first_miss()

    def tell(self, point: Point, observation: float):
        super().tell(point, observation)
        self._grid.hit(point)
