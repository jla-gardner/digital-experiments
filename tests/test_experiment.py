import shutil
from pathlib import Path

from digital_experiments.experiment import experiment


def test_absolute_path(tmp_path):
    if tmp_path.exists():
        shutil.rmtree(tmp_path)

    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)

    assert len(add.observations) == 1
    observation = add.observations[0]
    assert observation.config == {"a": 1, "b": 2}
    assert observation.result == 3


def test_relative_path():
    path = Path(__file__).parent / "experiments/test"
    if path.exists():
        shutil.rmtree(path)

    @experiment(root="experiments/test")
    def add(a, b):
        return a + b

    add(1, 2)

    assert path.exists()

    assert len(add.observations) == 1
    observation = add.observations[0]
    assert observation.config == {"a": 1, "b": 2}
    assert observation.result == 3
