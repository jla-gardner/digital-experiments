import pytest

from digital_experiments import experiment
from digital_experiments.inspection import code_for
from digital_experiments.observation import Observation
from digital_experiments.save_and_load.backend import (
    Backend,
    _available_backends,
    backend_type_from_name,
    this_is_a_backend,
)


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
        IncorrectBackend(tmp_path, "fake code")


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

    CorrectBackend(tmp_path, "fake code")


def test_unknown_backend_type():
    """
    The backend type must be registered
    """

    with pytest.raises(ValueError):
        backend_type_from_name("unknown")


@pytest.mark.parametrize("backend", _available_backends())
def test_available_backends(backend, tmp_path):
    """
    All available backends can be instantiated and used
    """

    fake_code = code_for(lambda: 1 + 1)
    klass = backend_type_from_name(backend)
    assert klass.name == backend

    home = tmp_path / backend
    home.mkdir()
    backend_instance = klass(home, fake_code)
    backend_instance.save(Observation(id="1", config={"a": 1, "b": 2}, result=1))

    observations = backend_instance.all_observations()
    assert len(observations) == 1
    assert observations[0].id == "1"
    assert observations[0].config == {"a": 1, "b": 2}
    assert observations[0].result == 1

    @experiment(backend=backend, absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)

    assert len(add.observations) == 1
