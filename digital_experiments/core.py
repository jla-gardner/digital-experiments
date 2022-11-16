import functools
import inspect
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd

from digital_experiments.backends import Backend, JSONBackend, pretty_json
from digital_experiments.ids import random_id
from digital_experiments.tee import stdout_to_
from digital_experiments.util import (
    copy_docstring_from,
    do_nothing,
    flatten,
    matches,
    no_context,
    now,
)


def get_unique_folder(root: os.PathLike) -> Path:
    """Return a unique folder in the given root folder."""
    root = Path(root)
    while True:
        folder = root / random_id()
        if not folder.exists():
            return folder


def update_root_folder(original_root: Path, code: str):
    original_code = original_root / "code.py"
    versions = sorted(original_root.glob("v-*"), key=lambda p: int(p.name[2:]))

    if not versions and not original_code.exists():
        original_root.mkdir(parents=True)
        original_code.write_text(code)
        return original_root

    if not versions:
        if original_code.read_text() == code:
            return original_root
        else:
            temp = Path("/tmp") / original_root.name
            shutil.move(original_root, temp)
            shutil.move(temp, original_root / "v-1")
            versions = [original_root / "v-1"]

    for version in versions:
        if (version / "code.py").read_text() == code:
            return version

    new_version = original_root / f"v-{len(versions) + 1}"
    new_version.mkdir()
    (new_version / "code.py").write_text(code)
    return new_version


class Manager:
    def __init__(self):
        self._directories: List[Path] = []
        self._contexts: List[str] = []

    @property
    def current_directory(self) -> Path:
        return self._directories[-1]

    @property
    def current_context(self) -> str:
        return "manual" if not self._contexts else self._contexts[-1]

    def set_context(self, context: str):
        self._contexts.append(context)

    def reset_context(self):
        return self._contexts.pop()

    def experiment(
        self,
        _func=None,
        *,
        save_to: str = None,
        capture_logs: bool = False,
        verbose: bool = False,
        backend: str = "json",
    ):
        """
        hello, I need to add this docstring
        """
        info = print if verbose else do_nothing

        def decorator(func: Callable):
            root_folder = Path(save_to or func.__name__)
            code = inspect.getsource(func)
            folder = update_root_folder(root_folder, code)
            sig = inspect.signature(func)
            backend = JSONBackend(folder)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):

                expmt_dir = get_unique_folder(folder)
                expmt_dir.mkdir(parents=True, exist_ok=False)

                config = sig.bind(*args, **kwargs)
                config.apply_defaults()
                config = config.arguments

                info(f"Starting new experiment - {expmt_dir.name}")
                info(f"Arguments: {pretty_json(config)}")

                _start = now()
                self._directories.append(expmt_dir)

                with stdout_to_(expmt_dir / "log") if capture_logs else no_context():
                    ret = func(*args, **kwargs)

                self._directories.pop()

                metadata = {
                    "_time": {"start": _start, "end": now()},
                    "_context": self.current_context,
                }
                backend.save(expmt_dir.name, config, ret, metadata)

                if not any(expmt_dir.iterdir()):
                    shutil.rmtree(expmt_dir)

                info(f"Finished experiment - {expmt_dir.name}", end="\n\n")
                return ret

            return wrapper

        if _func == None:  # called as @record(root=...)
            return decorator
        else:  # called as @record
            return decorator(_func)


@dataclass
class Experiment:
    id: str
    config: dict
    result: Any
    log: str
    artefacts: Dict[str, Path]
    metadata: dict

    @classmethod
    def from_folder(cls, folder: Path, backend: Backend):
        core_files = [
            folder / f for f in ("config.json", "results.json", "log", "metadata.json")
        ]
        artefacts = {
            f.name: f
            for f in sorted(Path(folder).glob("*.*"))
            if f not in core_files and f.is_file()
        }
        log = (folder / "log").read_text() if (folder / "log").exists() else None

        config, result, metadata = backend.load(folder.name)

        return cls(
            id=folder.name,
            config=config,
            result=result,
            log=log,
            artefacts=artefacts,
            metadata=metadata,
        )

    def matches_config(self, config: dict):
        return matches(self.props(), config)

    def props(self, meta=False):
        results = (
            self.result if isinstance(self.result, dict) else {"result": self.result}
        )
        props = dict(id=self.id, **self.config, **results)
        if meta:
            props = {**props, **self.metadata}

        return props

    def row(self, meta=False):
        return flatten(self.props(meta=meta))


def all_experiments(root: Path) -> List[Experiment]:
    if not root.exists():
        return []

    results = []
    for folder in sorted(root.iterdir()):
        if folder.is_dir():
            try:
                e = Experiment.from_folder(folder, JSONBackend(root))
                results.append(e)
            except FileNotFoundError:
                continue

    return results


def all_experiments_matching(
    root: str, config_template: dict = None, include_metadata: bool = False
) -> Tuple[pd.DataFrame, List[Experiment]]:

    config_template = config_template or dict()
    experiments = [
        exp
        for exp in all_experiments(Path(root))
        if exp.matches_config(config_template)
    ]

    if not experiments:
        return pd.DataFrame(), []

    df = pd.DataFrame([exp.row(include_metadata) for exp in experiments])

    to_drop = ["id"]
    df.drop(to_drop, axis=1, inplace=True)

    return (
        df.reset_index(drop=False).rename(columns={"index": "experiment_number"}),
        experiments,
    )


__MANAGER = Manager()


@copy_docstring_from(Manager.experiment)
def experiment(
    _func=None,
    *,
    save_to: str = None,
    capture_logs: bool = True,
    verbose: bool = False,
):
    return __MANAGER.experiment(
        _func=_func,
        save_to=save_to,
        capture_logs=capture_logs,
        verbose=verbose,
    )


@copy_docstring_from(Manager.current_directory)
def current_directory():
    return __MANAGER.current_directory


def set_context(context: str):
    __MANAGER.set_context(context)


def reset_context():
    __MANAGER.reset_context()
