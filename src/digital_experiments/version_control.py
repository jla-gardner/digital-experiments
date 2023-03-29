"""
Version control for experiments.

Each experiment is associated with a root directory on disk.
Multiple versions of the experiment are stored in this directory, 
typically based on the code of the experiment, and the backend
used to store its results.

The general structure of the file system for this directory (root) is:
<root>
├── version-1
│   ├── .digital-experiment
│   ├── observations.<format>
│   └── ... other backend specific files
├── version-2/...
└── named-version/...

i.e. every version of the experiment is stored in a subdirectory
which definitely contains the .digital-experiment metadata file.

These directories are numbered sequentially, but can be renamed
by the user to be more descriptive.
"""

from pathlib import Path
from typing import List, Optional

from .backends import Backend, Files, HomeLabel, backend_from_type

MUST_SPECIFY_BACKEND = ValueError(
    "If the experiment has never been run before, "
    "you must specify a backend."
)


def get_all_versions(root: Path) -> List[str]:
    """
    Find all the versions of the experiment in the root directory
    """
    assert root.exists()
    return [file.parent.name for file in root.glob(f"**/{Files.LABEL}")]


def current_max_version(root: Path) -> int:
    """
    Find the current maximum version number of the experiment
    in the root directory
    """
    numbered_versions = []

    for version in get_all_versions(root):
        if version.startswith("version-"):
            try:
                numbered_versions.append(int(version.split("-")[-1]))
            except:
                pass

    return max(numbered_versions, default=0)


def get_backend_for(root, acceptance_function) -> Optional[Backend]:
    """
    Find the alphabetically-first home for this experiment
    that satisfies the acceptance function, if it exists.
    """

    if not root.exists():
        return None

    existing_versions = get_all_versions(root)

    for version in sorted(existing_versions):
        home = root / version
        if acceptance_function(root, version):
            return Backend.from_existing(home)

    return None


def create_backend_for(
    root, experiment_code: str, backend_name: str
) -> Backend:

    version = 1 if not root.exists() else current_max_version(root) + 1
    home = root / f"version-{version}"

    backend_class = backend_from_type(backend_name)
    return backend_class.create_new(home, experiment_code)


def get_or_create_backend_for(
    root,
    experiment_code: str,
    backend_name: str,
) -> Backend:
    acceptance_fn = matches_code_and_backend(experiment_code, backend_name)
    backend = get_backend_for(root, acceptance_fn)

    if backend is None:
        return create_backend_for(root, experiment_code, backend_name)

    return backend


# Acceptance functions --------------------------------------------------------


def latest_version(root: Path, version: str):
    """
    Find the latest version of the experiment in the root directory
    """
    return version == f"version-{current_max_version(root)}"


def matches_code_and_backend(code, backend):
    def acceptance(root, version):
        home = root / version
        label = HomeLabel.from_existing(home)
        return label.code == code and label.backend_name == backend

    return acceptance


def for_version(specified_version: str):
    return lambda root, version: version == specified_version
