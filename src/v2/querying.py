from typing import List

import pandas as pd

from .observation import Observation


def union(things, *more_things):
    things = list(things) + list(more_things)
    return set.union(*[set(t) for t in things])


def intersect(things, *more_things):
    things = list(things) + list(more_things)
    return set.intersection(*[set(t) for t in things])


def to_dataframe(
    observations: List[Observation], id: bool = False, metadata: bool = False
):
    dicts = [o.as_dict() for o in observations]
    if not id:
        for d in dicts:
            del d["id"]
    if not metadata:
        for d in dicts:
            del d["metadata"]
    config_keys = union(d["config"].keys() for d in dicts)
    result_keys = union(
        d["result"].keys() if isinstance(d["result"], dict) else []
        for d in dicts
    )

    if intersect(config_keys, result_keys):
        raise ValueError(
            "There are keys in the config and result that overlap. "
            "This is not supported."
        )

    for d in dicts:
        d.update(d["config"])
        del d["config"]
        if result_keys:
            d.update(d["result"])
            del d["result"]
        else:
            # preserve the ordering of config -> result for aesthetics
            r = d["result"]
            del d["result"]
            d["result"] = r

    return pd.DataFrame(dicts)
