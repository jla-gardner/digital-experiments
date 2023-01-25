.. digital-experiments documentation master file, created by
   sphinx-quickstart on Wed Jan 25 11:37:34 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:github_url: https://github.com/jla-gardner/digital-experiments

💻🧪 digital-experiments
========================

.. warning::

   This project is under active development.

Installation
------------
.. _installation:

.. code-block:: console

   (.venv) $ pip install digital-experiments

Usage
-----
.. _usage:

.. code-block:: python

      from digital_experiments import experiment

      @experiment
      def example(a: float, b: int):
         return a ** b
      
      example(2, 3)
      # 8.0


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

