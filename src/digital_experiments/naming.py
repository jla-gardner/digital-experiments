from datetime import datetime
from pathlib import Path
from typing import Callable

from digital_experiments.util import independent_random as rand

me = Path(__file__).parent
nouns = (me / "nouns.txt").read_text().split()
adjectives = (me / "adjectives.txt").read_text().split()


def new_experiment_id(rejection_function: Callable = None) -> Path:
    """generate a new experiment id"""

    if rejection_function is None:
        rejection_function = lambda id: False

    while True:
        id = "-".join(
            (
                datetime.now().strftime("%y%m%d-%H%M%S-%f")[:-2],
                rand.choice(adjectives),
                rand.choice(nouns),
            )
        )
        if not rejection_function(id):
            return id
