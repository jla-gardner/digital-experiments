import argparse
from os.path import commonprefix


def main():
    parser = argparse.ArgumentParser("Merge two files that contain a common prefix.")
    parser.add_argument("file_1", type=argparse.FileType("r"))
    parser.add_argument("file_2", type=argparse.FileType("r"))
    args = parser.parse_args()
    print(sorted_merge(args.file1.read(), args.file2.read()))


def sorted_merge(a, b):
    a = set(a.splitlines())
    b = set(b.splitlines())
    return "\n".join(sorted(a.union(b)))


if __name__ == "__main__":
    main()
