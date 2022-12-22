from glob import glob
from pathlib import Path
from typing import Mapping

import pandas as pd

from digital_experiments.backends import Files, backend_used_for
from digital_experiments.experiment import Experiment
from digital_experiments.util import flatten, unflatten


def all_experiments(thing, version="latest", metadata=False) -> pd.DataFrame:
    if callable(thing):
        root = Path(thing.__name__)
    else:
        root = Path(thing)

    if not root.exists():
        return pd.DataFrame()

    if Files.CODE not in [f.name for f in root.iterdir() if f.is_file()]:
        if version == "latest":
            versions = sorted(map(lambda p: int(p.name[2:]), root.glob("v-*")))
            version = versions[-1]

        root = root / f"v-{version}"

    backend = backend_used_for(root)
    df = backend.all_experiments(root, metadata)
    if "results.results" in df.columns:
        df["results"] = df["results.results"]
        del df["results.results"]

    return df


def experiments_matching(
    root: str, template: dict = None, metadata: bool = False, **more_template
) -> pd.DataFrame:

    df = all_experiments(root, metadata=metadata)

    template = flatten({**(template or {}), **more_template})
    return pd.DataFrame(
        [row for _, row in df.iterrows() if matches(dict(row), template)]
    )


def get_artefacts(root: str, id: str):
    paths = [Path(p) for p in glob(f"{root}/**", recursive=True) if id in p]
    root_dir = paths[0].parent
    backend = backend_used_for(root_dir)

    return {
        p.name: p for p in paths if p.is_file() and p.name not in backend.core_files
    }


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


def convert_to_experiments(df):
    experiment_dicts = df.to_dict(orient="records")
    return [Experiment(**unflatten(d)) for d in experiment_dicts]
