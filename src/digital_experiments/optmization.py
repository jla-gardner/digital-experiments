from datetime import datetime
from typing import Any, Callable, Dict, Sequence, Union

import numpy as np
from skopt import gp_minimize
from skopt.sampler import Hammersly
from skopt.space import Categorical, Dimension, Integer, Real
from skopt.utils import use_named_args

from digital_experiments.core import additional_metadata
from digital_experiments.querying import (
    convert_to_experiments,
    experiments_matching,
    matches,
)
from digital_experiments.util import independent_random

Numeric = Union[int, float, np.number]


class Modes:
    MANUAL = "manual"
    RANDOM = "random"
    BAYESIAN = "bayesian-optimization"


SEARCH_MODE = "search-mode"


def optimize_step(
    previous_arguments: Sequence[Dict],
    previous_outputs: Sequence[Numeric],
    space: Dict[str, Dimension],
    objective: Callable,
    n_random_steps: int,
    overrides: Dict[str, Any] = None,
    loss_fn: Callable = None,
):
    """
    Perform a single optimization step on the objective function.

    Pass in all previous arguments and outputs, and the space to search over.
    Any previous calls that correspond to the space will be used to initialize
    the optimization.

    Args:
        - `previous_arguments`: list of previous arguments
        - `previous_outputs`: list of previous outputs
        - `space`: space to optimize over
        - `objective`: objective function
        - `n_random_steps`: number of random steps to perform
        - `overrides`: keyword overrides to apply to the objective function
        - `loss_fn`: loss function to apply to the objective function

    Returns:
        `None`

    Example:
        >>> from skopt.space import Real
        >>> from digital_experiments.optmization import optimize_step
        >>> def objective(x, y):
        ...     return x + y
        >>> # this will perform a random search, since only 1 previous call:
        >>> optimize_step(
        ...     previous_arguments=[{"x": 1, "y": 0.5}],
        ...     previous_outputs=[0.5],
        ...     space={"x": Real(0, 1), "y": Real(0, 1)},
        ...     objective=objective,
        ...     n_random_steps=2,
        ... )
        >>> # this will perform a bayesian optimization, since 2 previous calls:
        >>> optimize_step(
        ...     previous_arguments=[{"x": 1, "y": 0.5}, {"x": 0.5, "y": 0.5}],
        ...     previous_outputs=[1.5, 1],
        ...     space={"x": Real(0, 1), "y": Real(0, 1)},
        ...     objective=objective,
        ...     n_random_steps=2,
        ... )
        >>> # this will perform a random search, since only 1 previous call
        >>> # that matches the space:
        >>> optimize_step(
        ...     previous_arguments=[{"x": 1, "y": 0.5}, {"x": 3, "y": 4}],
        ...     previous_outputs=[1.5, 7],
        ...     space={"x": Real(0, 1), "y": Real(0, 1)},
        ...     objective=objective,
        ...     n_random_steps=2,
        ... )
    """

    # ensure no overrides are passed that also being optimized over
    overrides = overrides or {}
    assert not any(
        k in overrides for k in space
    ), "you're overriding a variable you're trying to optimize for"

    # if no loss_fn is passed, use the identity function
    loss_fn = loss_fn or (lambda x: x)

    # convert to skopt space
    dimensions = []
    for k, v in space.items():
        v.name = k
        dimensions.append(v)

    @use_named_args(dimensions)
    def _objective(**kwargs):
        return loss_fn(objective(**kwargs, **overrides))

    # filter out previous calls that are not in the space we are optimizing over
    template = is_in(space)
    template.update(overrides)
    acceptable_idxs = [
        i for i, x in enumerate(previous_arguments) if matches(x, template)
    ]
    previous_arguments = [previous_arguments[i] for i in acceptable_idxs]
    previous_outputs = [previous_outputs[i] for i in acceptable_idxs]

    # remove any arguments that are not in the space (these will now be all the same)
    x0 = [tuple(prev_arg[k] for k in space) for prev_arg in previous_arguments]
    y0 = [loss_fn(prev_out) for prev_out in previous_outputs]

    # if we have not yet performed enough random steps, perform a random step
    if n_random_steps > len(previous_arguments):
        # deterministicaly sample from the space
        _random_points = Hammersly().generate(dimensions, n_random_steps)

        # choose a new random point we have not used
        _random_points = [p for p in _random_points if tuple(p) not in x0]
        point = _random_points[independent_random.randint(0, len(_random_points))]

        # perform the random step
        with additional_metadata({SEARCH_MODE: Modes.RANDOM}):
            gp_minimize(
                _objective,
                dimensions,
                x0=point,
                n_calls=1,
                n_initial_points=0,
            )

    else:
        # perform a single step of bayesian optimization
        with additional_metadata({SEARCH_MODE: Modes.BAYESIAN}):
            gp_minimize(
                _objective,
                dimensions,
                x0=x0,
                y0=y0,
                n_calls=1,
                n_initial_points=0,
            )


def is_in(space):
    def _in(a):
        return lambda x: x in a

    return {k: _in(v) for k, v in space.items()}


def optimize_step_for(
    experiment: Callable,
    space: Dict[str, Dimension],
    n_random_points: int,
    config_overides: Dict[str, Any] = None,
    root: str = "",
    loss_fn: Callable = None,
):
    root = root or experiment.__name__
    config_overides = config_overides or {}

    for k in config_overides:
        assert (
            k not in space
        ), f"cannot override parameter ({k}) that is being optimized over"

    df = experiments_matching(root, config=config_overides)
    experiments = convert_to_experiments(df)

    previous_arguments = [e.config for e in experiments]
    previous_outputs = [e.results for e in experiments]

    optimize_step(
        previous_arguments,
        previous_outputs,
        space,
        objective=experiment,
        n_random_steps=n_random_points,
        overrides=config_overides,
        loss_fn=loss_fn,
    )


# class Optimizer:
#     def __init__(
#         self,
#         experiment: Callable,
#         space: Dict[str, Dimension],
#         overrides: Dict[str, Any] = None,
#         loss_fn: Callable = None,
#         root: str = None,
#     ):
#         self.experiment = experiment
#         self.space = space
#         self.overrides = overrides
#         self.loss_fn = loss_fn
#         self.root = root

#     def random_step():
#         pass
