<div align="center">
    <img src="docs/source/logo.svg" style="width: 400px; height: auto;"/>
</div>

<div align="center">
    
A lightweight python package for recording and analysing configurations and results of coding experiments.

[![PyPI](https://img.shields.io/pypi/v/digital-experiments)](https://pypi.org/project/digital-experiments/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/digital-experiments?color=green&label=installs&logo=Python&logoColor=white)](https://pypistats.org/packages/digital-experiments)
[![GitHub](https://img.shields.io/github/license/jla-gardner/local-cache)](LICENCE.md)
[![](https://github.com/jla-gardner/load-atoms/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/jla-gardner/load-atoms/actions/workflows/tests.yaml)
[![codecov](https://codecov.io/gh/jla-gardner/digital-experiments/branch/master/graph/badge.svg?token=VGSFM0GWF1)](https://codecov.io/gh/jla-gardner/digital-experiments)

</div>

---

Keeping track of the results of coding experiments can be a pain. 
Over time, code and dependencies can change, and without careful record-keeping, it becomes difficult to remember and reproduce optimal configurations and results.


`digital-experiments` automates such tracking. To enable this automation, wrap your experiment's main function with the [`@experiment`](https://jla-gardner.github.io/digital-experiments/core-api.html#digital_experiments.experiment) decorator. Every time the function is called, the following information is saved to disk:
- the inputs (`args`, `kwargs` and defaults)
- the output/s (any, arbitrary object)
- the code of the function
- the current `git` information (if available)
- timing information
- python environment information

This information is available for analysis in the same or different python sessions, via the [`observations` API](https://jla-gardner.github.io/digital-experiments/core-api.html#digital_experiments.core.Experiment.observations).

To get started, see the basic use case below, or [our example notebook](https://jla-gardner.github.io/digital-experiments/usage.html).


## Installation

`pip install digital-experiments`

## Basic Use


1. Define your experiment as a pure-python function, and decorate it with `@experiment`:

```python
from digital_experiments import experiment

@experiment
def my_experiment(a, b=2):
    return a ** b
```

2. Call the function as normal:

```python
>>> my_experiment(2, 3)
8
>>> my_experiment(4)
16
```

3. Access the results of the experiment:

```python
>>> my_experiment.observations()
[Observation(<id1>, {'a': 2, 'b': 3} → 8}),
Observation(<id2>, {'a': 4, 'b': 2} → 16})]
```

If you have `pandas` installed, you can also access these results as a `DataFrame`:

```python
>>> my_experiment.to_dataframe()
      id  config.a  config.b  result
0  <id1>         2         3       8
1  <id2>         4         2      16
```

## Documentation

For more information, see the [documentation](https://jla-gardner.github.io/digital-experiments/).
