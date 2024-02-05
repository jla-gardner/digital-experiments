#########
Callbacks
#########

Callbacks are a way to extend the functionality of an experiment.


Avaliable callbacks
===================

.. autoclass:: digital_experiments.callbacks.SaveLogs


Implementing your own callbacks
===============================

.. autoclass:: digital_experiments.callbacks.Callback
    :members:


The callback lifecycle
----------------------

We can learn about the lifecycle of a callback by implementing a simple callback
of our own:

.. code-block:: python

    from typing import Callable, Any
    from digital_experiments import Callback, Observation


    class DummyCallback(Callback):
        def __init__(self):
            super().__init__()
            print("I'm being initialized")

        def setup(self, function: Callable) -> None:
            print("I'm being setup")

        def start(self, id: str, config: dict[str, Any]) -> None:
            print(f"Experiment {id} is starting")

        def end(self, observation: Observation) -> None:
            print(f"Experiment {observation.id} has ended")
            observation.metadata["dummy"] = "hello there"

Each callback to be used by an experiment is instantiated by the user and passed
to the :func:`@experiment <digital_experiments.experiment>` decorator:

.. code-block:: python

    >>> callback = DummyCallback()
    "I'm being initialized"

When an experiment is first imported/defined, the :func:`setup <digital_experiments.callbacks.Callback.setup>`
method is called:

.. code-block:: python

    >>> @experiment(callbacks=[callback])
    ... def my_experiment():
            print("my_experiment is running")

    "I'm being setup"

.. hint::
    These two steps typically occur one after the other when the experiment is
    decorated using compact syntax ``@experiment(callbacks=[DummyCallback()])``.

Everytime the experiment is subsequently run, the :func:`start <digital_experiments.callbacks.Callback.start>`
and :func:`end <digital_experiments.callbacks.Callback.end>` methods are called:

.. code-block:: python

    >>> my_experiment()
    "Experiment 1 is starting"
    "my_experiment is running"
    "Experiment 1 has ended"

    >>> my_experiment()
    "Experiment 2 is starting"
    "my_experiment is running"
    "Experiment 2 has ended"

    >>> my_experiment()
    "Experiment 3 is starting"
    "my_experiment is running"
    "Experiment 3 has ended"

We can see that the :func:`end <digital_experiments.callbacks.Callback.end>` method has worked:

.. code-block:: python

    >>> my_experiment.observations[0].metadata["dummy"]
    "hello there"











