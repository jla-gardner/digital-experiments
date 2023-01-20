import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import numpy as np
from skopt import Optimizer
from skopt.sampler import Hammersly
from skopt.space import Dimension, Space

from digital_experiments.core import additional_metadata
from digital_experiments.querying import experiments_for


class Modes:
    MANUAL = "manual"
    RANDOM = "random"
    BAYESIAN = "bayesian-optimization"


SEARCH_MODE = "search-mode"

Point = Dict[str, Any]


@dataclass
class Step:
    point: Point
    y: float


class NiceOptimizer:
    def __init__(
        self,
        objective: Callable,
        space: Dict[str, Dimension],
        steps: List[Step] = None,
        seed: int = None,
    ) -> None:

        if steps is None:
            steps = []
        self.random_points: List[Point] = []
        self.steps_so_far: List[Step] = []
        self.random = np.random.RandomState(seed=seed)
        self.objective = objective
        self.space = space
        self.generate_more_random_points()
        self.actual_optimizer = get_default_optimizer(space)
        for step in steps:
            self.record(step.point, step.y, fit=step is steps[-1])

    def explore_step(self):
        """Perform a single exploration step."""

        point = self.get_random_point()
        return self.do_step(point)

    def exploit_step(self):
        """Perform a single exploitation step."""

        point = self.get_optimized_point()
        return self.do_step(point)

    def optimize_step(self):
        """Perform a single optimization step."""

        if len(self.steps_so_far) <= self.n_explore_steps:
            return self.explore_step()
        return self.exploit_step()

    def get_random_point(self) -> Point:
        """Get the next point to try, randomly."""

        # If we have no more random points, generate some more
        if len(self.unused_random_points) == 0:
            self.generate_more_random_points()

        return self.random.choice(self.unused_random_points)

    def get_optimized_point(self) -> Point:
        """Get the next point to try, optimized."""

        values = self.actual_optimizer.ask()
        return self.to_point(values)

    def do_step(self, point: Point):
        """Perform a step."""

        output = self.objective(**point)
        self.record(point, output)
        return point, output

    def points_so_far(self) -> List[Point]:
        """Points that have been seen so far."""

        return [step.point for step in self.steps_so_far]

    def record(self, point: Point, output: float, fit: bool = True):
        """Record a step."""
        if not self.check_point(point):
            return
        self.steps_so_far.append(Step(point, output))
        self.actual_optimizer.tell(list(point.values()), output, fit)

    def check_point(self, point: Point) -> bool:
        """Check if a point should be told to the optimizer."""

        # raise warning if point has already been seen,
        # or if point is outside of the space
        if point in self.points_so_far():
            warnings.warn(f"Point {point} has already been seen.")
        if not point.values() in to_skopt_space(self.space):
            warnings.warn(f"Point {point} is outside of the space - not recording.")
            return False
        return True

    @property
    def unused_random_points(self) -> List[Point]:
        """Random points that have not been used yet."""

        return [p for p in self.random_points if p not in self.points_so_far()]

    def to_point(self, values):
        return dict(zip(self.space.keys(), values))

    def generate_more_random_points(self):
        """Generate more random points."""

        N = len(self.steps_so_far) * 2 + 1

        values = sample_random_points(self.space, N)
        self.random_points += [self.to_point(v) for v in values]


class ExperimentMinimizer(NiceOptimizer):
    def explore_step(self):
        with additional_metadata({SEARCH_MODE: Modes.RANDOM}):
            return super().explore_step()

    def exploit_step(self):
        with additional_metadata({SEARCH_MODE: Modes.BAYESIAN}):
            return super().exploit_step()


def sample_random_points(space, n) -> List[Dict[str, Any]]:
    return Hammersly().generate(list(space.values()), n)
    # return to_skopt_space(space).rvs(n_samples=n)


def get_default_optimizer(space):
    """Get the default optimizer."""

    return Optimizer(
        dimensions=list(space.values()),
        base_estimator="GP",
        n_initial_points=1,
    )


def to_skopt_space(space: Dict[str, Dimension]) -> Space:
    """Convert a space to a skopt space."""

    dimensions = []
    for name, dimension in space.items():
        dimensions.append(dimension)
    return Space(dimensions)


def optimizer(experiment, space, overrides=None, loss_fn=None):
    if overrides is None:
        overrides = {}
    if loss_fn is None:
        loss_fn = lambda x: x

    experiments = experiments_for(experiment, config=overrides)

    points = [{k: v for k, v in e.config.items() if k in space} for e in experiments]
    values = [loss_fn(e.result) for e in experiments]
    steps = [Step(p, v) for p, v in zip(points, values)]

    def objective(**kwargs):
        result = experiment(**{**overrides, **kwargs})
        return loss_fn(result)

    return ExperimentMinimizer(objective, space, steps)
