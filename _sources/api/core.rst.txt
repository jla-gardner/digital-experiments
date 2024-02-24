####
Core
####


The primary functionality of the :doc:`digital-experiments <../index>` package 
is exposed via the :func:`~digital_experiments.experiment` decorator. Wrapping
a function with this decorator returns an :class:`~digital_experiments.core.Experiment`
object, with identical signature to the original function. 

Use the :meth:`(experiment).observations <digital_experiments.core.Experiment.observations>` method to access the results of the
experiment, which are stored as :class:`~digital_experiments.core.Observation`
objects.

*Within* an experiment, use the :func:`~digital_experiments.current_id` and
:func:`~digital_experiments.current_dir` functions to access the automatically
assigned experiment ID and related storage directory.

Use the :func:`~digital_experiments.time_block` function to time 
certain blocks of code within the experiment.

`Kitchen Sink <https://idioms.thefreedictionary.com/everything+but+the+kitchen+sink>`__ example
===============================================================================================

An example that intends to display the full range of available functionality:

.. literalinclude:: kitchen_sink.py
    :language: python

Available functions
===================

.. autofunction:: digital_experiments.experiment
.. autofunction:: digital_experiments.current_id
.. autofunction:: digital_experiments.current_dir
.. autofunction:: digital_experiments.time_block


Internal classes
================

.. autoclass:: digital_experiments.core.Experiment
    :members:
.. autoclass:: digital_experiments.core.Observation