import warnings
from typing import Any, Dict, List

import pandas as pd

from .observation import Observation


def union(things):
    return set.union(*[set(t) for t in things])


def intersect(things):
    return set.intersection(*[set(t) for t in things])


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


def to_dataframe(
    observations: List[Observation], id: bool = False, metadata: bool = False
):
    """
    Convert a list of observations to a pandas DataFrame

    Parameters
    ----------
    observations: list of Observation
        list of observations to convert
    id: bool
        whether to include the id column
    metadata: bool
        whether to include the metadata column

    Returns
    -------
    pd.DataFrame
        DataFrame with the observations
    """

    dicts = [o.as_dict() for o in observations]
    config_keys = union(d["config"].keys() for d in dicts)
    result_keys = union(
        d["result"].keys() if isinstance(d["result"], dict) else []
        for d in dicts
    )

    overlap = intersect([config_keys, result_keys])
    if not overlap:
        for d in dicts:
            d.update(d["config"])
            del d["config"]
            if isinstance(d["result"], dict):
                d.update(d["result"])
                del d["result"]
    else:
        warnings.warn(
            f"There are keys in config and results that overlap: {overlap}. "
            "Failed to flatten the dataframe nicely."
        )

    dicts = [flatten(d) for d in dicts]
    df = pd.DataFrame(dicts)

    if not id:
        # remove the id column
        del df["id"]
    if not metadata:
        # remove all metadata columns
        df = df.filter(regex="^(?!metadata).*$")

    return df
