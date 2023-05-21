import shutil
from pathlib import Path

from digital_experiments import experiment
from digital_experiments.inspection import code_for
from digital_experiments.version_control import (
    current_max_version,
    get_all_versions,
    get_backend_for,
    get_or_create_backend_for,
    is_version,
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
    assert versions[0].name == "version-1", "Should have one version"
    assert current_max_version(root) == 1

    shutil.move(root / "version-1", root / "my-renamed-version")
    versions = get_all_versions(root)
    assert len(versions) == 1, "Should have one version"
    assert versions[0].name == "my-renamed-version", "Should have one version"

    backend = get_backend_for(root, is_version("my-renamed-version"))
    assert backend is not None, "Should have a backend"

    # test that we don't error if we rename a version to something
    # that still matches the pattern `version-*`
    shutil.move(root / "my-renamed-version", root / "version-renamed")
    max_version = current_max_version(root)
    assert max_version == 0, "No numbered versions should exist"

    # define a new version
    # since we have renamed our old one, this should be version-1
    @experiment(absolute_root=tmp_path)
    def add(a, b):
        # this is a new version
        return a + b

    versions = get_all_versions(root)
    assert len(versions) == 2, "Should have two versions"
    assert "version-renamed" in [v.name for v in versions]
    assert "version-1" in [v.name for v in versions]


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

    backend = get_backend_for(root, is_version("version-1"))
    assert backend is not None, "Should have a backend"

    backend = get_backend_for(root, is_version("version-2"))
    assert backend is None, "Should not have a backend"


def test_get_or_create_backend_for(tmp_path):
    @experiment(absolute_root=tmp_path, backend="csv")
    def add(a, b):
        return a + b

    # get the code
    code = code_for(add._experiment)
    backend_str = "csv"

    backend = get_or_create_backend_for(tmp_path, code, backend_str)
    assert backend is not None, "Should have a backend"
