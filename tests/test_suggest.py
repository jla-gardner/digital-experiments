import pytest

from digital_experiments.search.skopt_suggest import SKSuggester
from digital_experiments.search.space import (
    Categorical,
    Grid,
    LogUniform,
    Space,
    Uniform,
)
from digital_experiments.search.suggest import GridSuggester, RandomSuggester

SPACE = Space(
    x=Uniform(3.6, 10.7),
    y=LogUniform(1e-3, 1e4),
    z=Categorical(["a", "b", "c"]),
)


@pytest.mark.parametrize(
    "suggester_class",
    [
        RandomSuggester,
        SKSuggester,
    ],
)
def test_suggester(suggester_class):
    suggester = suggester_class(SPACE)

    point = suggester.suggest()
    unit_point = SPACE.inverse_transform(point)

    assert suggester.is_valid_point(point)
    assert SPACE.contains(point)

    fake_observation = 5.0
    suggester.tell(point, fake_observation)

    assert point in suggester.previous_points()
    assert unit_point in suggester.previous_unit_points()
    assert len(suggester.previous_points()) == 1
    assert len(suggester.previous_unit_points()) == 1


def test_grid():
    grid = Grid(
        x=range(3),
        y=[4, 5, 6],
        z=Categorical("ab"),
    )

    suggester = GridSuggester(grid)

    assert suggester.total_points == 3 * 3 * 2
    assert suggester.suggest() == {"x": 0, "y": 4, "z": "a"}

    suggester.tell({"x": 0, "y": 4, "z": "a"}, observation=5.0)

    assert suggester.suggest() == {"x": 1, "y": 4, "z": "a"}
