import pytest

from digital_experiments.search.distributions import Categorical, LogUniform, Uniform
from digital_experiments.search.space import Space


def test_space():
    space = Space(
        x=Uniform(3.6, 10.7),
        y=LogUniform(1e-3, 1e4),
        z=Categorical(["a", "b", "c"]),
    )

    s = space.random_sample()
    unit_s = space.transform_to_unit_range(s)

    assert space.contains(s), "Sampled value is not in the distribution"
    for k, v in s.items():
        assert space[k].contains(v), "Sampled value is not in the distribution"
    assert 0 <= unit_s[k] <= 1, "Unit value is not in the unit range"


def test_incorrect_args():
    with pytest.raises(ValueError):
        Space(x=1)
