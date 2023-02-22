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