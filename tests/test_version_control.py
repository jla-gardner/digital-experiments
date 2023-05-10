from pathlib import Path

from digital_experiments import experiment
from digital_experiments.version_control import (
    current_max_version,
    for_version,
    get_all_versions,
    get_backend_for,
    latest_version,
)


def _get_root_for(experiment):
    return experiment._backend.home.parent


def test_multiple_versions():
    @experiment
    def add(a, b):
        return a + b

    add(1, 2)
    root = _get_root_for(add)
    versions = get_all_versions(root)
    assert len(versions) == 1, "Should have one version"
    assert versions[0] == "version-1", "Should have one version"
    assert current_max_version(root) == 1


def test_get_backend():
    root = Path("made-up-path")
    backend = get_backend_for(root, latest_version)
    assert backend is None, "root doesn't exist, should be None"


def test_acceptance_functions():
    @experiment
    def add(a, b):
        return a + b

    root = _get_root_for(add)
    backend = get_backend_for(root, latest_version)
    assert backend is not None, "Should have a backend"

    backend = get_backend_for(root, for_version("version-1"))
