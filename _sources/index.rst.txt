:github_url: https://github.com/jla-gardner/digital-experiments

.. toctree::
      :maxdepth: 1
      :hidden:

      Quickstart <self>

.. toctree::
      :maxdepth: 2
      :hidden: 
      :caption: Usage:
   
      usage
      control

.. toctree::
      :maxdepth: 3
      :hidden:
      :caption: API:

      api/core
      api/callbacks
      api/backends
      api/controllers

.. image:: logo.svg
   :alt: digital-experiments logo
   :width: 450px
   :align: center
   :target: .


`digital-experiments <.>`_ is a lightweight tool for automatically 
tracking and analysing the configuration and results of coding experiments.

Compared to other such tools, digital-experiments:

- **improves reproducibility** by not only tracking the inputs and outputs of 
  an experiment, but also the exact code and environment used at run-time.
- **improves interpretability** by automatically associating results with the 
  experiment that generated them. No more :code:`results-v2-final.csv` files.


Quickstart
----------

.. grid:: 1 1 2 2

      .. grid-item::

            .. code-block:: python
                  :class: copy-button
                  :caption: 1: definition: :code:`example.py`

                  from digital_experiments import (
                        experiment,
                  )

                  @experiment
                  def example(a: int, b: int = 3):
                        # perform your experiment here:
                        #   - train a model
                        #   - run a simulation
                        #   - etc.
                        # and return the result 
                        # (any arbitrary object/s)
                        return a ** b

                  if __name__ == "__main__":
                        # run the experiment
                        # like any other function
                        print(example(2))
                        print(example(b=2, a=3))

            .. code-block:: text
                  :class: copy-button
                  :caption: 2: running

                  $ python example.py
                  8
                  9

            
            
      .. grid-item::

            .. code-block:: pycon
                  :class: copy-button
                  :caption: 3: analysis

                  >>> from example import example

                  >>> for o in example.observations():
                  ...     print(o.config, "→", o.result)
                  {'a': 2, 'b': 3} →  8
                  {'a': 3, 'b': 2} →  9

                  >>> o.metadata["code"]
                  @experiment
                  def example(a, b):
                      return a ** b
                  
                  >>> o.metadata["timing"]
                  {
                    "start": "2024-02-24 10:10:01",
                    "end": "2024-02-24 10:10:01",
                    "duration": 0.000007
                  }

                  >>> o.metadata["environment"].keys()
                  ['system', 'pip_freeze', 'git']

                  >>> example.to_dataframe()
                        id config.a config.b  result
                  0  <id1>       2         3       8
                  1  <id2>       3         2       9


See a :doc:`Kitchen Sink example <api/core>` for a summary of all the functionality
of digital-experiments, or :doc:`The Basics <usage>` for a step-by-step guide. 


Installation
------------

.. code-block:: console
   :class: copy-button

   $ pip install digital-experiments

Extending :code:`digital-experiments`
-------------------------------------

`digital-experiments <.>`_ is designed to be easily extended and hacked
to suit your needs.
Three obvious ways this can be done are by implementing custom:

1. :class:`Callbacks <digital_experiments.callbacks.Callback>` to trigger
   custom logic before and after each experiment is run.
2. :class:`Backends <digital_experiments.backends.Backend>` to allow you to
   save your :class:`~digital_experiments.core.Observation` to disk in custom
   formats.
3. :class:`Controllers <digital_experiments.controllers.Controller>` to define 
   automated workflows for your experiments.

Contributing
------------

Contributions are welcome! Head on over to the `GitHub repository
<hhttps://github.com/jla-gardner/digital-experiments>`_ to get started.