from digital_experiments.search.space import (
    Categorical,
    LogUniform,
    Space,
    Uniform,
)


def test_uniform():
    x = Uniform(3.6, 10.7)

    s = x.random_sample()
    unit_s = x.inverse_transform(s)

    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"

    assert x.contains(3.6), "Lower bound is not in the distribution"
    assert x.contains(10.7), "Upper bound is not in the distribution"
    assert not x.contains(3.5)


def test_log_uniform():
    x = LogUniform(1e-3, 1e4)

    s = x.random_sample()
    unit_s = x.inverse_transform(s)

    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"


def test_categorical():
    vals = ["a", "b", "c"]
    x = Categorical(vals)

    s = x.random_sample()
    unit_s = x.inverse_transform(s)

    assert s in vals, "Sampled value is not in the distribution"
    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"


def test_space():
    space = Space(
        x=Uniform(3.6, 10.7),
        y=LogUniform(1e-3, 1e4),
        z=Categorical(["a", "b", "c"]),
    )

    s = space.random_sample()
    unit_s = space.inverse_transform(s)

    assert space.contains(s), "Sampled value is not in the distribution"
    for k, v in s.items():
        assert space[k].contains(v), "Sampled value is not in the distribution"
    assert 0 <= unit_s[k] <= 1, "Unit value is not in the unit range"
