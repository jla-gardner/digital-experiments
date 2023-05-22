from pathlib import Path
from typing import Callable, Dict, Type

from digital_experiments.save_and_load.backend import Backend
from digital_experiments.util import ExistingPath


class Home:
    """
    a digital experiment is given a "home"

    this is a directory that contains a collection of backends,
    each of which is responsible for saving and loading results for
    stores a specific version of the experiment
    """

    def __init__(self, root: Path):
        if not root.exists():
            root.mkdir(parents=True)
        self.root = ExistingPath(root)

    def all_backends(self) -> Dict[str, Backend]:
        """
        return all the backends in this home as a dictionary from
        name to backend
        """

        return {
            path.name: Backend.from_existing(path)
            for path in self.root.iterdir()
            if Backend.is_backend(path)
        }

    def numbered_backends(self) -> Dict[int, Backend]:
        """
        return all the numbered backends in this home as a dictionary from
        number to backend
        """
        backends = {}
        for name, backend in self.all_backends().items():
            # numbered versions are of the format "version-<number>"
            if not name.startswith("version-"):
                continue

            try:
                _, number = name.split("-")
                backends[int(number)] = backend
            except:
                pass

        return backends

    def current_max_version(self) -> int:
        """
        Find the current maximum version number of the experiment
        in the root directory
        """
        return max(self.numbered_backends().keys(), default=0)

    def backend_for(self, function: Callable, backend_type: Type[Backend]) -> Backend:
        """
        return the backend for the given function,
        optionally creating it if it does not exist
        """

        for backend in self.all_backends().values():
            if backend.is_for(function) and isinstance(backend, backend_type):
                return backend

        # if we get here, we need to create a new backend
        location = self.root / f"version-{self.current_max_version() + 1}"
        return backend_type.create_new(location, function)
