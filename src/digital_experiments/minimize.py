import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Union

import numpy as np
from skopt import Optimizer
from skopt.space import Dimension, Space

from . import control_center as GLOBAL


class Modes:
    MANUAL = "manual"
    RANDOM = "random"
    BAYESIAN = "bayesian-optimization"


SEARCH_MODE = "search-mode"

Point = Dict[str, Any]


@dataclass
class Step:
    point: Point
    observation: float


class Minimizer:
    """
    Minimize a function while avoiding skopt's `@use_named_args` decorator.

    Usage:

    ```python
    from skopt.space import Real
    from digital_experiments.optmization import Minimizer

    def objective(x, y):
        return x + y

    minimizer = Minimizer(
        objective=objective,
        space={
            "x": Real(0, 1),
            "y": Real(0, 1),
        },
        n_explore_steps=10,
    )

    # manually perform an exploration step
    minimizer.explore_step()

    # manually perform an exploitation step
    minimizer.exploit_step()

    # perform a single optimization step (based on the number of steps so far)
    minimizer.optimize_step()
    """

    def __init__(
        self,
        objective: Callable,
        space: Dict[str, Dimension],
        steps: List[Step] = None,
        seed: int = None,
        n_explore_steps: int = 10,
        optimizer: Optimizer = None,
    ) -> None:

        if steps is None:
            steps = []

        if seed is None:
            seed = datetime.now().microsecond
        self.random = np.random.RandomState(seed=seed)

        self.space = space
        if optimizer is None:
            optimizer = get_default_optimizer(space, self.random)
        self.actual_optimizer = optimizer

        self.n_explore_steps = n_explore_steps

        self.objective = objective
        self.steps_so_far: List[Step] = []
        for step in steps:
            self.record(step.point, step.observation, fit=step is steps[-1])

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

        return {
            name: dimension.rvs(1, random_state=self.random)[0]
            for name, dimension in self.space.items()
        }

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
            warnings.warn(
                f"Point {point} is outside of the space - not recording."
            )
            return False
        return True

    def to_point(self, values):
        return dict(zip(self.space.keys(), values))


class ExperimentMinimizer(Minimizer):
    def explore_step(self):
        with GLOBAL.additional_metadata({SEARCH_MODE: Modes.RANDOM}):
            return super().explore_step()

    def exploit_step(self):
        with GLOBAL.additional_metadata({SEARCH_MODE: Modes.BAYESIAN}):
            return super().exploit_step()


def get_default_optimizer(space, rng) -> Optimizer:
    """Get the default optimizer."""

    return Optimizer(
        dimensions=list(space.values()),
        base_estimator="GP",
        n_initial_points=1,
        random_state=rng,
    )


def to_skopt_space(space: Dict[str, Dimension]) -> Space:
    """Convert a space to a skopt space."""

    dimensions = []
    for name, dimension in space.items():
        dimension.name = name
        dimensions.append(dimension)
    return Space(dimensions)


def identity(x):
    return x


def minimizer(
    experiment: Union[str, Callable],
    space: Dict[str, Dimension],
    overrides: Dict[str, Any] = None,
    loss_fn: Callable = None,
    seed: int = None,
    n_explore_steps: int = 10,
) -> Minimizer:
    """
    Create a minimizer for a given experiment.

    Args:
        experiment: The experiment to optimize.
        space: The search space.
        overrides: Any overrides to the experiment.
        loss_fn: A function to convert the experiment result to a float.

    Returns:
        An optimizer.

    Usage:

    ```python
    from digital_experiments import experiment
    from digital_experiments.minimize import minimizer, Real

    @experiment
    def objective(x, y):
        return x - y

    minim = minimizer(
        objective,
        {"x": Real(-10, 10), "y": Real(-10, 10)}
        n_explore_steps=5,
    )

    for _ in range(10):
        minim.optimize_step()
    ```
    """

    if overrides is None:
        overrides = {}
    if loss_fn is None:
        loss_fn = identity

    # TODO: filter by config overrides
    previous_observations = experiment.observations

    points = [
        {k: v for k, v in expmt.config.items() if k in space.keys()}
        for expmt in previous_observations
    ]
    values = [loss_fn(e.result) for e in previous_observations]
    steps = [Step(p, v) for p, v in zip(points, values)]

    def objective(**kwargs):
        result = experiment(**{**overrides, **kwargs})
        return loss_fn(result)

    return ExperimentMinimizer(objective, space, steps, seed, n_explore_steps)
