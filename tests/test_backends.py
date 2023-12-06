import pytest
from digital_experiments.backends import (
    _ALL_BACKENDS,
    Backend,
    instantiate_backend,
    register_backend,
)
from digital_experiments.core import Observation


def test_incomplete_subclassing(tmp_path):
    """A backend must implement all abstract methods"""

    @register_backend("incorrect")
    class IncorrectBackend(Backend):
        pass

    with pytest.raises(TypeError):
        IncorrectBackend(tmp_path)


def test_failure_to_register(tmp_path):
    """A backend must be registered with @register_backend"""

    with pytest.raises(ValueError):
        instantiate_backend("un-registered", tmp_path)


@pytest.mark.parametrize("backend", _ALL_BACKENDS.keys())
def test_success_to_register(backend, tmp_path):
    """A backend must be registered with @register_backend"""

    backend = instantiate_backend(backend, tmp_path)
    assert isinstance(backend, Backend)

    observation = Observation(
        id="1", config={"a": 1, "b": 2}, result=1, metadata={}
    )
    backend.record(observation)

    loaded = backend.load("1")
    assert loaded == observation

    assert backend.all_ids() == ["1"]
