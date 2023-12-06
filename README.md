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
