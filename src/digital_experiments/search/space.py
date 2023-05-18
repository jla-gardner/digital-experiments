"""
Space objects define the space of acceptable values for a given set of
(named) hyperparameters. 

Each hyperparameter is associated with a distribution over values.
These distributions are defined by the Distribution class. 
"""

from collections import UserDict
from typing import Any, Dict, Mapping, Union

from digital_experiments.search.distributions import from_shorthand
from digital_experiments.util import get_random_number

Point = Mapping[str, Any]
UnitPoint = Mapping[str, float]


class Space(UserDict):
    def __setitem__(self, key: str, item: Any) -> None:
        return super().__setitem__(key, from_shorthand(item))

    def random_sample(self, random_number_generator=None) -> Point:
        """
        randomly sample n points from the space
        """
        if random_number_generator is None:
            random_number_generator = get_random_number

        return {
            k: d.random_sample(random_number_generator) for k, d in self.data.items()
        }

    def transform_from_unit_range(self, point: Mapping[str, float]) -> Point:
        """
        Transform a mapping of keys to values in the unit range
        to a mapping of keys to values in the distribution's range.
        """
        return {k: d.transform_from_unit_range(point[k]) for k, d in self.data.items()}

    def transform_to_unit_range(self, point: Mapping[str, float]) -> UnitPoint:
        """
        Transform a mapping of keys to values in the distribution's range
        to a mapping of keys to values in the unit range.
        """

        return {k: d.transform_to_unit_range(point[k]) for k, d in self.data.items()}

    def contains(self, point: Mapping[str, float]):
        """
        Check if a point is in the space.
        """

        for k, v in point.items():
            if k not in self.data:
                raise ValueError(f"Invalid dimension: {k} not in {self.data}")
            if not self.data[k].contains(v):
                return False
        return True


def to_space(thing: Union[Space, Dict[str, Any]]):
    """
    ensure that `thing` is a Space object, converting it from a dictionary
    if necessary
    """
    if isinstance(thing, Space):
        return thing

    return Space(**thing)
