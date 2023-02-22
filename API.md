# Desired API

```python
from digital_experiments import experiment

@experiment
def my_experiment(a, b):
    # do stuff
    return a + b

my_experiment(1, 2)
```

```python
>>> my_experiment.observations
[{
    "config": {
        'a': 1,
        'b': 2,
    }
    'result': 3
}]
```

```python
@experiment
def my_experiment_1(a, b):
    # do stuff
    return {"c": a + b}

my_experiment_1(1, 2)
```

```python
>>> my_experiment_1.observations
[{
    "config": {
        'a': 1,
        'b': 2,
    }
    'result': {
        'c': 3
    }
}]
```

```python
>>> my_experiment_1.configs
[{
    'a': 1,
    'b': 2,
}]
```

```python
>>> my_experiment_1.results
[{
    'c': 3
}]
```

```python

```
