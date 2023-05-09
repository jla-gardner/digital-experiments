import warnings
from typing import List

import pandas as pd

from .observation import Observation
from .util import flatten, intersect, union


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

    if len(observations) == 0:
        warnings.warn("No observations to convert to dataframe")
        return pd.DataFrame()

    dicts = [o.as_dict() for o in observations]
    config_keys = union(d["config"].keys() for d in dicts)
    result_keys = union(
        d["result"].keys() if isinstance(d["result"], dict) else [] for d in dicts
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


def matches(thing, template):
    return all(thing.get(k) == v for k, v in template.items())


def filtered_observations(
    observations,
    config=None,
    metadata=None,
    result=None,
):
    """
    Filter a list of observations based on config, metadata and result.

    Parameters
    ----------
    observations: list of Observation
        list of observations to filter
    config: dict
        filter on the config
    metadata: dict
        filter on the metadata
    result: dict
        filter on the result

    Returns
    -------
    list of Observation
        filtered list of observations
    """

    config = config or {}
    metadata = metadata or {}
    result = result or {}

    return [
        obs
        for obs in observations
        if matches(obs.config, config)
        and matches(obs.metadata, metadata)
        and matches(obs.result, result)
    ]
