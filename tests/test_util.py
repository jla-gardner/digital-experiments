from digital_experiments.util import (
    flatten,
    generate_id,
    intersect,
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
