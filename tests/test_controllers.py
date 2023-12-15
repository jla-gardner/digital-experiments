import pytest
from digital_experiments import experiment
from digital_experiments.controllers import Controller, GridSearch, RandomSearch


def test_random_search(tmp_path):
    class RVS:
        def rvs(self, *args, **kwargs):
            return 1

    controller = RandomSearch(a=[1, 2, 3], b=RVS())
    suggestion = controller.suggest(None)  # type: ignore

    assert suggestion["a"] in [1, 2, 3]
    assert suggestion["b"] == 1

    @experiment(root=tmp_path)
    def example(a, b):
        return a * b

    controller.control(example, n=10)
    assert len(example.observations()) == 10

    with pytest.raises(TypeError):
        controller = RandomSearch(a=1)  # type: ignore
        controller.suggest(None)  # type: ignore


def test_no_suggestion(tmp_path):
    class NoSuggestion(Controller):
        def suggest(self, experiment):
            return None

    controller = NoSuggestion()
    assert controller.suggest(None) is None  # type: ignore

    @experiment(root=tmp_path)
    def example():
        pass

    controller.control(example, n=10)
    assert len(example.observations()) == 0


def test_grid_search(tmp_path):
    @experiment(root=tmp_path)
    def example(a, b):
        return a * b

    controller = GridSearch(a=[1, 2, 3], b=range(2))
    first = controller.suggest(example)
    assert first == {"a": 1, "b": 0}

    assert len([x for x in controller._grid_iter()]) == 6

    controller.control(example, n=10)
    assert len(example.observations()) == 6, "Only 6 experiments are possible"

    assert controller.suggest(example) is None

    with pytest.raises(TypeError):
        controller = GridSearch(a=1)  # type: ignore
