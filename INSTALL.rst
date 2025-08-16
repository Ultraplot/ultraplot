Installation
============

Ultraplot is published on `PyPi <https://pypi.org/project/ultraplot/>`__
and `conda-forge <https://conda-forge.org>`__. It can be installed
with ``pip`` or ``conda`` as follows:

.. code-block:: bash

   pip install ultraplot
   conda install -c conda-forge ultraplot

Likewise, an existing installation of ultraplot can be upgraded to the latest version with:

.. code-block:: bash

   pip install --upgrade ultraplot
   conda upgrade ultraplot


To install a development version of ultraplot, you can use
``pip install git+https://github.com/ultraplot/ultraplot.git``
or clone the repository and run ``pip install -e .`` inside
the ``ultraplot`` folder.

ultraplot's only hard dependency is `matplotlib <https://matplotlib.org/>`__.
The *soft* dependencies are `cartopy <https://cartopy.readthedocs.io/stable/>`__,
`basemap <https://matplotlib.org/basemap/index.html>`__,
`xarray <http://xarray.pydata.org>`__, and `pandas <https://pandas.pydata.org>`__.
See the documentation for details.
