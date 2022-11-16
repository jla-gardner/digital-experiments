import functools
import inspect
import os
import shutil
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd

from digital_experiments.backends import Backend, Files, get_backend, pretty_json
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


def update_root_folder(original_root: Path, code: str, backend: str):
    original_code = original_root / "code.py"
    versions = sorted(original_root.glob("v-*"), key=lambda p: int(p.name[2:]))

    if not versions and not original_code.exists():
        original_root.mkdir(parents=True)
        original_code.write_text(code)
        (original_root / ".backend").write_text(backend)
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
    (new_version / ".backend").write_text(backend)
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
            folder = update_root_folder(root_folder, code, backend)
            sig = inspect.signature(func)
            _backend = get_backend(folder, backend)

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
                _backend.save(expmt_dir.name, config, ret, metadata)

                if not any(expmt_dir.iterdir()):
                    shutil.rmtree(expmt_dir)

                info(f"Finished experiment - {expmt_dir.name}", end="\n\n")
                return ret

            return wrapper

        if _func == None:  # called as @record(root=...)
            return decorator
        else:  # called as @record
            return decorator(_func)


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

    backend = get_backend(root)
    return backend.all_experiments(metadata)


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
    backend = get_backend(root_dir)

    return {
        p.name: p for p in paths if p.is_file() and p.name not in backend.core_files
    }


__MANAGER = Manager()


@copy_docstring_from(Manager.experiment)
def experiment(
    _func=None,
    *,
    save_to: str = None,
    capture_logs: bool = False,
    verbose: bool = False,
    backend: str = "json",
):
    return __MANAGER.experiment(
        _func=_func,
        save_to=save_to,
        capture_logs=capture_logs,
        verbose=verbose,
        backend=backend,
    )


@copy_docstring_from(Manager.current_directory)
def current_directory():
    return __MANAGER.current_directory


def set_context(context: str):
    __MANAGER.set_context(context)


def reset_context():
    __MANAGER.reset_context()
