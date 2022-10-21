from datetime import datetime
from random import choice
from pathlib import Path


me = Path(__file__).parent
nouns = (me / "nouns.txt").read_text().split()
adjectives = (me / "adjectives.txt").read_text().split()

def random_id():
    return "-".join((
        datetime.now().strftime("%y%m%d-%H%M%S-%f")[:-2],
        choice(adjectives),
        choice(nouns)
    ))
