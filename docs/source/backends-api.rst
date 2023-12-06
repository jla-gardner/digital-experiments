########
Backends
########

Backends are responsible for storing and retrieving experiment data. 
A single backend is instantiated and associated with an experiment when it is
created. By saving observations to disk, backends allow follow up experiments
and anaylsis to be performed in future python sessions.

Available backends
==================

.. autoclass:: digital_experiments.backends.PickleBackend
.. autoclass:: digital_experiments.backends.JSONBackend


Creating your own backend
=========================

Creating your own backend involves subclassing :class:`Backend <digital_experiments.backends.Backend>`, implementing the
abstract methods, and registering your implementation so that you can subsequently use it by name.

.. autofunction:: digital_experiments.backends.register_backend
.. autoclass:: digital_experiments.backends.Backend
    :members:
