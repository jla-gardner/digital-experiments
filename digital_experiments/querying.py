from glob import glob
from pathlib import Path

import pandas as pd

from digital_experiments.backends import Files, backend_used_for, get_backend
from digital_experiments.util import flatten, matches


def all_experiments(thing, version="latest", metadata=False) -> pd.DataFrame:
    if callable(thing):
        root = Path(thing.__name__)
    else:
        root = Path(thing)

    if Files.CODE not in [f.name for f in root.iterdir() if f.is_file()]:
        if version == "latest":
            versions = sorted(map(lambda p: int(p.name[2:]), root.glob("v-*")))
            version = versions[-1]

        root = root / f"v-{version}"

    backend = backend_used_for(root)
    return backend.all_experiments(root, metadata)


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
