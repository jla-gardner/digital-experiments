import pytest

from digital_experiments.backends import (
    Backend,
    available_backends,
    backend_from_type,
    this_is_a_backend,
)
from digital_experiments.observation import Observation


def test_incomplete_subclassing():
    """
    A backend must implement save and all_observations
    """

    @this_is_a_backend("incorrect")
    class IncorrectBackend(Backend):
        pass

    with pytest.raises(TypeError):
        IncorrectBackend()


def test_failure_to_register(tmp_path):
    """
    A backend must be registered with @this_is_a_backend
    """

    class IncorrectBackend(Backend):
        def save(self, obs):
            pass

        def all_observations(self):
            pass

    with pytest.raises(ValueError):
        IncorrectBackend(tmp_path)


def test_correct_backend(tmp_path):
    """
    A backend can be registered and instantiated
    """

    @this_is_a_backend("correct")
    class CorrectBackend(Backend):
        def save(self, obs):
            pass

        def all_observations(self):
            pass

    CorrectBackend(tmp_path)


def test_unknown_backend_type():
    """
    The backend type must be registered
    """

    with pytest.raises(ValueError):
        backend_from_type("unknown")


@pytest.mark.parametrize("backend", available_backends())
def test_available_backends(backend, tmp_path):
    """
    All available backends can be instantiated and used
    """

    klass = backend_from_type(backend)
    assert klass.name == backend

    home = tmp_path / backend
    home.mkdir()
    backend = klass(home)
    backend.save(Observation(id="1", config={"a": 1, "b": 2}, result=1))

    observations = backend.all_observations()
    assert len(observations) == 1
    assert observations[0].id == "1"
    assert observations[0].config == {"a": 1, "b": 2}
    assert observations[0].result == 1
