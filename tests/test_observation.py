from digital_experiments.observation import Observation


def test_observation():
    obs = Observation(
        id="1",
        config={"a": 1, "b": 2},
        result={"c": 3},
    )

    assert obs.metadata == {}

    rep = repr(obs)
    assert all([x in rep for x in ["Observation", "config", "result"]])
