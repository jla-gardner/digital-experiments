from dataclasses import asdict
from glob import glob
from pathlib import Path
from typing import Callable, List, Union

import pandas as pd

from digital_experiments.backends import Files, backend_used_for
from digital_experiments.experiment import Experiment
from digital_experiments.util import flatten, matches


def experiments_for(
    thing: Union[str, Callable],
    template: dict = None,
    version="latest",
    **more_template,
) -> List[Experiment]:

    if callable(thing):
        root = Path(thing.__name__)
    else:
        root = Path(thing)

    if not root.exists():
        return []

    if Files.CODE not in [f.name for f in root.iterdir() if f.is_file()]:
        if version == "latest":
            versions = sorted(map(lambda p: int(p.name[2:]), root.glob("v-*")))
            version = versions[-1]

        root = root / f"v-{version}"

    backend = backend_used_for(root)
    experiments = backend.all_experiments(root)

    template = {**(template or {}), **more_template}
    return [e for e in experiments if matches(asdict(e), template)]


def get_artefacts(root: str, id: str):
    paths = [Path(p) for p in glob(f"{root}/**", recursive=True) if id in p]
    root_dir = paths[0].parent
    backend = backend_used_for(root_dir)

    return {
        p.name: p for p in paths if p.is_file() and p.name not in backend.core_files()
    }


def to_dataframe(
    experiments: List[Experiment], id: bool = False, metadata: bool = False
) -> pd.DataFrame:
    """
    Convert a list of experiments into a dataframe
    """
    df = pd.DataFrame([flatten(asdict(e)) for e in experiments])
    if not id:
        df = df.drop(columns="id")
    if not metadata:
        df = df.filter(regex="^(?!metadata)")
    return df
