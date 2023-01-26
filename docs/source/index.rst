.. digital-experiments documentation master file, created by
   sphinx-quickstart on Wed Jan 25 11:37:34 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:github_url: https://github.com/jla-gardner/digital-experiments

💻 digital-experiments 🧪
=========================

.. warning::

   This project is under active development. Until version 1.0.0 is released, breaking changes to the API may occur.

Use this python package to locally track the results of your experiments, and automatically optimise their parameters.

Installation
------------
.. _installation:

.. code-block:: console

   (.venv) $ pip install digital-experiments

.. _usage:

Usage
-----

.. The main concept of this package is that of an `experiment`. An experiment is a peice of code that takes as input some configuration, does some processing (the actual experiment) and outputs some result. You've seen such experiments before: python functions.

The main entry point to `digital-experiments` is the :func:`@experiment<digital_experiments.experiment>` decorator. This can be used to wrap any function that takes a set of parameters and returns a result:

.. code-block:: python

      from digital_experiments import experiment

      @experiment
      def example(a, b):
         return a ** b

At first glance, this decorator doesn't change the behaviour of the function at all:

.. code-block:: python

      >>> example(2, 3)
      8
      >>> example(b=2, a=3)
      9

Under the hood, however, the parameters and results from each function call are stored locally. These can be accessed (as a :class:`pandas.DataFrame`) using the :func:`get_results<digital_experiments.results_for>` method:

.. code-block:: python

      >>> from digital_experiments import get_results
      >>> get_results(example)

.. raw:: html
   :file: _static/df.html


Overview
--------

.. toctree::
   :maxdepth: 1

   Home <self>

.. toctree::
   :maxdepth: 1
   :caption: Examples:

   examples/basic-usage.ipynb
   examples/advanced-usage.ipynb
   examples/simple-optimization.ipynb

.. toctree::
   :maxdepth: 3
   :caption: API Reference:

   api

