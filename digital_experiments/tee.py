import sys


class Tee:
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode

    def __enter__(self):
        self.file = open(self.name, self.mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_value, exc_tb):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()


def stdout_to_(file):
    return Tee(file, "a")
