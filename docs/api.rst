.. _api:

=============
API reference
=============

The comprehensive API reference. All of the below objects are imported
into the top-level namespace. Use ``help(uplt.object)`` to read
the docs during a python session.

Please note that UltraPlot removes the associated documentation when functionality
is deprecated (see :ref:`What's New <whats_new>`). However, UltraPlot adheres to
`effort versioning <https://jacobtomlinson.dev/effver/>`__, which means old code that uses
deprecated functionality will still work and issue warnings rather than errors.

.. important::

   The documentation for "wrapper" functions like `standardize_1d` and `cmap_changer`
   from UltraPlot < 0.8.0 can now be found under individual :class:`~ultraplot.axes.PlotAxes`
   methods like :func:`~ultraplot.axes.PlotAxes.plot` and :func:`~ultraplot.axes.PlotAxes.pcolor`. Note
   that calling ``help(ax.method)`` in a python session will show both the UltraPlot
   documentation and the original matplotlib documentation.

Figure class
============

.. automodule:: ultraplot.figure
   :no-private-members:

.. automodsumm:: ultraplot.figure
   :toctree: api


Grid classes
============

.. automodule:: ultraplot.gridspec
   :no-private-members:



.. automodsumm:: ultraplot.gridspec
   :toctree: api
   :skip: SubplotsContainer


Axes classes
============

.. automodule:: ultraplot.axes
    :no-private-members:

.. automodsumm:: ultraplot.axes
   :toctree: api

Top-level functions
===================

.. automodule:: ultraplot.ui
    :no-private-members:

.. automodsumm:: ultraplot.ui
   :toctree: api


Configuration tools
===================

.. automodule:: ultraplot.config
   :no-private-members:

.. automodsumm:: ultraplot.config
   :toctree: api
   :skip: inline_backend_fmt, RcConfigurator


Constructor functions
=====================

.. automodule:: ultraplot.constructor
   :no-private-members:

.. automodsumm:: ultraplot.constructor
   :toctree: api
   :skip: Colors


Locators and formatters
=======================

.. automodule:: ultraplot.ticker
   :no-private-members:

.. automodsumm:: ultraplot.ticker
   :toctree: api


Axis scale classes
==================

.. automodule:: ultraplot.scale
   :no-private-members:

.. automodsumm:: ultraplot.scale
   :toctree: api


Colormaps and normalizers
=========================

.. automodule:: ultraplot.colors
   :no-private-members:

.. automodsumm:: ultraplot.colors
   :toctree: api
   :skip: ListedColormap, LinearSegmentedColormap, PerceptuallyUniformColormap, LinearSegmentedNorm


Projection classes
==================

.. automodule:: ultraplot.proj
   :no-private-members:

.. automodsumm:: ultraplot.proj
   :toctree: api


Demo functions
==============

.. automodule:: ultraplot.demos
   :no-private-members:

.. automodsumm:: ultraplot.demos
   :toctree: api


Miscellaneous functions
=======================

.. automodule:: ultraplot.utils
   :no-private-members:

.. automodsumm:: ultraplot.utils
   :toctree: api
   :skip: shade, saturate
