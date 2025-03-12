.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/UltraPlotLogo.svg
    :alt: UltraPlot Logo
    :width: 100%

|build-status| |coverage| |docs| |pypi| |code-style| |pre-commit| |pr-welcome| |license|

A succinct `matplotlib <https://matplotlib.org/>`__ wrapper for making beautiful,
publication-quality graphics. It builds upon ProPlot_ and transports it into the modern age (supporting mpl 3.9.0+).

.. _ProPlot: https://github.com/proplot-dev/

Why UltraPlot? | Write Less, Create More
=========================================
.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/logo/whyUltraPlot.svg
    :width: 100%
    :alt: Comparison of ProPlot and UltraPlot
    :align: center

Documentation
=============

The documentation is `published on readthedocs <https://ultraplot.readthedocs.io>`__.

Installation
============

UltraPlot is published on `PyPi <https://pypi.org/project/ultraplot/>`__ and
`conda-forge <https://conda-forge.org>`__. It can be installed with ``pip`` or
``conda`` as follows:

.. code-block:: bash

   pip install ultraplot
   conda install -c conda-forge ultraplot

Likewise, an existing installation of UltraPlot can be upgraded
to the latest version with:

.. code-block:: bash

   pip install --upgrade ultraplot
   conda upgrade ultraplot

To install a development version of UltraPlot, you can use
``pip install git+https://github.com/ultraplot/ultraplot.git``
or clone the repository and run ``pip install -e .``
inside the ``ultraplot`` folder.


.. |build-status| image::  https://github.com/ultraplot/ultraplot/actions/workflows/build-ultraplot.yml/badge.svg

.. |code-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg

.. |pr-welcome| image:: https://img.shields.io/badge/PRs-welcome-brightgreen

.. |docs| image:: https://readthedocs.org/projects/ultraplot/badge/?version=latest
   :alt: docs
   :target: https://ultraplot.readthedocs.io/en/latest/?badge=latest

.. |pypi| image:: https://img.shields.io/pypi/v/ultraplot?color=83%20197%2052
   :alt: pypi
   :target: https://pypi.org/project/ultraplot/

.. |license| image:: https://img.shields.io/github/license/ultraplot/ultraplot.svg
   :alt: license
   :target: LICENSE.txt

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/Ultraplot/ultraplot/main.svg
   :target: https://results.pre-commit.ci/latest/github/Ultraplot/ultraplot/main
   :alt: pre-commit.ci status

.. |coverage| image:: https://codecov.io/gh/Ultraplot/ultraplot/graph/badge.svg?token=C6ZB7Q9II4 
   :target: https://codecov.io/gh/Ultraplot/ultraplot
   :alt: coverage
