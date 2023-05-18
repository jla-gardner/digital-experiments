from digital_experiments.search.distributions import (
    Categorical,
    LogUniform,
    Uniform,
    convert_from_shorthand,
)


def test_uniform():
    x = Uniform(3.6, 10.7)

    s = x.random_sample()
    unit_s = x.transform_to_unit_range(s)

    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"

    assert x.contains(3.6), "Lower bound is not in the distribution"
    assert x.contains(10.7), "Upper bound is not in the distribution"
    assert not x.contains(3.5)


def test_log_uniform():
    x = LogUniform(1e-3, 1e4)

    s = x.random_sample()
    unit_s = x.transform_to_unit_range(s)

    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"


def test_categorical():
    vals = ["a", "b", "c"]
    x = Categorical(vals)

    s = x.random_sample()
    unit_s = x.transform_to_unit_range(s)

    assert s in vals, "Sampled value is not in the distribution"
    assert x.contains(s), "Sampled value is not in the distribution"
    assert 0 <= unit_s <= 1, "Unit value is not in the unit range"


def test_from_shorthand():
    dims = {"foo": [1, 2, 3], "bar": Uniform(0, 1)}
    new_dims = convert_from_shorthand(dims)

    assert isinstance(new_dims["foo"], Categorical)
    assert isinstance(new_dims["bar"], Uniform)
