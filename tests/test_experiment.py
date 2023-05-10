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


def test_caching(tmp_path):
    calls = 0

    @experiment(absolute_root=tmp_path, cache=True)
    def add(a, b):
        nonlocal calls
        calls += 1
        return a + b

    add(1, 2)
    assert calls == 1

    ret = add(1, 2)
    assert calls == 1
    assert ret == 3

    add(1, 3)
    assert calls == 2


def test_verbose(capsys, tmp_path):
    @experiment(verbose=True, absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)
    captured = capsys.readouterr()

    assert "Running experiment" in captured.out
    assert "Finished experiment" in captured.out


def test_repr(tmp_path):
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)
    add(2, 3)
    assert repr(add) == "Experiment(add, observations=2)"
