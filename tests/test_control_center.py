from pathlib import Path

import pytest

from digital_experiments import experiment
from digital_experiments.control_center import (
    Run,
    add_metadata,
    current_directory,
    dont_record,
    end_run,
)

run = Run("id", Path("directory"))


def test_run():
    assert run.id == "id"
    assert run.directory == Path("directory")


def test_dont_record(tmp_path):
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)
    assert len(add.observations) == 1

    with dont_record():
        add(1, 2)

    assert len(add.observations) == 1


def test_errors():
    # no current directory outside of experiment
    with pytest.raises(Exception):
        current_directory()

    with pytest.raises(RuntimeError):
        add_metadata({})

    with pytest.raises(RuntimeError):
        end_run()
