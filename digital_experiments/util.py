import sys
from collections.abc import Mapping


def identity(x):
    return x


def nothing(*args, **kwargs):
    pass


def update_with_passed_kwargs(defaults):
    for arg in sys.argv[1:]:
        try:
            key, value = arg.split("=")
        except ValueError:
            raise Exception(
                f"Expected arguments of the form key=value: unable to underderstand `{arg}`"
            )
            
        defaults[key] = value if type(defaults[key]) is str else eval(value)


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
