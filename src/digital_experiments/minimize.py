from typing import Any, Callable, Dict, Union

from digital_experiments.experiment import Experiment
from digital_experiments.search.skopt_suggest import SKSuggester
from digital_experiments.search.space import Distribution, Space, to_space
from digital_experiments.search.suggest import Step, Suggester

from . import control_center as GLOBAL


class Modes:
    MANUAL = "manual"
    RANDOM = "random"
    BAYESIAN = "bayesian-optimization"


SEARCH_MODE = "search-mode"


class Minimizer:
    def __init__(self, objective: Callable, suggester: Suggester) -> None:
        self.objective = objective
        self.suggester = suggester

    def step(self):
        point = self.suggester.suggest()
        observation = self.objective(**point)
        self.suggester.tell(point, observation)
        return Step(point, observation)

    def best_point(self):
        all_steps = self.suggester.previous_steps
        best_step = min(all_steps, key=lambda step: step.observation)
        return best_step.point

    @property
    def steps(self):
        return self.suggester.previous_steps


class ExperimentMinimzer(Minimizer):
    def explore_step(self):
        point = self.suggester.explore_step()
        with GLOBAL.additional_metadata({SEARCH_MODE: Modes.RANDOM}):
            observation = self.objective(**point)
        self.suggester.tell(point, observation)
        return Step(point, observation)

    def exploit_step(self):
        point = self.suggester.exploit_step()
        with GLOBAL.additional_metadata({SEARCH_MODE: Modes.BAYESIAN}):
            observation = self.objective(**point)
        self.suggester.tell(point, observation)
        return Step(point, observation)


def minimizer(
    experiment: Experiment,
    space: Union[Dict[str, Distribution], Space],
    loss_fn: Callable = None,
    seed: int = 42,
    n_explore_steps: int = 10,
) -> Minimizer:
    """
    Create a minimizer for a given experiment.

    Args:
        experiment: The experiment to optimize.
        space: The search space.
        loss_fn: A function to convert the experiment result to a float.

    Returns:
        An optimizer.

    Usage:

    ```python
    ```
    """

    if loss_fn is None:
        loss_fn = identity

    def objective(**kwargs):
        result = experiment(**kwargs)
        return loss_fn(result)

    space: Space = to_space(space)

    previous_observations = experiment.observations

    points = [
        {k: v for k, v in obs.config.items() if k in space.keys()}
        for obs in previous_observations
    ]
    values = [loss_fn(e.result) for e in previous_observations]
    previous_steps = [Step(p, v) for p, v in zip(points, values)]

    suggester = SKSuggester(space, previous_steps, n_explore_steps, seed)
    return ExperimentMinimzer(objective, suggester)


def identity(x):
    return x
