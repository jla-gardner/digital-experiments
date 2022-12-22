import shutil
from pathlib import Path

from digital_experiments import experiment
from digital_experiments.optmization import Real, optimize_step_for


def basic_opt(backend: str):
    @experiment(backend=backend)
    def my_opt_experiment(x):
        return (x - 1) ** 2

    path = Path("my_opt_experiment")
    info = f"(backend: {backend})"
    print(info)

    space = {"x": Real(-0.7, 2.6)}

    for i in range(5):
        optimize_step_for(my_opt_experiment, space, n_random_points=5)

    shutil.rmtree(path)


def test_basic_experiments():
    basic_opt("json")
    basic_opt("csv")
