import pytest
from digital_experiments.callbacks import (
    CodeVersioning,
    GlobalStateNotifier,
    Logging,
    SaveLogs,
    Timing,
    current_dir,
    current_id,
    time_block,
)
from digital_experiments.core import Observation


def test_global_state(tmp_path):
    callback = GlobalStateNotifier(tmp_path)

    id, config = "1", {"a": 1}
    callback.start(id, config)

    assert current_id() == id
    assert current_dir() == tmp_path / "storage" / id

    callback.end(Observation(id=id, config=config, result=1, metadata={}))

    with pytest.raises(RuntimeError, match="No experiment running"):
        current_id()

    with pytest.raises(RuntimeError, match="No experiment running"):
        current_dir()


def dummy(x):
    return x


def test_code_versioning():
    callback = CodeVersioning()

    callback.setup(dummy)

    code = "def dummy(x):\n    return x\n"
    assert callback.code == code

    obs = Observation(id="1", config={}, result=1, metadata={})
    callback.end(obs)
    assert obs.metadata["code"] == code


def test_logging(capsys):
    noisy_callback = Logging(verbose=True)

    noisy_callback.setup(dummy)
    noisy_callback.start("1", {})
    captured = capsys.readouterr()
    assert "starting experiment" in captured.out

    result = "a really long string that should be truncated" * 10
    noisy_callback.end(
        Observation(id="1", config={}, result=result, metadata={})
    )
    captured = capsys.readouterr()
    assert "finished experiment" in captured.out
    # assert "..." in captured.out
    assert result not in captured.out

    quiet_callback = Logging(verbose=False)

    quiet_callback.setup(dummy)
    quiet_callback.start("1", {})
    captured = capsys.readouterr()
    assert captured.out == ""

    quiet_callback.end(Observation(id="1", config={}, result=1, metadata={}))
    captured = capsys.readouterr()
    assert captured.out == ""


def test_timing():
    callback = Timing()

    callback.start("1", {})

    with time_block("custom-block"):
        pass

    metadata = {}
    callback.end(Observation(id="1", config={}, result=1, metadata=metadata))

    assert "custom-block" in metadata["timing"]
    assert "start" in metadata["timing"]["total"]

    with pytest.raises(RuntimeError, match="No experiment running"):  # noqa: SIM117
        with time_block("custom-block"):
            pass


def test_save_logs(tmp_path, capsys):
    callbacks = [
        GlobalStateNotifier(tmp_path),
        SaveLogs("logs.txt"),
    ]

    for callback in callbacks:
        callback.setup(dummy)

    id, metadata = "1", {}
    for callback in callbacks:
        callback.start(id, {})

    print("hello world", flush=True)

    obs = Observation(id=id, config={}, result=1, metadata=metadata)
    for callback in reversed(callbacks):
        callback.end(obs)

    assert (
        tmp_path / "storage" / id / "logs.txt"
    ).read_text() == "hello world\n"

    # test printing still works
    print("other text")
    captured = capsys.readouterr()
    assert "other text" in captured.out
