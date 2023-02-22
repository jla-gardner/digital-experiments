import pytest

from digital_experiments.backends import (
    Backend,
    backend_from_type,
    this_is_a_backend,
)
from digital_experiments.observation import Observation


def mock_backend_filestructure(path, backend_name):
    path.mkdir(parents=True, exist_ok=True)
    (path / ".code").touch()
    (path / ".backend").write_text(backend_name)


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

    mock_backend_filestructure(tmp_path, "incorrect")

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

    mock_backend_filestructure(tmp_path, "correct")

    CorrectBackend(tmp_path)


def test_unknown_backend_type():
    """
    The backend type must be registered
    """

    with pytest.raises(ValueError):
        backend_from_type("unknown")


def test_available_backends(tmp_path):
    observation = Observation(id="1", config={"a": 1, "b": 2}, result=1)

    for backend in ("yaml",):
        # will throw an error if doesn't exist
        klass = backend_from_type(backend)
        assert klass.name == backend

        home = tmp_path / backend
        mock_backend_filestructure(home, backend)
        actual_backend = klass(home)
        actual_backend.save(observation)

        assert actual_backend.all_observations() == [observation]
