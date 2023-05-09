import pytest

from digital_experiments import experiment
from digital_experiments.observation import Observation
from digital_experiments.querying import filtered_observations, matches


def test_matching():
    thing = {"a": 1, "b": 2, "c": 3}
    template = {"a": 1, "b": 2}

    assert matches(thing, template), "Should match"


def test_filtered_observations():
    observations = [
        Observation(
            id="1",
            config={"a": 1, "b": 2},
            result={"c": 3},
            metadata={"d": 4},
        ),
        Observation(
            id="2",
            config={"a": 1, "b": 2},
            result={"c": 4},
            metadata={"d": 4},
        ),
        Observation(
            id="3",
            config={"a": 1, "b": 2},
            result={"c": 5},
            metadata={"d": 4},
        ),
    ]

    filtered = filtered_observations(observations, config={"a": 1})

    assert len(filtered) == 3, "Should match all"
    assert filtered[0].id == "1", "Should match all"

    filtered = filtered_observations(observations, config={"a": 1}, result={"c": 5})

    assert len(filtered) == 1, "Should only match one"
    assert filtered[0].id == "3", "Should only match one"


def test_to_dataframe(tmp_path):
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    with pytest.warns(UserWarning, match="No observations"):
        df = add.to_dataframe()
        assert len(df) == 0, "Should have no rows"

    add(1, 2)
    add(1, 3)

    df = add.to_dataframe()
    assert len(df) == 2, "Should have two rows"
