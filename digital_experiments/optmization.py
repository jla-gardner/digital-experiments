from pathlib import Path

import numpy as np
from skopt import Space, gp_minimize
from skopt.sampler import Hammersly
from skopt.space import Categorical, Integer, Real
from skopt.utils import use_named_args

from digital_experiments.core import all_experiments, reset_context, set_context


def optimize_step(experiment, loss, n_random_points, space, root=None):
    root = root or experiment.__name__

    previous_experiments = all_experiments(Path(root))
    previous_config = [tuple(e.config.values()) for e in previous_experiments]
    previous_results = [loss(e.result) for e in previous_experiments]

    _space = []
    for k, v in space.items():
        v.name = k
        _space.append(v)

    __actual_space = Space(_space)
    to_keep = [i for i, c in enumerate(previous_config) if c in __actual_space]
    previous_config = [previous_config[i] for i in to_keep]
    previous_results = [previous_results[i] for i in to_keep]

    @use_named_args(_space)
    def objective(**kwargs):
        results = experiment(**kwargs)
        return loss(results)

    random_search_phase = n_random_points > len(previous_config) + 1

    if random_search_phase:
        set_context("random-search")
        _random_points = Hammersly().generate(
            __actual_space.dimensions, n_random_points
        )
        _random_points = [p for p in _random_points if tuple(p) not in previous_config]
        point = _random_points[np.random.randint(0, len(_random_points))]
        gp_minimize(
            objective,
            _space,
            x0=point,
            n_calls=1,
            n_initial_points=0,
        )

    else:
        set_context("bayesian-optimization")
        gp_minimize(
            objective,
            _space,
            x0=previous_config,
            y0=previous_results,
            n_calls=1,
            n_initial_points=0,
        )
    reset_context()
