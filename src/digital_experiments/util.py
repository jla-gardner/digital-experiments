from datetime import datetime
from typing import Any, Dict


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
