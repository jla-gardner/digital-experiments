import shutil
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


def test_multiple_versions(tmp_path):
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    add(1, 2)
    root = _get_root_for(add)
    versions = get_all_versions(root)
    assert len(versions) == 1, "Should have one version"
    assert versions[0] == "version-1", "Should have one version"
    assert current_max_version(root) == 1

    shutil.move(root / "version-1", root / "my-renamed-version")
    versions = get_all_versions(root)
    assert len(versions) == 1, "Should have one version"
    assert versions[0] == "my-renamed-version", "Should have one version"

    backend = get_backend_for(root, for_version("my-renamed-version"))
    assert backend is not None, "Should have a backend"

    # define a new version
    # since we have renamed our old one, this should be version-1
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        # this is a new version
        return a + b

    versions = get_all_versions(root)
    assert len(versions) == 2, "Should have two versions"
    assert "my-renamed-version" in versions
    assert "version-1" in versions


def test_get_backend():
    root = Path("made-up-path")
    backend = get_backend_for(root, latest_version)
    assert backend is None, "root doesn't exist, should be None"


def test_acceptance_functions(tmp_path):
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        return a + b

    root = _get_root_for(add)
    backend = get_backend_for(root, latest_version)
    assert backend is not None, "Should have a backend"

    backend = get_backend_for(root, for_version("version-1"))
    assert backend is not None, "Should have a backend"

    backend = get_backend_for(root, for_version("version-2"))
    assert backend is None, "Should not have a backend"
