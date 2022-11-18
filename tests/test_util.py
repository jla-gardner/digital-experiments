import numpy as np

from digital_experiments.util import flatten, pretty_json, unflatten

nested = {"a": 1, "b": {"c": 2, "d": "hi"}}
flat = {"a": 1, "b.c": 2, "b.d": "hi"}

def test_flatten():
    assert flatten(nested) == flat

def test_unflatten():
    assert unflatten(flat) == nested

def test_pretty_json():
    assert pretty_json(nested) == """{
    "a": 1,
    "b": {
        "c": 2,
        "d": "hi"
    }
}"""
    # check that serialising numpy arrays works
    assert pretty_json({'a': np.array([1, 2, 3])}) == """{
    "a": [
        1,
        2,
        3
    ]
}"""