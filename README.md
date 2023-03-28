<div align="center">
<img src="docs/source/logo.svg" width="50%">
</div>

---

A lightweight python library for keeping track of, and optimizing, configuration and results for digital experiments.

## Getting Started

Installation is as easy as `pip install digital-experiments`

Using the library is easy too. Here's a simple example:

```python
from digital_experiments import experiment

@experiment
def my_experiment(a, b=2):
    return a ** b

my_experiment(2, b=3)
```

## Walkthrough

The [examples directory](examples/) contains some notebooks that help explain how this package works

-   [Basic Overview](examples/digital_experiments.ipynb)
-   [Optimising with digital-experiments](examples/optimization.ipynb)

---

<div align="center">
    <img src="https://raw.github.com/jla-gardner/digital-experiments/master/res/optimization.gif" alt="drawing" width="400"/>
    <img src="https://raw.github.com/jla-gardner/digital-experiments/master/res/optimization.svg" alt="drawing" width="400"/>
</div>
