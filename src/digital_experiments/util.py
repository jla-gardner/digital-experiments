import contextlib
import functools
import inspect
import json
import shutil
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np


def identity(x):
    return x


def first(iterable):
    return next(iter(iterable))


def flatten(_dict, seperator="."):
    """
    flatten nested dicts into a single level

    e.g.
    flatten({"a": 1, "b": {"c": 2}}) == {"a": 1, "b.c": 2}
    """

    def _flatten(_dict, prefix=""):
        for key, value in _dict.items():
            if isinstance(value, Mapping):
                yield from _flatten(value, prefix + key + seperator)
            else:
                yield prefix + key, value

    return dict(_flatten(_dict))


def unflatten(_dict, seperator="."):
    """
    unflatten a single level dict into a nested dict

    e.g.
    unflatten({"a": 1, "b.c": 2}) == {"a": 1, "b": {"c": 2}}
    """

    def _unflatten(_dict, prefix=""):
        if not any(seperator in key for key in _dict.keys()):
            return _dict
        _new_dict = {}

        for key, value in _dict.items():
            if seperator not in key:
                _new_dict[key] = value
                continue

            prefix, suffix = key.split(seperator, 1)
            if prefix not in _new_dict:
                _new_dict[prefix] = {}
            _new_dict[prefix][suffix] = value

        return {
            k: unflatten(v) if isinstance(v, dict) else v for k, v in _new_dict.items()
        }

    return _unflatten(_dict)


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


def get_passed_kwargs_for(func):
    kwargs: Dict[str, str] = get_passed_kwargs()

    relevant_kwargs = {}
    signature = inspect.signature(func)
    for k, v in kwargs.items():
        if k in signature.parameters:
            relevant_kwargs[k] = interpret(v, signature.parameters[k])

    return relevant_kwargs


def copy_docstring_from(func):
    def decorator(f):
        f.__doc__ = func.__doc__
        return f

    return decorator


def now():
    return datetime.now().timestamp()


def no_context():
    return contextlib.nullcontext()


def do_nothing(*args, **kwargs):
    pass


def move_tree(src: Path, dest: Path):
    temp = Path("/tmp") / src.name
    shutil.move(src, temp)
    shutil.move(temp, dest)


def time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = now()
        ret = func(*args, **kwargs)
        end = now()
        return {"start": start, "end": end}, ret

    return wrapper


np_types = {
    "bool_": bool,
    "integer": int,
    "floating": float,
    "ndarray": list,
}


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        for np_type in np_types:
            if isinstance(obj, getattr(np, np_type)):
                return np_types[np_type](obj)
        return json.JSONEncoder.default(self, obj)


def pretty_json(thing):
    return json.dumps(thing, indent=4, cls=NpEncoder)


independent_random = np.random.RandomState(seed=1)


def get_complete_config(func, args, kwargs):
    sig = inspect.signature(func)
    config = sig.bind(*args, **kwargs)
    config.apply_defaults()
    config = config.arguments
    return config


def matches(thing, template):
    """
    does thing conform to the passed (and optionally nested template?)

    e.g.
    matches({"a": 1, "b": 2}, template={"a": 1}) == True
    matches({"a": 1, "b": 2}, template={"a": 1, "c": 3}) == False
    matches({"a": 1, "b": 2}, template={"a": lambda x: x > 0}) == True
    matches(
        {"a": 1, "b": {"c": 2}},
        template={"b": {"c": lambda x: x%2 == 0}}
    ) == True
    """

    for key in set(thing.keys()).union(set(template.keys())):
        if key not in template:
            # template doesn't specify what to do with this key
            continue
        if key not in thing:
            # thing doesn't have this required key: doesn't match
            return False
        if matches_value(thing[key], template[key]):
            continue
        else:
            # value doesn't match
            return False

    return True


def matches_value(value, template_value):
    """
    does value conform to the entry in template_value?

    e.g.
    matches_value(1, 1) == True
    matches_value(1, 2) == False
    matches_value(1, lambda x: x > 0) == True
    matches_value({"a": 1}, {"a": 1}) == True # calls back into matches
    """

    if isinstance(value, Mapping):
        return matches(value, template_value)
    if callable(template_value):
        return template_value(value)
    return value == template_value
