:github_url: https://github.com/jla-gardner/digital-experiments

.. toctree::
   :maxdepth: 4
   :hidden:
   :caption: Contents:

   Home <self>
   usage
   control
   api

.. image:: logo.svg
   :alt: digital-experiments logo
   :width: 450px
   :align: center

**Keeping track of the results of coding experiments can be a pain.** 
Over time, code and dependencies can change, and without careful record-keeping, it becomes difficult to remember and reproduce optimal configurations and results.


:code:`digital-experiments` **tracks these things for you.**
To enable this automation, wrap your experiment's main function with the :func:`@experiment <digital_experiments.experiment>` decorator.
Every time your function is called, the following information is saved to disk:

- the inputs (:code:`args`, :code:`kwargs` and defaults)
- the output/s (any, arbitrary object)
- the code of the function
- the current :code:`git` information (if available)
- timing information
- python environment information

.. Use the `💻 digital-experiments 🧪 <https://github.com/jla-gardner/digital-experiments>`_ python package to track the results of your coding experiments.

Installation
------------

.. code-block:: console
   :class: copy-button

   $ pip install digital-experiments


Quickstart
----------

The main entry point to ``digital-experiments`` is the :func:`@experiment <digital_experiments.experiment>` decorator. This can be used to wrap any python function:

.. code-block:: python
   :class: copy-button

   from digital_experiments import experiment

   @experiment
   def example(a, b):
      return a ** b

This decorator leaves the apparent behaviour of the function unchanged:

.. code-block:: python

      >>> example(2, 3)
      8
      >>> example(b=2, a=3)
      9


Under-the-hood, these results have been saved. You can access these results using the :func:`observations<digital_experiments.core.Experiment.observations>` method attached to the experiment:

.. code-block:: python

      >>> example.observations()
      [Observation(<id1>, {'a': 2, 'b': 3} → 8}),
       Observation(<id2>, {'a': 3, 'b': 2} → 9})]

If you have :mod:`pandas` installed, you can also access the results as a :class:`pandas.DataFrame`:

.. code-block:: python

      >>> example.to_dataframe()
            id config.a config.b  result
      0  <id1>       2         3       8
      1  <id2>       3         2       9

For further information on how to use ``digital-experiments``, see :doc:`the usage page <usage>`.
 
Complete documentation of the API is available :doc:`here <api>`.



