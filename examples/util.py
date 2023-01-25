from pathlib import Path

from digital_experiments.util import root_dir_for

# prefix components:
space = "    "
branch = "│   "
# pointers:
tee = "├── "
last = "└── "


def _tree(dir_path: str, prefix: str = ""):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters

    see https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
    """
    contents = sorted(Path(dir_path).iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name
        if path.is_dir():  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from _tree(path, prefix=prefix + extension)


def tree(func):
    for line in _tree(root_dir_for(func)):
        print(line)
