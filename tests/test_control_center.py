from pathlib import Path

from digital_experiments.control_center import (
    Run,
    current_directory,
    recording_run,
)

run = Run("id", Path("directory"))


def test_run():
    assert run.id == "id"
    assert run.directory == Path("directory")


def test_current_directory():
    with recording_run(run):
        assert current_directory() == run.directory.resolve()
