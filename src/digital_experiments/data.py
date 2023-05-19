import operator
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Union


class DoesMathsMixin(ABC):
    """
    A mixin that adds maths methods to a class.

    To use, inherit from this class and implement the `_do_maths` and
    `_do_reverse_maths` methods.
    """

    @abstractmethod
    def _do_maths(self, other_thing, op: Callable):
        """
        Perform the maths operation `self` <`op`> `other_thing`,
        where `self` is the first term in the maths expression.

        Parameters:
        -----------
        other_thing: The second term in the maths expression
        op: The operator to use (e.g. operator.add)
        """

    @abstractmethod
    def _do_reverse_maths(self, other_thing, op: Callable):
        """
        Perform the maths operation `thing` <`op`> `self`,
        where `self` is the second term in the maths expression.

        Parameters:
        -----------
        other_thing: The first term in the maths expression
        op: The operator to use (e.g. operator.add)
        """


def create_math_method(op: Callable) -> Callable:
    def math_method(self, other):
        return self._do_maths(other, op)

    return math_method


def create_reverse_math_method(op: Callable) -> Callable:
    def math_method(self, other):
        return self._do_reverse_maths(other, op)

    return math_method


# Define the mathematical operations you want to support
math_ops = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "truediv": operator.truediv,
    "floordiv": operator.floordiv,
    "mod": operator.mod,
    "pow": operator.pow,
}

# Dynamically add the math methods to the DoesMathsMixin class
for method_name, op in math_ops.items():
    setattr(DoesMathsMixin, f"__{method_name}__", create_math_method(op))
    setattr(DoesMathsMixin, f"__r{method_name}__", create_reverse_math_method(op))


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Data(DoesMathsMixin, DotDict):
    """
    A class that represents a collection of data, and behaves like a dictionary.
    >>> Data({"a": 1, "b": 2})
    Data({"a": 1, "b": 2})
    >>> Data(a=1, b=2)
    Data({"a": 1, "b": 2})

    Additional functionality:

    - Maths operations are applied as follows:

    >>> Data({"a": 1, "b": 2}) + 1 # add 1 to each value
    Data({"a": 2, "b": 3})
    >>> Data({"a": 1, "b": 2}) * Data({"a": 2, "b": 3})
    Data({"a": 2, "b": 6})
    >>> Data({"a": 1, "b": 2}) ** 2
    Data({"a": 1, "b": 4})

    - Data fields can be accessed using [square bracket] or .dot notation:

    >>> data = Data({"a": 1, "b": 2})
    >>> data["a"]
    1
    >>> data.b
    2

    - The `.map` instance method returns a new `Data` object with the
    same keys, but with the values mapped by the function passed in:

    >>> data = Data({
    ...     "a": [1, 2, 3],
    ...     "b": [4, 5, 6, 7],
    ... })
    >>> data.map(sum)
    Data({"a": 6, "b": 22})
    >>> data.map(len)
    Data({"a": 3, "b": 4})

    - The `.apply` class method returns a new `Data` object with the
    with the same keys, and where the values are the result of applying
    the function passed in to multiple data objects:

    >>> data1 = Data({"a": 1, "b": 2})
    >>> data2 = Data({"a": 3, "b": 4})
    >>> Data.apply(lambda x, y: x + y, data1, data2)
    Data({"a": 4, "b": 6})
    """

    def _do_maths(self, thing, operation):
        # if the other thing is a Data object
        if isinstance(thing, Data):
            # check that the keys are the same
            assert set(self.keys()) == set(thing.keys())
            # and then do the zip up the keys and resulting operations
            return Data({k: operation(v, thing[k]) for k, v in self.items()})

        # otherwise, attempt to do the operation with the other thing
        # for each of the values in the Data object
        return Data({k: operation(v, thing) for k, v in self.items()})

    def _do_reverse_maths(self, thing, operation):
        # called as e.g. `thing` + `data`
        # so we e.g. add `thing` to each of the values in `data`
        return Data({k: operation(thing, v) for k, v in self.items()})

    def map(self, func: Callable) -> "Data":
        """
        Return a new `Data` object with the same keys, but with the
        values mapped by the function passed in.
        """
        return Data({k: func(v) for k, v in self.items()})

    @classmethod
    def apply(cls, func: Callable, *data_objects: "Data") -> "Data":
        """
        Return a new `Data` object with the same keys, and where the
        values are the result of applying the function passed in to
        multiple data objects.

        Parameters:
        -----------
        func: The function to apply to the data objects. Each data object
            will be passed in as a separate argument in the order they
            are given.
        *data_objects: The data objects to apply the function to.

        Returns:
        --------
        A new `Data` object with the same keys and new values.

        Example:
        --------
        >>> def concatenate(*lists):
        ...     return [item for sublist in lists for item in sublist]
        >>> d1 = Data(a=[1, 2], b=[10, 11])
        >>> d2 = Data(a=[3, 4], b=[12, 13])
        >>> Data.apply(concatenate, d1, d2)
        Data({"a": [1, 2, 3, 4], "b": [10, 11, 12, 13]})
        """
        # check that all the keys are the same
        if not all(
            set(data.keys()) == set(data_objects[0].keys()) for data in data_objects
        ):
            raise ValueError("All data objects must have the same keys")

        # perform the functions, and zip up the keys and resulting values
        return Data(
            {
                k: func(*[data[k] for data in data_objects])
                for k in data_objects[0].keys()
            }
        )

    def __repr__(self):
        return f"Data({super().__repr__()})"
