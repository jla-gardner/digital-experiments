from digital_experiments.control_center import additional_metadata
from digital_experiments.metadata import record_metadata


def f(x):
    return x + 1


def test_record_metadata():
    args = [1]
    kwargs = {}
    metadata, result = record_metadata(f, args, kwargs)
    assert result == 2, "metadata collection has changed the result"

    assert "time" in metadata, "metadata should include the time"
    assert metadata["time"]["duration"] > 0


def test_additional_metadata():
    args = [10]
    kwargs = {}

    extra_metadata = {"foo": "bar"}
    with additional_metadata(extra_metadata):
        metadata, result = record_metadata(f, args, kwargs)
        assert result == 11
        assert (
            metadata["foo"] == "bar"
        ), "additional metadata should be included"
