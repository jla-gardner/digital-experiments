import contextlib
import inspect
import sys
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Callable, Dict, Sequence, Union

import numpy as np


def identity(x):
    return x


def nothing(*args, **kwargs):
    pass


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


Result = Dict[str, Union[Any, "Result"]]


def summarise(results: Sequence[Result], agg_fns: Sequence[Callable] = None) -> Result:
    if agg_fns is None:
        agg_fns = [np.mean, np.std]

    _template = results[0]
    for result in results:
        assert result.keys() == _template.keys(), "Results must have the same keys"

    summary = {}
    for key in _template:
        if isinstance(_template[key], dict):
            summary[key] = summarise([result[key] for result in results], agg_fns)
        else:
            summary[key] = {
                agg_fn.__name__: agg_fn([result[key] for result in results])
                for agg_fn in agg_fns
            }
    return summary


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
