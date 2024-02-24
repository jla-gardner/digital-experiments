from pathlib import Path
from time import sleep

from digital_experiments import current_dir, current_id, experiment, time_block
from digital_experiments.callbacks import SaveLogs


@experiment(
    backend="json",
    cache=True,
    callbacks=[SaveLogs("my-logs.txt")],
    root=Path("results"),
    verbose=True,
)
def my_experiment(a: int, b: int) -> int:
    with time_block("add"):
        sleep(0.5)
        c = a + b

    with time_block("multiply"):
        sleep(0.5)
        c = c * 2

    print("this will appear in the logs")
    (current_dir() / "output.txt").write_text(f"hello from {current_id()}")
    return c


# new experiment:
my_experiment(1, 2)
# "this will appear in the logs"
# (returns 6)

# don't record the experiment again due to cache=True
my_experiment(1, 2)
# (returns 6)

# get the observation
observation = my_experiment.observations()[-1]

print(my_experiment.artefacts(observation.id))
# "Path('results/storage/<id>/my-logs')"

for a in range(10):
    my_experiment(a, a)

# access the results as a pandas dataframe
df = my_experiment.to_dataframe()
