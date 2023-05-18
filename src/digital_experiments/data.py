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
