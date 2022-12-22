import shutil
from pathlib import Path

from digital_experiments import experiment


def basic_experiment(backend: str):
    @experiment(backend=backend)
    def my_experiment():
        return 42

    path = Path("my_experiment")
    info = f"(backend: {backend})"
    
    assert not path.exists(), "The experiment should not have been saved yet" + info
    assert my_experiment() == 42, "Experiment should return the correct value" + info
    assert path.exists(), "The experiment should have been saved" + info

    shutil.rmtree(path)


def test_basic_experiments():
    basic_experiment("csv")
    basic_experiment("json")
