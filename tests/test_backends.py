import pytest
from digital_experiments.backends import Backend, instantiate_backend, register_backend


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


# @pytest.mark.parametrize("backend", available_backends())
# def test_available_backends(backend, tmp_path):
#     """
#     All available backends can be instantiated and used
#     """

#     klass = backend_from_type(backend)
#     assert klass.name == backend

#     home = tmp_path / backend
#     home.mkdir()
#     backend_instance = klass(home)
#     backend_instance.save(Observation(id="1", config={"a": 1, "b": 2}, result=1))

#     observations = backend_instance.all_observations()
#     assert len(observations) == 1
#     assert observations[0].id == "1"
#     assert observations[0].config == {"a": 1, "b": 2}
#     assert observations[0].result == 1

#     @experiment(backend=backend, absolute_root=tmp_path)
#     def add(a, b):
#         return a + b

#     add(1, 2)

#     assert len(add.observations) == 1
