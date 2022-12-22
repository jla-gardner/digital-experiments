import contextlib
import functools
import inspect
import shutil
from pathlib import Path
from typing import Callable, Dict, List, Union

from digital_experiments.backends import Backend, Files, get_backend, id_for
from digital_experiments.naming import new_experiment_id
from digital_experiments.tee import stdout_to_
from digital_experiments.util import (
    copy_docstring_from,
    do_nothing,
    get_complete_config,
    move_tree,
    no_context,
    pretty_json,
    time,
)


def do_experiment(
    func: Callable,
    args: List,
    kwargs: Dict,
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
    config = get_complete_config(func, args, kwargs)

    info(f"Starting new experiment - {expmt_id}")
    info(f"Arguments: {pretty_json(config)}")

    # time the experiment
    timing, ret = time(func)(*args, **kwargs)

    # save the results
    metadata = {"timing": timing, **additional_metadata}
    backend.save(expmt_dir, config, ret, metadata)

    info(f"Finished experiment - {expmt_id}", end="\n\n")
    return ret


def exmpt_setup(func: Callable, save_to: Union[None, str], backend: Backend) -> Path:
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

    def setup_dir(dir: Path) -> Path:
        """
        the root folder for experiments needs to
        - exist
        - contain the code of the experiment in `code.py`
        - contain the backend identifier in `.backend`
        """
        dir.mkdir(parents=True, exist_ok=False)
        (dir / Files.CODE).write_text(code)
        (dir / Files.BACKEND).write_text(id_for(backend))
        return dir

    default_root = Path(save_to or func.__name__)

    # the experiment has never been run before
    if not default_root.exists():
        return setup_dir(default_root)
    # otherwise experiment has been run ⬇️

    # several versions of the experiment can exist
    versions = list(default_root.glob("v-*"))

    if not versions:
        # the experiment's code has not been changed
        if (default_root / Files.CODE).read_text() == code:
            return default_root
        # the experiment's code has been changed for the first time:
        # move all the old results to v-1, and setup v-2
        else:
            move_tree(default_root, default_root / "v-1")
            return setup_dir(default_root / "v-2")

    for version in versions:
        # the experiment's code has reverted to a previous version
        if (version / Files.CODE).read_text() == code:
            return version

    # the experiment's code has been changed again, create a new version
    return setup_dir(default_root / f"v-{len(versions) + 1}")


def clean_up_exmpt(dir: Path):
    # remove the experiment directory if empty (keeps file system looking clean)
    if not any(dir.iterdir()):
        shutil.rmtree(dir)


class ExperimentManager:
    def __init__(self):
        self._directories: List[Path] = []
        self._metadata: List[Dict] = []
        self.active: bool = True

    def current_directory(self) -> Path:
        """
        get the directory for the current experiment
        """
        return self._directories[-1]

    @contextlib.contextmanager
    def additional_metadata(self, metadata=None, **more_metadata):
        metadata = {**metadata, **more_metadata} if metadata else more_metadata
        self._metadata.append(metadata)
        yield
        self._metadata.pop()

    def _additional_metadata(self):
        return self._metadata[-1] if self._metadata else {}

    @contextlib.contextmanager
    def _using_directory(self, directory: Path):
        """Context manager for setting the current directory"""
        self._directories.append(directory)
        yield
        self._directories.pop()

    @contextlib.contextmanager
    def dont_record(self):
        self.active = False
        yield
        self.active = True

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

        This decorator takes care of:
        - recording the experiment's config
        - recording the experiment's results
        - recording other metadata (e.g. timing)
        - recording the experiment's logs
        - recording the experiment's code
        - saving the above

        Usage:
        ```
        @experiment
        def my_experiment(a, b):
            return a + b
        ```
        """

        info = print if verbose else do_nothing
        backend: Backend = get_backend(backend)

        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.active:
                    return func(*args, **kwargs)

                # setup the file system ready for the experiment
                expmt_root_dir = exmpt_setup(func, save_to, backend)

                # create a new experiment
                expmt_dir = expmt_root_dir / new_experiment_id()
                expmt_dir.mkdir(parents=True, exist_ok=False)

                optional_logging = (
                    stdout_to_(expmt_dir / "log") if capture_logs else no_context()
                )
                with optional_logging, self._using_directory(expmt_dir):
                    ret = do_experiment(
                        func,
                        args,
                        kwargs,
                        expmt_dir,
                        backend,
                        info,
                        self._additional_metadata(),
                    )

                clean_up_exmpt(expmt_dir)
                return ret

            return wrapper

        if _func == None:  # called using kwargs, i.e. as @record(save_to=...)
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
    return __MANAGER.current_directory()


@copy_docstring_from(ExperimentManager.dont_record)
def dont_record():
    return __MANAGER.dont_record()


@copy_docstring_from(ExperimentManager.additional_metadata)
def additional_metadata(metadata=None, **more_metadata):
    return __MANAGER.additional_metadata(metadata, **more_metadata)
