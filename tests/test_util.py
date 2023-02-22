from digital_experiments.util import flatten, generate_id

nested = {"a": 1, "b": {"c": 2, "d": "hi"}}
flat = {"a": 1, "b_c": 2, "b_d": "hi"}


def test_flatten():
    assert flatten(nested) == flat


def test_id_generation():
    id1 = generate_id()
    id2 = generate_id()
    assert id1 != id2, "IDs should be unique"
    assert id1 < id2, "IDs should be ordered by time"
