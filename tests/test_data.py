import pytest

from digital_experiments.data import Data


def test_creation():
    d = Data(x=1, y=2)

    # check dot notation access
    assert d.x == 1

    # check dict access
    assert d["y"] == 2

    # check is in fact a dict
    assert isinstance(d, dict)

    # check that we can't access non-existent keys
    with pytest.raises(KeyError):
        d["z"]

    # check that we can delete things
    del d["x"]
    assert "x" not in d


def test_data_math():
    d = Data(x=1, y=2)

    # check addition
    assert d + 1 == Data(x=2, y=3)  # normal addition
    assert 1 + d == Data(x=2, y=3)  # reverse addition
    assert d + Data(x=4, y=2) == Data(x=5, y=4)

    # check subtraction
    assert d - 1 == Data(x=0, y=1)  # normal subtraction
    assert 1 - d == Data(x=0, y=-1)  # reverse subtraction
    assert d - Data(x=4, y=2) == Data(x=-3, y=0)

    # check multiplication
    assert d * 2 == Data(x=2, y=4)  # normal multiplication
    assert 2 * d == Data(x=2, y=4)  # reverse multiplication
    assert d * Data(x=4, y=2) == Data(x=4, y=4)

    # check division
    assert d / 2 == Data(x=0.5, y=1)  # normal division
    assert 2 / d == Data(x=2, y=1)  # reverse division
    assert d / Data(x=4, y=2) == Data(x=0.25, y=1)

    # check floor division
    assert d // 2 == Data(x=0, y=1)  # normal floor division
    assert 2 // d == Data(x=2, y=1)  # reverse floor division
    assert d // Data(x=4, y=2) == Data(x=0, y=1)

    # check modulo
    assert d % 2 == Data(x=1, y=0)  # normal modulo
    assert 2 % d == Data(x=0, y=0)  # reverse modulo
    assert d % Data(x=4, y=2) == Data(x=1, y=0)

    # check power
    assert d**2 == Data(x=1, y=4)  # normal power
    assert 2**d == Data(x=2, y=4)  # reverse power
    assert d ** Data(x=4, y=2) == Data(x=1, y=4)


def test_map():
    data = Data(a=[1, 2, 3], b=[4, 5, 6, 7])
    assert data.map(sum) == Data({"a": 6, "b": 22})


def test_apply():
    def concatenate(*lists):
        return [item for sublist in lists for item in sublist]

    d1 = Data(a=[1, 2], b=[4, 5])
    d2 = Data(a=[8, 9], b=[11, 12])
    assert Data.apply(concatenate, d1, d2) == Data(a=[1, 2, 8, 9], b=[4, 5, 11, 12])

    wrong_d2 = Data(c=[8, 9], d=[11, 12])
    with pytest.raises(ValueError):
        Data.apply(concatenate, d1, wrong_d2)
