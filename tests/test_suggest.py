import pytest

from digital_experiments.search.distributions import Categorical, LogUniform, Uniform
from digital_experiments.search.skopt_suggest import SKSuggester
from digital_experiments.search.space import Space
from digital_experiments.search.suggest import (
    GridSuggester,
    NamedBooleanGrid,
    RandomSuggester,
)

SPACE = Space(
    x=Uniform(3.6, 10.7),
    y=LogUniform(1e-3, 1e4),
    z=Categorical(["a", "b", "c"]),
)


def test_boolean_grid():
    things = dict(x=[1, 2, 3], y="hi")
    grid = NamedBooleanGrid(things)

    assert grid.total_hits() == 0
    assert grid.total_misses() == 6

    assert grid.first_miss() == {"x": 1, "y": "h"}

    grid.hit({"x": 1, "y": "h"})
    # test that grid iterates over values in correct order
    assert grid.first_miss() == {"x": 1, "y": "i"}

    for _ in range(5):
        grid.hit(grid.first_miss())

    with pytest.raises(ValueError, match="Grid is full"):
        grid.first_miss()

    assert grid.total_hits() == 6
    assert grid.total_misses() == 0


def test_grid_suggester():
    space = {"x": [1, 2, 3], "y": "hi"}
    suggester = GridSuggester(space)

    assert suggester.suggest() == {"x": 1, "y": "h"}

    suggester.tell({"x": 1, "y": "h"}, observation=5.0)
    assert suggester.suggest() == {"x": 1, "y": "i"}


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
    unit_point = SPACE.transform_to_unit_range(point)

    assert suggester.is_valid_point(point)
    assert SPACE.contains(point)

    fake_observation = 5.0
    suggester.tell(point, fake_observation)

    assert point in suggester.previous_points()
    assert unit_point in suggester.previous_unit_points()
    assert len(suggester.previous_points()) == 1
    assert len(suggester.previous_unit_points()) == 1


# def test_grid():
#     grid = dict(
#         x=range(3),
#         y=[4, 5, 6],
#         z=Categorical("ab"),
#     )

#     suggester = GridSuggester(grid)

#     assert suggester.suggest() == {"x": 0, "y": 4, "z": "a"}

#     suggester.tell({"x": 0, "y": 4, "z": "a"}, observation=5.0)
#     assert suggester.suggest() == {"x": 1, "y": 4, "z": "a"}


# def test_grid_suggestions():
#     """
#     test that the suggested points cover the space
#     and that the points are suggested in the correct order,
#     i.e first dimension (x) changes fastest
#     """

#     suggester = GridSuggester(
#         dict(
#             x=[1, 2],
#             y=[3, 4],
#         )
#     )

#     true_points = [
#         {"x": 1, "y": 3},
#         {"x": 2, "y": 3},
#         {"x": 1, "y": 4},
#         {"x": 2, "y": 4},
#     ]

#     for idx, point in enumerate(true_points):
#         assert suggester.point_from(idx) == point, "point_from failed"
#         assert suggester.idx_from(point) == idx, "idx_from failed"

#     suggested_points = []
#     for _ in range(4):
#         point = suggester.suggest()
#         suggester.tell(point, observation=5.0)
#         suggested_points.append(point)

#     assert suggested_points == true_points
