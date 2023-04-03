import inspect
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

from filelock import FileLock

from digital_experiments.experiment import Experiment


def generate_id():
    return datetime.now().strftime("%y.%m.%d-%H.%M.%S-%f")


def flatten(dict_of_dicts: Dict[str, Dict], seperator="_") -> Dict[str, Any]:
    """
    Flatten a dictionary of dictionaries

    Parameters
    ----------
    dict_of_dicts: dict
        dictionary of dictionaries
    seperator: str
        seperator to use when flattening

    Returns
    -------
    dict
        flattened dictionary

    Examples
    --------
    >>> flatten({"a": {"b": 1, "c": 2}, "d": 3})
    {'a_b': 1, 'a_c': 2, 'd': 3}
    """

    result = {}
    for k, v in dict_of_dicts.items():
        if isinstance(v, dict):
            v = flatten(v, seperator)
            for k2, v2 in v.items():
                result[k + seperator + k2] = v2
        else:
            result[k] = v
    return result


def unflatten(dictionary, seperator="."):
    """
    unflatten a single level dict into a nested dict

    Parameters
    ----------
    dictionary: dict
        dictionary to unflatten
    seperator: str
        seperator to use when unflattening

    Returns
    -------
    dict
        unflattened dictionary

    Examples
    --------
    >>> unflatten({"a_b": 1, "a_c": 2, "d": 3})
    {'a': {'b': 1, 'c': 2}, 'd': 3}
    """

    result = {}
    for k, v in dictionary.items():
        if seperator not in k:
            result[k] = v
            continue

        k1, k2 = k.split(seperator, 1)
        if k1 not in result:
            result[k1] = {}
        result[k1][k2] = v

    # result is now a dict of str to either dict or value
    # the nested dicts might still contain seperators
    for k, v in result.items():
        if not isinstance(v, dict):
            continue
        result[k] = unflatten(v, seperator)

    return result


def union(things):
    return set.union(*[set(t) for t in things])


def intersect(things):
    return set.intersection(*[set(t) for t in things])


def is_in(thing):
    def _is_in(things):
        return thing in things

    return _is_in


@contextmanager
def exclusive_file_access(filehandle: Union[str, Path], mode: str = "r"):
    if isinstance(filehandle, str):
        filehandle = Path(filehandle)

    lock_path = filehandle.with_suffix(".lock")
    lock = FileLock(lock_path)
    with lock:
        if not filehandle.exists():
            filehandle.touch()
        with open(filehandle, mode) as f:
            yield f

    # remove the lock file
    lock_path.unlink(missing_ok=True)


def get_passed_kwargs() -> Dict[str, str]:
    passed = sys.argv[1:]
    kwargs = {}
    for arg in passed:
        try:
            k, v = arg.split("=")
            kwargs[k] = v
        except ValueError:
            raise ValueError(
                f"Invalid keyword argument passed. Expected the format key=value, got {arg}"
            )
    return kwargs


def interpret(value: str, parameter: inspect.Parameter) -> Any:
    is_str = isinstance(parameter.default, str) or parameter.annotation == str
    return value if is_str else eval(value)


# TODO update this to take an Experiment object
def get_passed_kwargs_for(experiment: Experiment):
    kwargs: Dict[str, str] = get_passed_kwargs()

    relevant_kwargs = {}
    signature = inspect.signature(experiment._experiment)
    for k, v in kwargs.items():
        if k in signature.parameters:
            relevant_kwargs[k] = interpret(v, signature.parameters[k])

    return relevant_kwargs
