import inspect
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

from filelock import FileLock


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


@contextmanager
def exclusive_file_access(filehandle: Union[str, Path], mode: str = "r"):
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


def get_passed_kwargs_for(experiment):
    kwargs: Dict[str, str] = get_passed_kwargs()

    relevant_kwargs = {}
    signature = inspect.signature(experiment._experiment)
    for k, v in kwargs.items():
        if k in signature.parameters:
            relevant_kwargs[k] = interpret(v, signature.parameters[k])

    return relevant_kwargs


def dict_equality(d1: Dict, d2: Dict):
    if set(d1.keys()) != set(d2.keys()):
        return False

    for k in d1.keys():
        v1 = d1[k]
        v2 = d2[k]

        if isinstance(v1, dict):
            if not isinstance(v2, dict):
                return False
            if not dict_equality(v1, v2):
                return False
            continue

        if v1 != v2:
            return False

    return True


def merge_dicts(d1, d2):
    """
    nestedly merge two dictionaries

    Example
    -------
    >>> d1 = {"a": {"b": 1, "c": 2}, "d": 3}
    >>> d2 = {"a": {"b": 4, "e": 5}, "f": 6}
    >>> merge_dictionaries(d1, d2)
    {'a': {'b': 4, 'c': 2, 'e': 5}, 'd': 3, 'f': 6}
    """

    new_dict = {}
    for k, v in d1.items():
        if k not in d2:
            # the key is not in d2, so we can just add it
            new_dict[k] = v
            continue

        # the key is in d2

        # first, check if the value is a dict
        if isinstance(v, dict):
            # if the matching value in d2 is not a dict, we can't merge
            if not isinstance(d2[k], dict):
                raise ValueError(f"Cannot merge {v} with {d2[k]}")

            # if the matching value in d2 is a dict, we can merge
            new_dict[k] = merge_dicts(v, d2[k])
            continue

        # if the value is not a dict
        # we can want to ensure that the values are equal
        # if they are not, we can't merge
        if v != d2[k]:
            raise ValueError(f"Cannot merge {v} with {d2[k]}")

        # the values are equal, so we can just add the value from d2
        new_dict[k] = d2[k]

    # now we need to add all the keys from d2 that are not in d1
    for k, v in d2.items():
        if k not in d1:
            new_dict[k] = v

    return new_dict
