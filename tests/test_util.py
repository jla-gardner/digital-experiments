import sys

import pytest

from digital_experiments import experiment
from digital_experiments.experiment import get_passed_kwargs_for
from digital_experiments.util import (
    dict_equality,
    flatten,
    generate_id,
    get_passed_kwargs,
    intersect,
    merge_dicts,
    unflatten,
    union,
)

nested = {"a": 1, "b": {"c": 2, "d": {"f": "hi"}}}
flat = {"a": 1, "b_c": 2, "b_d_f": "hi"}


def test_flatten():
    assert flatten(nested, seperator="_") == flat


def test_unflatten():
    assert unflatten(flat, seperator="_") == nested


def test_id_generation():
    id1 = generate_id()
    id2 = generate_id()
    assert id1 != id2, "IDs should be unique"
    assert id1 < id2, "IDs should be ordered by time"


def test_union():
    assert union(([1, 2, 3], [2, 3, 4])) == {1, 2, 3, 4}
    assert union(("hi", "there")) == {"h", "i", "t", "e", "r"}


def test_intersect():
    assert intersect(([1, 2, 3], [2, 3, 4])) == {2, 3}
    assert intersect(("hi", "there")) == {"h"}


def test_dict_equality():
    assert dict_equality({"a": 1, "b": 2}, {"b": 2, "a": 1})

    nested1 = {"a": 1, "b": {"c": 2, "d": {"f": "hi"}}}
    nested2 = {"a": 1, "b": {"c": 2, "d": {"f": "hi"}}}
    assert dict_equality(nested1, nested2)

    nested1 = {"a": 1, "b": {"c": 2, "d": {"f": "hi"}}}
    nested2 = {"a": 1, "b": {"c": 2, "d": {"f": "bye"}}}
    assert not dict_equality(nested1, nested2)

    assert not dict_equality({"a": 1, "b": 2}, nested1)
    assert not dict_equality(nested1, {"a": 1, "b": 2})

    assert not dict_equality({"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3})


def test_kwarg_parsing(tmp_path):
    sys.argv = ["test.py", "a=1", "b=2", "c=3", "d"]
    with pytest.raises(ValueError, match="Invalid keyword argument passed"):
        get_passed_kwargs()

    sys.argv = ["test.py", "a=1", "b=False", "c=hello"]

    # get_passed_kwargs should return a dict of strings
    assert get_passed_kwargs() == {"a": "1", "b": "False", "c": "hello"}

    @experiment(absolute_root=tmp_path)
    def test_experiment(a: int, b=False, *, c: str):
        return a + int(b) + len(c)

    # get_passed_kwargs_for should return a dict of the correct types
    # by inferring them either from
    #  - the defaults in a signature
    #  - type hints
    kwargs = get_passed_kwargs_for(test_experiment)
    assert kwargs == {"a": 1, "b": False, "c": "hello"}


def test_merge_dicts():
    d1 = {"a": {"b": 1, "c": 2}, "d": 3}
    d2 = {"a": {"e": 5}, "f": 6}

    # ensure correct nested merge
    assert merge_dicts(d1, d2) == {"a": {"b": 1, "c": 2, "e": 5}, "d": 3, "f": 6}

    bad_d2 = {"a": 1}
    with pytest.raises(ValueError):
        merge_dicts(d1, bad_d2)

    bad_d2 = {"d": 4}
    with pytest.raises(ValueError):
        merge_dicts(d1, bad_d2)

    good_d2 = {"d": 3}
    assert merge_dicts(d1, good_d2) == {"a": {"b": 1, "c": 2}, "d": 3}
