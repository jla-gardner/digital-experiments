"""
Space objects define the space of acceptable values for a given set of
(named) hyperparameters. 

Each hyperparameter is associated with a distribution over values.
These distributions are defined by the Distribution class. Internally,
they work by mapping from the unit range ([0, 1]) to the desired
distribution. Each distribution can be randomly sampled.

Samplers sample from these spaces to generate new points to evaluate.
"""

import math
import random
from typing import Any, Dict, Iterable, Mapping, Sequence


def default_generator():
    """returns a random number between 0 and 1"""
    return random.random()


class Distribution:
    def random_sample(self, n=1, generator=None):
        """
        Randomly sample n points from the distribution.
        """
        if generator is None:
            generator = default_generator

        values = []
        for _ in range(n):
            values.append(generator())

        samples = [self.transform(v) for v in values]

        if n == 1:
            return samples[0]

        return samples

    def transform(self, unit_value):
        """
        Takes `value` in the unit range and transforms it to the
        distribution's range.
        """
        raise NotImplementedError()

    def inverse_transform(self, value):
        """
        Takes `value` in the distribution's range and transforms it to the
        unit range.
        """
        raise NotImplementedError()

    def contains(self, value):
        """
        Returns True if `value` is in the distribution's range.
        """
        raise NotImplementedError()


class Uniform(Distribution):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def transform(self, unit_value):
        return self.low + (self.high - self.low) * unit_value

    def inverse_transform(self, value):
        return (value - self.low) / (self.high - self.low)

    def contains(self, value):
        return self.low <= value <= self.high


class LogUniform(Distribution):
    def __init__(self, low, high):
        self.low = low
        self.high = high
        self._uniform = Uniform(math.log(low), math.log(high))

    def transform(self, unit_value):
        return math.exp(self._uniform.transform(unit_value))

    def inverse_transform(self, value):
        return self._uniform.inverse_transform(math.log(value))

    def contains(self, value):
        return self.low <= value <= self.high


class Categorical(Distribution):
    def __init__(self, options: Sequence):
        self.options = options

    def transform(self, unit_value):
        return self.options[int(unit_value * len(self.options))]

    def inverse_transform(self, value):
        return self.options.index(value) / len(self.options)

    def contains(self, value):
        return value in self.options


def process_dimensions(dimensions: Mapping[str, Any]):
    new_dims = {}

    for name, dim in dimensions.items():
        if isinstance(dim, Distribution):
            new_dims[name] = dim
        elif isinstance(dim, Iterable):
            new_dims[name] = Categorical(dim)
        else:
            raise ValueError(f"Invalid dimension: {dim}")

    return new_dims


class Space:
    def __init__(self, **dimensions: Distribution):
        self.dimensions = process_dimensions(dimensions)

    def items(self):
        return self.dimensions.items()

    def keys(self):
        return self.dimensions.keys()

    def values(self):
        return self.dimensions.values()

    def random_sample(self, n=1, generator=None):
        if generator is None:
            generator = default_generator

        samples = []
        for _ in range(n):
            point = {
                k: d.random_sample(generator=generator)
                for k, d in self.dimensions.items()
            }
            samples.append(point)

        if n == 1:
            return samples[0]

        return samples

    def transform(self, point: Mapping[str, float]):
        """
        Transform a mapping of keys to values in the unit range
        to a mapping of keys to values in the distribution's range.
        """
        return {k: d.transform(point[k]) for k, d in self.dimensions.items()}

    def inverse_transform(self, point: Mapping[str, float]):
        """
        Transform a mapping of keys to values in the distribution's range
        to a mapping of keys to values in the unit range.
        """

        return {k: d.inverse_transform(point[k]) for k, d in self.dimensions.items()}

    def contains(self, point: Mapping[str, float]):
        """
        Returns True if `point` is in the space.
        """
        for k, v in point.items():
            if not self.dimensions[k].contains(v):
                return False
        return True

    def __getitem__(self, key):
        return self.dimensions[key]


class Grid(Space):
    def __init__(self, **dimensions: Any):
        dimensions = process_dimensions(dimensions)

        for k, v in dimensions.items():
            if not isinstance(v, Categorical):
                raise ValueError(f"Grid dimensions must be Categorical: {k}")

        self.dimensions: Dict[str, Categorical] = dimensions


def is_iterable(obj):
    return hasattr(obj, "__iter__")


def to_space(thing):
    if isinstance(thing, Space):
        return thing

    return Space(**thing)
