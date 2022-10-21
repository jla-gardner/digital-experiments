from pathlib import Path
from random import randint

from skopt import Space, gp_minimize
from skopt.sampler import Halton
from skopt.space import Categorical, Integer, Real
from skopt.utils import use_named_args

from digital_experiments.core import all_experiments


def optimize_step(experiment, loss, root, n_random_points, space):

    previous_experiments = all_experiments(Path(root))
    previous_config = [tuple(e.config.values()) for e in previous_experiments]
    previous_results = [loss(e.results) for e in previous_experiments]

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
        print("Using Random Search")
        _random_points = Halton().generate(__actual_space.dimensions, n_random_points)
        point = _random_points[randint(len(previous_config), n_random_points - 1)]
        gp_minimize(
            objective,
            _space,
            x0=point,
            n_calls=1,
            n_initial_points=0,
        )

    else:
        print("Using Bayesian Optimization")
        gp_minimize(
            objective,
            _space,
            x0=previous_config,
            y0=previous_results,
            n_calls=1,
            n_initial_points=0,
        )
