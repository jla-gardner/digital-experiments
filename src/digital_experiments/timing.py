import contextlib
from datetime import datetime

from . import control_center as ControlCenter


def now():
    """
    get the current timestamp
    """
    return datetime.now().timestamp()


@contextlib.contextmanager
def time_block(name: str):
    """
    context manager for timing a section of an experiment

    start, duration and end are saved in metadata['timing'][name]

    Example:
    --------
    >>> @experiment
    >>> def my_experiment():
    ...     with time_block("load"):
    ...         data = load_data()
    ...     with time_block("train"):
    ...         model = train_model(data)
    >>> my_experiment()
    >>> observation = my_experiment.observations[-1]
    >>> observation.metadata["timing"]["load"]["duration"]
    1.234
    """
    start = now()
    yield
    end = now()
    ControlCenter.add_metadata(
        {"timing": {name: {"start": start, "end": end, "duration": end - start}}}
    )


def mark(name: str):
    """
    record a mark in the experiment's metadata

    start, each name and end are saved in metadata['timing_marks']

    Example:
    --------
    >>> @experiment
    >>> def my_experiment():
    ...     mark("start")
    ...     data = load_data()
    ...     mark("data loaded")
    ...     model = train_model(data)
    ...     mark("model trained")
    >>> my_experiment()
    >>> observation = my_experiment.observations[-1]
    >>> observation.metadata["marks"]
    [("start", 0.0), ("data loaded", 1.234), ("model trained", 2.345)]
    """
    run = ControlCenter.current_run()
    if "timing_marks" not in run.metadata:
        run.metadata["timing_marks"] = []
    run.metadata["timing_marks"].append((name, now()))
