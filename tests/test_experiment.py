import os
from pathlib import Path

import pytest
from digital_experiments import current_dir, experiment
from digital_experiments.backends import _ALL_BACKENDS


@pytest.mark.parametrize("backend", _ALL_BACKENDS)
def test_experiment(backend: str, tmp_path):
    @experiment(backend=backend, root=tmp_path)
    def square(x):
        return x**2

    assert square(2) == 4, "square(2) should be 4"

    observations = square.observations()
    assert len(observations) == 1, "there should be one observation"
    assert observations[0].result == 4, "result should be 4"


def test_caching(tmp_path):
    @experiment(root=tmp_path, cache=True)
    def square(x):
        return x**2

    assert square(2) == 4, "square(2) should be 4"
    assert square(2) == 4, "square(2) should be 4"

    observations = square.observations()
    assert len(observations) == 1, "there should be one observation"


def test_root():
    os.environ["DE_ROOT"] = "test-loc"

    @experiment
    def square(x):
        return x**2

    assert square.backend.root == Path("test-loc")

    del os.environ["DE_ROOT"]

    @experiment
    def cube(x):
        return x**3

    assert cube.backend.root == Path("experiments/cube")


def test_artefacts(tmp_path):
    @experiment(root=tmp_path)
    def example():
        (current_dir() / "results.txt").write_text("hello world")

    assert not example.artefacts("non-existent-id")

    example()
    id = example.observations()[-1].id
    artefacts = example.artefacts(id)
    assert len(artefacts) == 1
    assert "hello world" in artefacts[0].read_text()

    assert example.artefacts("non-existent-id") == []


def test_to_dataframe(tmp_path):
    @experiment(root=tmp_path)
    def example(a, b=2):
        return a + b

    df = example.to_dataframe()
    assert len(df) == 0

    example(1)
    df = example.to_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["config.a"] == 1
    assert df.iloc[0]["config.b"] == 2
    assert df.iloc[0].result == 3
