import pytest

from digital_experiments import experiment
from digital_experiments.minimize import minimizer
from digital_experiments.search.space import Uniform


def test_minimizer(tmp_path):
    @experiment(absolute_root=tmp_path)
    def quadratic(x):
        return x**2

    quadratic(1)
    quadratic(-1)

    minim = minimizer(
        quadratic,
        space={"x": Uniform(-3, 3)},
        n_explore_steps=3,
    )

    for _ in range(7):
        minim.step()

    best = minim.best_point()["x"]

    assert best == pytest.approx(0, abs=0.1)
    assert len(minim.steps) == 2 + 7, "9 steps: 2 manual, 1 explore, 7 exploit"
