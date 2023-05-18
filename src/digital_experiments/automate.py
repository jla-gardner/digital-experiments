from typing import Any, Callable, Dict

from digital_experiments.experiment import Experiment
from digital_experiments.search.suggest import Step, Suggester


def automate_experiment(
    experiment: Experiment,
    suggester: Suggester,
    n_steps: int = None,
    overrides: Dict[str, Any] = None,
    extract_observation: Callable[[Any], float] = None,
):
    if len(suggester.previous_steps) > 0:
        raise ValueError(
            "Experiment automation requires a new suggester instance with no previous steps"
        )

    if overrides is None:
        overrides = {}
    if any(key in suggester.space for key in overrides):
        raise ValueError(
            "You are attempting to override a parameter that is already in the suggester's space. "
        )

    if extract_observation is None:
        extract_observation = lambda result: result

    # gather the initial observations
    points = [
        {k: v for k, v in obs.config.items() if k in suggester.space.keys()}
        for obs in experiment.observations
    ]
    values = [obs.value for obs in experiment.observations]

    # filter out invalid points
    steps = [Step(p, v) for p, v in zip(points, values) if suggester.is_valid_point(p)]

    # tell the suggester about the initial observations
    for step in steps:
        suggester.tell(step.point, step.observation)

    if n_steps is None:
        try:
            n_steps = len(suggester)
        except TypeError:
            raise ValueError("Please pass a value for `n_steps`")

    # run the experiment
    for _ in range(n_steps):
        point = suggester.suggest()
        result = experiment(**point, **overrides)
        observation = extract_observation(result)
        suggester.tell(point, observation)
