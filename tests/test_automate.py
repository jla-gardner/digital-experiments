from digital_experiments import experiment
from digital_experiments.automate import automate_experiment
from digital_experiments.search.suggest import GridSuggester


def test_automation(tmp_path):
    @experiment(absolute_root=tmp_path)
    def exponential(x, y):
        return x**y

    grid = {
        "x": [1, 2, 3],
        "y": [1, 2, 3],
    }

    automate_experiment(
        exponential,
        GridSuggester(grid),
    )

    assert len(exponential.observations) == 9
