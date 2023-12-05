import pytest
from digital_experiments import experiment
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
