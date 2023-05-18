import math
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Mapping, Sequence, TypeVar, Union

from digital_experiments.util import get_random_number, is_iterable


class Distribution(ABC):
    def random_sample(self, random_number_generator=None):
        """
        Randomly sample n points from the distribution.
        """
        if random_number_generator is None:
            random_number_generator = get_random_number

        unit_value = random_number_generator()
        return self.transform_from_unit_range(unit_value)

    @abstractmethod
    def transform_from_unit_range(self, unit_value: float) -> any:
        """
        Takes `value` in the unit range and transforms it to the
        distribution's range.
        """

    @abstractmethod
    def transform_to_unit_range(self, value: any) -> float:
        """
        Takes `value` in the distribution's range and transforms it to the
        unit range.
        """

    @abstractmethod
    def contains(self, value: Any) -> bool:
        """
        Returns True if `value` is in the distribution's range.
        """


class Uniform(Distribution):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def transform_from_unit_range(self, unit_value):
        return self.low + (self.high - self.low) * unit_value

    def transform_to_unit_range(self, value):
        return (value - self.low) / (self.high - self.low)

    def contains(self, value):
        return self.low <= value <= self.high


class LogUniform(Distribution):
    def __init__(self, low, high):
        self.low = low
        self.high = high
        self._uniform = Uniform(math.log(low), math.log(high))

    def transform_from_unit_range(self, unit_value):
        return math.exp(self._uniform.transform_from_unit_range(unit_value))

    def transform_to_unit_range(self, value):
        return self._uniform.transform_to_unit_range(math.log(value))

    def contains(self, value):
        return self.low <= value <= self.high


T = TypeVar("T")
"""A type variable for the type of the options."""


class Categorical(Distribution):
    def __init__(self, options: Sequence[T]):
        self.options = options

    def transform_from_unit_range(self, unit_value):
        return self.options[int(unit_value * len(self.options))]

    def transform_to_unit_range(self, value: T):
        return self.options.index(value) / len(self.options)

    def contains(self, value: T):
        return value in self.options


def from_shorthand(distribution) -> Distribution:
    """
    Convert a shorthand notation for a distribution into a Distribution object.
    """

    if isinstance(distribution, Distribution):
        return distribution

    if is_iterable(distribution):
        return Categorical(distribution)

    raise ValueError(f"Invalid distribution: {distribution}")


def convert_from_shorthand(distributions: Mapping[str, Any]) -> Dict[str, Distribution]:
    """
    parse a dictionary of dimensions with optional shorthand notations
    into a dictionary of Dimension objects

    Example:
    --------
    >>> process_dimensions({"foo": [1, 2, 3], "bar": Uniform(0, 1)})
    {"foo": Categorical([1, 2, 3]), "bar": Uniform(0, 1)}
    """

    return {name: from_shorthand(d) for name, d in distributions.items()}
