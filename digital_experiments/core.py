import contextlib
import functools
import inspect
import shutil
from pathlib import Path
from typing import Callable, Dict, List, Union

from digital_experiments.backends import Backend, get_backend, pretty_json
from digital_experiments.naming import new_experiment_id
from digital_experiments.tee import stdout_to_
from digital_experiments.util import (
    copy_docstring_from,
    do_nothing,
    move_tree,
    no_context,
    time,
)


def exmpt_setup(func: Callable, save_to: Union[None, str], backend: Backend):
    """
    setup the file system ready for an experiment

    This takes care of:
    - versioning the experiment
    - creating the experiment directory
    - copying the code to the experiment directory
    - copying the backend to the experiment directory

    Usually, experiments are saved to the specified directory (default_root)
    If a new version of the experiment is being run (i.e. the code has changed)
    then sub directories named v-1, v-2, etc are created, and results are saved
    to the latest version (or previous version if the code has been changed back)
    """

    code = inspect.getsource(func)

    def setup_dir(dir: Path):
        """
        the root folder for experiments needs to
        - exist
        - contain the code of the experiment in `code.py`
        - contain the backend identifier in `.backend`
        """
        dir.mkdir(parents=True, exist_ok=False)
        (dir / "code.py").write_text(code)
        (dir / ".backend").write_text(backend.rep)
        return dir

    default_root = Path(save_to or func.__name__)

    # the experiment has never been run before
    if not default_root.exists():
        return setup_dir(default_root)

    # several versions of the experiment can exist
    versions = list(default_root.glob("v-*"))

    if not versions:
        # the experiment's code has not been changed
        if (default_root / "code.py").read_text() == code:
            return default_root
        # the experiment's code has been changed for the first time:
        # move all the old results to v-1, and setup v-2
        else:
            move_tree(default_root, default_root / "v-1")
            return setup_dir(default_root / "v-2")

    for version in versions:
        # the experiment's code has reverted to a previous version
        if (version / "code.py").read_text() == code:
            return version

    # the experiment's code has been changed again, create a new version
    return setup_dir(default_root / f"v-{len(versions) + 1}")


def clean_up_exmpt(dir: Path):
    # remove the experiment directory if empty (keeps file system looking clean)
    if not any(dir.iterdir()):
        shutil.rmtree(dir)


def _do_experiment(
    func,
    args,
    kwargs,
    expmt_dir: Path,
    backend: Backend,
    info: Callable,
    additional_metadata: Dict,
):
    """
    do the experiment, and save the results
    """
    expmt_id = expmt_dir.name

    # get the (complete) config used for the experiment
    sig = inspect.signature(func)
    config = sig.bind(*args, **kwargs)
    config.apply_defaults()
    config = config.arguments

    info(f"Starting new experiment - {expmt_id}")
    info(f"Arguments: {pretty_json(config)}")

    # time the experiment
    timing, ret = time(func)(*args, **kwargs)

    # save the results
    metadata = {"timing": timing, **additional_metadata}
    backend.save(expmt_dir, config, ret, metadata)

    info(f"Finished experiment - {expmt_id}", end="\n\n")
    return ret


class ExperimentManager:
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

    @contextlib.contextmanager
    def _using_directory(self, directory: Path):
        """Context manager for setting the current directory"""
        self._directories.append(directory)
        yield
        self._directories.pop()

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
        decorator for running an experiment


        """

        info = print if verbose else do_nothing
        backend: Backend = get_backend(backend)

        def decorator(func: Callable):
            expmt_root_dir = exmpt_setup(func, save_to, backend)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                expmt_dir = expmt_root_dir / new_experiment_id()
                expmt_dir.mkdir(parents=True, exist_ok=False)

                metadata = {"context": self.current_context}

                optional_logging = (
                    stdout_to_(expmt_dir / "log") if capture_logs else no_context()
                )
                with optional_logging, self._using_directory(expmt_dir):
                    ret = _do_experiment(
                        func,
                        args,
                        kwargs,
                        expmt_dir,
                        backend,
                        info,
                        metadata,
                    )

                clean_up_exmpt(expmt_dir)
                return ret

            return wrapper

        if _func == None:  # called as @record(root=...)
            return decorator
        else:  # called as @record
            return decorator(_func)


__MANAGER = ExperimentManager()


@copy_docstring_from(ExperimentManager.experiment)
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


@copy_docstring_from(ExperimentManager.current_directory)
def current_directory():
    return __MANAGER.current_directory


def set_context(context: str):
    __MANAGER.set_context(context)


def reset_context():
    __MANAGER.reset_context()
