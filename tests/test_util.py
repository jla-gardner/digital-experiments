from digital_experiments.util import flatten, generate_id


def test_flatten():
    nested = {"a": 1, "b": {"c": 2, "d": "hi"}}
    flat = {"a": 1, "b_c": 2, "b_d": "hi"}

    assert flatten(nested, seperator="_") == flat


def test_id_generation():
    id1 = generate_id()
    id2 = generate_id()
    assert id1 != id2, "IDs should be unique"
    assert id1 < id2, "IDs should be ordered by time"
