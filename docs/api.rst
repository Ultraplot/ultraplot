.. _api:

=============
API reference
=============

The comprehensive API reference. All of the below objects are imported
into the top-level namespace. Use ``help(uplt.object)`` to read
the docs during a python session.

Please note that UltraPlot removes the associated documentation when functionality
is deprecated (see :ref:`What's New <whats_new>`). However, UltraPlot adheres to
`semantic versioning <https://semver.org>`__, which means old code that uses
deprecated functionality will still work and issue warnings rather than errors
until the first major release (version 1.0.0).

.. important::

   The documentation for "wrapper" functions like `standardize_1d` and `cmap_changer`
   from UltraPlot < 0.8.0 can now be found under individual `~ultraplot.axes.PlotAxes`
   methods like `~ultraplot.axes.PlotAxes.plot` and `~ultraplot.axes.PlotAxes.pcolor`. Note
   that calling ``help(ax.method)`` in a python session will show both the UltraPlot
   documentation and the original matplotlib documentation.

Figure class
============

.. automodule:: UltraPlot.figure

.. automodsumm:: UltraPlot.figure
   :toctree: api


Grid classes
============

.. automodule:: UltraPlot.gridspec

.. automodsumm:: UltraPlot.gridspec
   :toctree: api
   :skip: SubplotsContainer


Axes classes
============

.. automodule:: UltraPlot.axes

.. automodsumm:: UltraPlot.axes
   :toctree: api


Top-level functions
===================

.. automodule:: UltraPlot.ui

.. automodsumm:: UltraPlot.ui
   :toctree: api


Configuration tools
===================

.. automodule:: UltraPlot.config

.. automodsumm:: UltraPlot.config
   :toctree: api
   :skip: inline_backend_fmt, RcConfigurator


Constructor functions
=====================

.. automodule:: UltraPlot.constructor

.. automodsumm:: UltraPlot.constructor
   :toctree: api
   :skip: Colors


Locators and formatters
=======================

.. automodule:: UltraPlot.ticker

.. automodsumm:: UltraPlot.ticker
   :toctree: api


Axis scale classes
==================

.. automodule:: UltraPlot.scale

.. automodsumm:: UltraPlot.scale
   :toctree: api


Colormaps and normalizers
=========================

.. automodule:: UltraPlot.colors

.. automodsumm:: UltraPlot.colors
   :toctree: api
   :skip: ListedColormap, LinearSegmentedColormap, PerceptuallyUniformColormap, LinearSegmentedNorm


Projection classes
==================

.. automodule:: UltraPlot.proj

.. automodsumm:: UltraPlot.proj
   :toctree: api


Demo functions
==============

.. automodule:: UltraPlot.demos

.. automodsumm:: UltraPlot.demos
   :toctree: api


Miscellaneous functions
=======================

.. automodule:: UltraPlot.utils

.. automodsumm:: UltraPlot.utils
   :toctree: api
   :skip: shade, saturate
