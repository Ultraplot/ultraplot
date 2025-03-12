.. _cartopy: https://scitools.org.uk/cartopy/docs/latest/

.. _basemap: https://matplotlib.org/basemap/index.html

.. _seaborn: https://seaborn.pydata.org

.. _pandas: https://pandas.pydata.org

.. _xarray: http://xarray.pydata.org/en/stable/

.. _rainbow: https://doi.org/10.1175/BAMS-D-13-00155.1

.. _xkcd: https://blog.xkcd.com/2010/05/03/color-survey-results/

.. _opencolor: https://yeun.github.io/open-color/

.. _cmocean: https://matplotlib.org/cmocean/

.. _fabio: http://www.fabiocrameri.ch/colourmaps.php

.. _brewer: http://colorbrewer2.org/

.. _sciviscolor: https://sciviscolor.org/home/colormoves/

.. _matplotlib: https://matplotlib.org/stable/tutorials/colors/colormaps.html

.. _seacolor: https://seaborn.pydata.org/tutorial/color_palettes.html

.. _texgyre: https://frommindtotype.wordpress.com/2018/04/23/the-tex-gyre-font-family/

.. _why:

============
Why UltraPlot?
============

Matplotlib is an extremely versatile plotting package used by
scientists and engineers far and wide. However,
matplotlib can be cumbersome or repetitive for users who...

* Make highly complex figures with many subplots.
* Want to finely tune their annotations and aesthetics.
* Need to make new figures nearly every day.

UltraPlot's core mission is to provide a smoother plotting experience for
matplotlib's most demanding users. We accomplish this by *expanding upon*
matplotlib's :ref:`object-oriented interface <usage_background>`. UltraPlot
makes changes that would be hard to justify or difficult to incorporate
into matplotlib itself, owing to differing design choices and backwards
compatibility considerations.

This page enumerates these changes and explains how they address the
limitations of matplotlib's default interface. To start using these
features, see the :ref:`usage introduction <usage>`
and the :ref:`user guide <ug_basics>`.

.. _why_less_typing:

Less typing, more plotting
==========================

Limitation
----------

Matplotlib users often need to change lots of plot settings all at once. With
the default interface, this requires calling a series of one-liner setter methods.

This workflow is quite verbose -- it tends to require "boilerplate code" that
gets copied and pasted a hundred times. It can also be confusing -- it is
often unclear whether properties are applied from an :class:`~matplotlib.axes.Axes`
setter (e.g. `~matplotlib.axes.Axes.set_xlabel` and
`~matplotlib.axes.Axes.set_xticks`), an `~matplotlib.axis.XAxis` or
`~matplotlib.axis.YAxis` setter (e.g.
`~matplotlib.axis.Axis.set_major_locator` and
`~matplotlib.axis.Axis.set_major_formatter`), a :class:`~matplotlib.spines.Spine`
setter (e.g. `~matplotlib.spines.Spine.set_bounds`), or a "bulk" property
setter (e.g. `~matplotlib.axes.Axes.tick_params`), or whether one must dig
into the figure architecture and apply settings to several different objects.
It seems like there should be a more unified, straightforward way to change
settings without sacrificing the advantages of object-oriented design.

Changes
-------

UltraPlot includes the `ultraplot.axes.Axes.format` command to resolve this.
Think of this as an expanded and thoroughly documented version of the
`matplotlib.artist.Artist.update` command. :func:`~ultraplot.axes.Axes.format` can modify things
like axis labels and titles and apply new :ref:`"rc" settings <why_rc>` to existing
axes. It also integrates with various :ref:`constructor functions <why_constructor>`
to help keep things succinct. Further, the `ultraplot.figure.Figure.format`
and `ultraplot.gridspec.SubplotGrid.format` commands can be used to
:func:`~ultraplot.axes.Axes.format` several subplots at once.

Together, these features significantly reduce the amount of code needed to create
highly customized figures. As an example, it is trivial to see that...

.. code-block:: python

   import ultraplot as uplt
   fig, axs = uplt.subplots(ncols=2)
   axs.format(color='gray', linewidth=1)
   axs.format(xlim=(0, 100), xticks=10, xtickminor=True, xlabel='foo', ylabel='bar')

is much more succinct than...

.. code-block:: python

   import matplotlib.pyplot as plt
   import matplotlib.ticker as mticker
   import matplotlib as mpl
   with mpl.rc_context(rc={'axes.linewidth': 1, 'axes.edgecolor': 'gray'}):
       fig, axs = plt.subplots(ncols=2, sharey=True)
       axs[0].set_ylabel('bar', color='gray')
       for ax in axs:
           ax.set_xlim(0, 100)
           ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
           ax.tick_params(width=1, color='gray', labelcolor='gray')
           ax.tick_params(axis='x', which='minor', bottom=True)
           ax.set_xlabel('foo', color='gray')

Links
-----

* For an introduction, see :ref:`this page <ug_format>`.
* For `~ultraplot.axes.CartesianAxes` formatting,
  see :ref:`this page <ug_cartesian>`.
* For :class:`~ultraplot.axes.PolarAxes` formatting,
  see :ref:`this page <ug_polar>`.
* For `~ultraplot.axes.GeoAxes` formatting,
  see :ref:`this page <ug_geoformat>`.

.. _why_constructor:

Class constructor functions
===========================

Limitation
----------

Matplotlib and `cartopy`_ define several classes with verbose names like
`~matplotlib.ticker.MultipleLocator`, `~matplotlib.ticker.FormatStrFormatter`,
and `~cartopy.crs.LambertAzimuthalEqualArea`. They also keep them out of the
top-level package namespace. Since plotting code has a half life of about 30 seconds,
typing out these extra class names and import statements can be frustrating.

Parts of matplotlib's interface were designed with this in mind.
`Backend classes <https://matplotlib.org/faq/usage_faq.html#what-is-a-backend>`__,
`native axes projections <https://matplotlib.org/stable/api/projections_api.html>`__,
`axis scales <https://matplotlib.org/stable/gallery/scales/scales.html>`__,
`colormaps <https://matplotlib.org/stable/tutorials/colors/colormaps.html>`__,
`box styles <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.FancyBboxPatch.html>`__,
`arrow styles <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.FancyArrowPatch.html>`__,
and `arc styles <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.ConnectionStyle.html>`__
are referenced with "registered" string names,
as are `basemap projections <https://matplotlib.org/basemap/users/mapsetup.html>`__.
So, why not "register" everything else?

Changes
-------

In UltraPlot, tick locators, tick formatters, axis scales, property cycles, colormaps,
normalizers, and `cartopy`_ projections are all "registered". This is accomplished
by defining "constructor functions" and passing various keyword arguments through
these functions.

The constructor functions also accept intuitive inputs alongside "registered"
names. For example, a scalar passed to :class:`~ultraplot.constructor.Locator`
returns a `~matplotlib.ticker.MultipleLocator`, a
lists of strings passed to :class:`~ultraplot.constructor.Formatter` returns a
`~matplotlib.ticker.FixedFormatter`, and :class:`~ultraplot.constructor.Cycle`
and :class:`~ultraplot.constructor.Colormap` accept colormap names, individual colors, and
lists of colors. Passing the relevant class instance to a constructor function
simply returns it, and all the registered classes are available in the top-level
namespace -- so class instances can be directly created with e.g.
``uplt.MultipleLocator(...)`` or ``uplt.LogNorm(...)`` rather than
relying on constructor functions.

The below table lists the constructor functions and the keyword arguments that use them.

================================  ============================================================  ==============================================================================  ================================================================================================================================================================================================
Function                          Return type                                                   Used by                                                                         Keyword argument(s)
================================  ============================================================  ==============================================================================  ================================================================================================================================================================================================
:class:`~ultraplot.constructor.Proj`       `~cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap`  :func:`~ultraplot.figure.Figure.add_subplot` and :func:`~ultraplot.figure.Figure.add_subplots`  ``proj=``
:class:`~ultraplot.constructor.Locator`    :class:`~matplotlib.ticker.Locator`                                  :func:`~ultraplot.axes.Axes.format` and :func:`~ultraplot.axes.Axes.colorbar`                   ``locator=``, ``xlocator=``, ``ylocator=``, ``minorlocator=``, ``xminorlocator=``, ``yminorlocator=``, ``ticks=``, ``xticks=``, ``yticks=``, ``minorticks=``, ``xminorticks=``, ``yminorticks=``
:class:`~ultraplot.constructor.Formatter`  :class:`~matplotlib.ticker.Formatter`                                :func:`~ultraplot.axes.Axes.format` and :func:`~ultraplot.axes.Axes.colorbar`                   ``formatter=``, ``xformatter=``, ``yformatter=``, ``ticklabels=``, ``xticklabels=``, ``yticklabels=``
:class:`~ultraplot.constructor.Scale`      `~matplotlib.scale.ScaleBase`                                 :func:`~ultraplot.axes.Axes.format`                                                     ``xscale=``, ``yscale=``
:class:`~ultraplot.constructor.Colormap`   :class:`~matplotlib.colors.Colormap`                                 2D :class:`~ultraplot.axes.PlotAxes` commands                                            ``cmap=``
:class:`~ultraplot.constructor.Norm`       :class:`~matplotlib.colors.Normalize`                                2D :class:`~ultraplot.axes.PlotAxes` commands                                            ``norm=``
:class:`~ultraplot.constructor.Cycle`      :class:`~cycler.Cycler`                                              1D :class:`~ultraplot.axes.PlotAxes` commands                                            ``cycle=``
================================  ============================================================  ==============================================================================  ================================================================================================================================================================================================

Links
-----

* For more on axes projections,
  see :ref:`this page <ug_proj>`.
* For more on axis locators,
  see :ref:`this page <ug_locators>`.
* For more on axis formatters,
  see :ref:`this page <ug_formatters>`.
* For more on axis scales,
  see :ref:`this page <ug_scales>`.
* For more on datetime locators and formatters,
  see :ref:`this page <ug_datetime>`.
* For more on colormaps,
  see :ref:`this page <ug_apply_cmap>`.
* For more on normalizers,
  see :ref:`this page <ug_apply_norm>`.
* For more on color cycles, see
  :ref:`this page <ug_apply_cycle>`.

.. _why_spacing:

Automatic dimensions and spacing
================================

Limitation
----------

Matplotlib plots tend to require "tweaking" when you have more than one
subplot in the figure. This is partly because you must specify the physical
dimensions of the figure, despite the fact that...

#. The subplot aspect ratio is generally more relevant than the figure
   aspect ratio. A default aspect ratio of ``1`` is desirable for most plots, and
   the aspect ratio must be held fixed for :ref:`geographic and polar <ug_proj>`
   projections and most `~matplotlib.axes.Axes.imshow` plots.
#. The subplot width and height control the "apparent" size of lines, markers,
   text, and other plotted content. If the figure size is fixed, adding more
   subplots will decrease the average subplot size and increase the "apparent"
   sizes. If the subplot size is fixed instead, this can be avoided.

Matplotlib also includes `"tight layout"
<https://matplotlib.org/stable/tutorials/intermediate/tight_layout_guide.html>`__
and `"constrained layout"
<https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html>`__
algorithms that can help users avoid having to tweak
`~matplotlib.gridspec.GridSpec` spacing parameters like `left`, `bottom`, and `wspace`.
However, these algorithms are disabled by default and somewhat `cumbersome to configure
<https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html#padding-and-spacing>`__.
They also cannot apply different amounts of spacing between different subplot row and
column boundaries.

Changes
-------

By default, UltraPlot fixes the physical dimensions of a *reference subplot* rather
than the figure. The reference subplot dimensions are controlled with the `refwidth`,
`refheight`, and `refaspect` :class:`~ultraplot.figure.Figure` keywords, with a default
behavior of ``refaspect=1`` and ``refwidth=2.5`` (inches). If the `data aspect ratio
<https://matplotlib.org/stable/gallery/subplots_axes_and_figures/axis_equal_demo.html>`__
of the reference subplot is fixed (as with :ref:`geographic <ug_geo>`,
:ref:`polar <ug_polar>`, `~matplotlib.axes.Axes.imshow`, and
:func:`~ultraplot.axes.Axes.heatmap` plots) then this is used instead of `refaspect`.

Alternatively, you can independently specify the width or height of the *figure*
with the `figwidth` and `figheight` parameters. If only one is specified, the
other is adjusted to preserve subplot aspect ratios. This is very often useful
when preparing figures for submission to a publication. To request figure
dimensions suitable for submission to a :ref:`specific publication <journal_table>`,
use the `journal` keyword.

By default, UltraPlot also uses :ref:`its own tight layout algorithm <ug_tight>` --
preventing text labels from overlapping with subplots. This algorithm works with the
`ultraplot.gridspec.GridSpec` subclass rather than `matplotlib.gridspec.GridSpec`, which
provides the following advantages:

* The `ultraplot.gridspec.GridSpec` subclass interprets spacing parameters
  with font size-relative units rather than figure size-relative units.
  This is more consistent with the tight layout `pad` arguments
  (which, like matplotlib, are specified in font size-relative units)
  and obviates the need to adjust spaces when the figure size or font size changes.
* The `ultraplot.gridspec.GridSpec` subclass permits variable spacing
  between rows and columns, and the tight layout algorithm takes
  this into account. Variable spacing is critical for making
  outer :ref:`colorbars and legends <ug_guides>` and
  :ref:`axes panels <ug_insets_panels>` without "stealing space"
  from the parent subplot -- these objects usually need to be
  spaced closer to their parents than other subplots.
* You can :ref:`override <ug_tight>` particular spacing parameters
  and leave the tight layout algorithm to adjust the
  unspecified spacing parameters. For example, passing ``right=1`` to
  :func:`~ultraplot.figure.Figure.add_subplots` fixes the right margin
  at 1 font size-width while the others are adjusted automatically.
* Only one `ultraplot.gridspec.GridSpec` is permitted per figure,
  considerably simplifying the tight layout algorithm calculations.
  This restriction is enforced by requiring successive
  :func:`~ultraplot.figure.Figure.add_subplot` calls to imply the same geometry and
  include only subplot specs generated from the same :class:`~ultraplot.gridspec.GridSpec`.

Links
-----

* For more on figure sizing, see :ref:`this page <ug_autosize>`.
* For more on subplot spacing, see :ref:`this page <ug_tight>`.

.. _why_redundant:

Working with multiple subplots
==============================

Limitation
----------

When working with multiple subplots in matplotlib, the path of least resistance
often leads to *redundant* figure elements. Namely...

* Repeated axis tick labels.
* Repeated axis labels.
* Repeated colorbars.
* Repeated legends.

These sorts of redundancies are very common even in publications, where they waste
valuable page space. It is also generally necessary to add "a-b-c" labels to
figures with multiple subplots before submitting them to publications, but
matplotlib has no built-in way of doing this.

Changes
-------

UltraPlot makes it easier to work with multiple subplots and create clear,
concise figures.

* Axis tick labels and axis labels are automatically
  :ref:`shared and aligned <ug_share>` between subplot in the same
  :class:`~ultraplot.gridspec.GridSpec` row or column. This is controlled by the `sharex`,
  `sharey`, `spanx`, `spany`, `alignx`, and `aligny` figure keywords.
* The figure `ultraplot.figure.Figure.colorbar` and :class:`ultraplot.figure.Figure.legend`
  commands can easily draw colorbars and legends intended to reference more than
  one subplot in arbitrary contiguous rows and columns. See the
  :ref:`next section <why_colorbars_legends>` for details.
* A-b-c labels can be added to subplots simply using the :rcraw:`abc`
  setting -- for example, ``uplt.rc['abc'] = 'A.'`` or ``axs.format(abc='A.')``.
  This is possible because :func:`~ultraplot.figure.Figure.add_subplot` assigns a unique
  :func:`~ultraplot.axes.Axes.number` to every new subplot.
* The `ultraplot.gridspec.SubplotGrid.format` command can easily format multiple subplots
  at once or add colorbars, legends, panels, twin axes, or inset axes to multiple
  subplots at once. A :class:`~ultraplot.gridspec.SubplotGrid` is returned by
  `ultraplot.figure.Figure.subplots`, and can be indexed like a list or a 2D array.
* The :func:`~ultraplot.axes.Axes.panel_axes` (shorthand :func:`~ultraplot.axes.Axes.panel`) commands
  draw :ref:`thin panels <ug_panels>` along the edges of subplots. This can be useful
  for plotting 1D summary statistics alongside 2D plots. You can also add twin axes and
  panel axes to several subplots at once using :class:`~ultraplot.gridspec.SubplotGrid` commands.

Links
-----

* For more on axis sharing, see :ref:`this page <ug_share>`.
* For more on panels, see :ref:`this page <ug_panels>`.
* For more on colorbars and legends, see :ref:`this page <ug_guides>`.
* For more on a-b-c labels, see :ref:`this page <ug_abc>`.
* For more on subplot grids,  see :ref:`this page <ug_subplotgrid>`.

.. _why_colorbars_legends:

Simpler colorbars and legends
=============================

Limitation
----------

In matplotlib, it can be difficult to draw `~matplotlib.figure.Figure.legend`\ s
along the outside of subplots. Generally, you need to position the legend
manually and tweak the spacing to make room for the legend.

Also, `~matplotlib.figure.Figure.colorbar`\ s drawn along the outside of subplots
with e.g. ``fig.colorbar(..., ax=ax)`` need to "steal" space from the parent subplot.
This can cause asymmetry in figures with more than one subplot. It is also generally
difficult to draw "inset" colorbars in matplotlib and to generate outer colorbars
with consistent widths (i.e., not too "skinny" or "fat").

Changes
-------

UltraPlot includes a simple framework for drawing colorbars and legends
that reference :ref:`individual subplots <ug_guides_loc>` and
:ref:`multiple contiguous subplots <ug_guides_multi>`.

* To draw a colorbar or legend on the outside of a specific subplot, pass an
  "outer" location (e.g. ``loc='l'`` or ``loc='left'``)
  to `ultraplot.axes.Axes.colorbar` or `ultraplot.axes.Axes.legend`.
* To draw a colorbar or legend on the inside of a specific subplot, pass an
  "inner" location (e.g. ``loc='ur'`` or ``loc='upper right'``)
  to `ultraplot.axes.Axes.colorbar` or `ultraplot.axes.Axes.legend`.
* To draw a colorbar or legend along the edge of the figure, use
  `ultraplot.figure.Figure.colorbar` and :class:`ultraplot.figure.Figure.legend`.
  The `col`, `row`, and `span` keywords control which
  :class:`~ultraplot.gridspec.GridSpec` rows and columns are spanned
  by the colorbar or legend.

Since :class:`~ultraplot.gridspec.GridSpec` permits variable spacing between subplot
rows and columns, "outer" colorbars and legends do not alter subplot
spacing or add whitespace. This is critical e.g. if you have a
colorbar between columns 1 and 2 but nothing between columns 2 and 3.
Also, :class:`~ultraplot.figure.Figure` and :class:`~ultraplot.axes.Axes` colorbar widths are
now specified in *physical* units rather than relative units, which makes
colorbar thickness independent of subplot size and easier to get just right.

Links
-----

* For more on single-subplot colorbars and legends,
  see :ref:`this page <ug_guides_loc>`.
* For more on multi-subplot colorbars and legends,
  see :ref:`this page <ug_guides_multi>`.
* For new colorbar features,
  see :ref:`this page <ug_colorbars>`.
* For new legend features,
  see :ref:`this page <ug_legends>`.

.. _why_plotting:

Improved plotting commands
==========================

Limitation
----------

A few common plotting tasks take a lot of work using matplotlib alone. The `seaborn`_,
`xarray`_, and `pandas`_ packages offer improvements, but it would be nice to
have this functionality built right into matplotlib's interface.

Changes
-------

UltraPlot uses the :class:`~ultraplot.axes.PlotAxes` subclass to add various `seaborn`_,
`xarray`_, and `pandas`_ features to existing matplotlib plotting commands
along with several additional features designed to make things easier.

The following features are relevant for "1D" :class:`~ultraplot.axes.PlotAxes` commands
like :func:`~ultraplot.axes.PlotAxes.line` (equivalent to :func:`~ultraplot.axes.PlotAxes.plot`)
and :func:`~ultraplot.axes.PlotAxes.scatter`:

* The treatment of data arguments passed to the 1D :class:`~ultraplot.axes.PlotAxes`
  commands is :ref:`standardized <ug_1dstd>`. This makes them more flexible
  and arguably more intuitive to use than their matplotlib counterparts.
* The `cycle` keyword is interpreted by the :class:`~ultraplot.constructor.Cycle`
  :ref:`constructor function <why_constructor>` and applies
  :ref:`property cyclers <ug_apply_cycle>` on-the-fly. This permits succinct
  and flexible property cycler declaration.
* The `legend` and `colorbar` keywords draw :ref:`on-the-fly legends and colorbars
  <ug_guides_plot>` using the result of the :class:`~ultraplot.axes.PlotAxes` command.
  Note that colorbars can be drawn from :ref:`lists of artists <ug_colorbars>`.
* The default `ylim` (`xlim`) in the presence of a fixed `xlim` (`ylim`) is now
  adjusted to exclude out-of-bounds data. This can be useful when "zooming in" on
  a dependent variable axis but can be disabled by setting :rcraw:`axes.inbounds`
  to ``False`` or passing ``inbounds=False`` to :class:`~ultraplot.axes.PlotAxes` commands.
* The :func:`~ultraplot.axes.PlotAxes.bar` and :func:`~ultraplot.axes.PlotAxes.barh` commands accept 2D
  arrays and can :ref:`stack or group <ug_bar>` successive columns. Likewise, the
  :func:`~ultraplot.axes.PlotAxes.area` and :func:`~ultraplot.axes.PlotAxes.areax` commands (shorthands
  for :func:`~ultraplot.axes.PlotAxes.fill_between` and :func:`~ultraplot.axes.PlotAxes.fill_betweenx`)
  accept 2D arrays and can :ref:`stack or overlay <ug_bar>` successive columns.
* The :func:`~ultraplot.axes.PlotAxes.bar`, :func:`~ultraplot.axes.PlotAxes.barh`,
  :func:`~ultraplot.axes.PlotAxes.vlines`, :func:`~ultraplot.axes.PlotAxes.hlines`,
  :func:`~ultraplot.axes.PlotAxes.area`, and :func:`~ultraplot.axes.PlotAxes.areax`
  commands accept a `negpos` keyword argument that :ref:`assigns different
  colors <ug_negpos>` to "negative" and "positive" regions.
* The :func:`~ultraplot.axes.PlotAxes.linex` and :func:`~ultraplot.axes.PlotAxes.scatterx` commands
  are just like :func:`~ultraplot.axes.PlotAxes.line` and :func:`~ultraplot.axes.PlotAxes.scatter`,
  but positional arguments are interpreted as *x* coordinates or (*y*, *x*) pairs.
  There are also the related commands :func:`~ultraplot.axes.PlotAxes.stemx`,
  :func:`~ultraplot.axes.PlotAxes.stepx`, :func:`~ultraplot.axes.PlotAxes.boxh` (shorthand for
  :func:`~ultraplot.axes.PlotAxes.boxploth`), and :func:`~ultraplot.axes.PlotAxes.violinh` (shorthand
  for :func:`~ultraplot.axes.PlotAxes.violinploth`).
* The :func:`~ultraplot.axes.PlotAxes.line`, :func:`~ultraplot.axes.PlotAxes.linex`,
  :func:`~ultraplot.axes.PlotAxes.scatter`, :func:`~ultraplot.axes.PlotAxes.scatterx`,
  :func:`~ultraplot.axes.PlotAxes.bar`, and :func:`~ultraplot.axes.PlotAxes.barh` commands can
  draw vertical or horizontal :ref:`error bars or "shading" <ug_errorbars>` using a
  variety of keyword arguments. This is often more convenient than working directly
  with `~matplotlib.axes.Axes.errorbar` or `~matplotlib.axes.Axes.fill_between`.
* The :func:`~ultraplot.axes.PlotAxes.parametric` command draws clean-looking
  :ref:`parametric lines <ug_parametric>` by encoding the parametric
  coordinate using colormap colors rather than text annotations.

The following features are relevant for "2D" :class:`~ultraplot.axes.PlotAxes` commands
like :func:`~ultraplot.axes.PlotAxes.pcolor` and :func:`~ultraplot.axes.PlotAxes.contour`:

* The treatment of data arguments passed to the 2D :class:`~ultraplot.axes.PlotAxes`
  commands is :ref:`standardized <ug_2dstd>`. This makes them more flexible
  and arguably more intuitive to use than their matplotlib counterparts.
* The `cmap` and `norm` :ref:`keyword arguments <ug_apply_cmap>` are interpreted
  by the :class:`~ultraplot.constructor.Colormap` and :class:`~ultraplot.constructor.Norm`
  :ref:`constructor functions <why_constructor>`. This permits succinct
  and flexible colormap and normalizer application.
* The `colorbar` keyword draws :ref:`on-the-fly colorbars <ug_guides_plot>` using the
  result of the plotting command. Note that :ref:`"inset" colorbars <ug_guides_loc>` can
  also be drawn, analogous to "inset" legends.
* The :func:`~ultraplot.axes.PlotAxes.contour`, :func:`~ultraplot.axes.PlotAxes.contourf`,
  :func:`~ultraplot.axes.PlotAxes.pcolormesh`, and :func:`~ultraplot.axes.PlotAxes.pcolor` commands
  all accept a `labels` keyword. This draws :ref:`contour and grid box labels
  <ug_labels>` on-the-fly. Labels are automatically colored black or white
  according to the luminance of the underlying grid box or filled contour.
* The default `vmin` and `vmax` used to normalize colormaps now excludes data
  outside the *x* and *y* axis bounds `xlim` and `ylim` if they were explicitly
  fixed. This can be disabled by setting :rcraw:`cmap.inbounds` to ``False``
  or by passing ``inbounds=False`` to :class:`~ultraplot.axes.PlotAxes` commands.
* The `~ultraplot.colors.DiscreteNorm` normalizer is paired with most colormaps by
  default. It can easily divide colormaps into distinct levels, similar to contour
  plots. This can be disabled by setting :rcraw:`cmap.discrete` to ``False`` or
  by passing ``discrete=False`` to :class:`~ultraplot.axes.PlotAxes` commands.
* The `~ultraplot.colors.DivergingNorm` normalizer is perfect for data with a
  :ref:`natural midpoint <ug_norm>` and offers both "fair" and "unfair" scaling.
  The `~ultraplot.colors.SegmentedNorm` normalizer can generate
  uneven color gradations useful for :ref:`unusual data distributions <ug_norm>`.
* The :func:`~ultraplot.axes.PlotAxes.heatmap` command invokes
  :func:`~ultraplot.axes.PlotAxes.pcolormesh` then applies an `equal axes apect ratio
  <https://matplotlib.org/stable/gallery/subplots_axes_and_figures/axis_equal_demo.html>`__,
  adds ticks to the center of each gridbox, and disables minor ticks and gridlines.
  This can be convenient for things like covariance matrices.
* Coordinate centers passed to commands like :func:`~ultraplot.axes.PlotAxes.pcolor` are
  automatically translated to "edges", and coordinate edges passed to commands like
  :func:`~ultraplot.axes.PlotAxes.contour` are automatically translated to "centers". In
  matplotlib, ``pcolor`` simply truncates and offsets the data when it receives centers.
* Commands like :func:`~ultraplot.axes.PlotAxes.pcolor`, :func:`~ultraplot.axes.PlotAxes.contourf`
  and :func:`~ultraplot.axes.Axes.colorbar` automatically fix an irritating issue where
  saved vector graphics appear to have thin white lines between `filled contours
  <https://stackoverflow.com/q/8263769/4970632>`__, `grid boxes
  <https://stackoverflow.com/q/27092991/4970632>`__, and `colorbar segments
  <https://stackoverflow.com/q/15003353/4970632>`__. This can be disabled by
  passing ``edgefix=False`` to :class:`~ultraplot.axes.PlotAxes` commands.

Links
-----

* For the 1D plotting features,
  see :ref:`this page <ug_1dplots>`.
* For the 2D plotting features,
  see :ref:`this page <ug_2dplots>`.
* For treatment of 1D data arguments,
  see :ref:`this page <ug_1dstd>`.
* For treatment of 2D data arguments,
  see :ref:`this page <ug_2dstd>`.

.. _why_cartopy_basemap:

Cartopy and basemap integration
===============================

Limitation
----------

There are two widely-used engines for working with geographic data in
matplotlib: `cartopy`_ and `basemap`_.  Using cartopy tends to be
verbose and involve boilerplate code, while using basemap requires plotting
with a separate `~mpl_toolkits.basemap.Basemap` object rather than the
:class:`~matplotlib.axes.Axes`. They both require separate import statements and extra
lines of code to configure the projection.

Furthermore, when you use `cartopy`_ and `basemap`_ plotting
commands, "map projection" coordinates are the default coordinate system
rather than longitude-latitude coordinates. This choice is confusing for
many users, since the vast majority of geophysical data are stored with
longitude-latitude (i.e., "Plate Carrée") coordinates.

Changes
-------

UltraPlot can succinctly create detailed geographic plots using either cartopy or
basemap as "backends". By default, cartopy is used, but basemap can be used by passing
``backend='basemap'`` to axes-creation commands or by setting :rcraw:`geo.backend` to
``'basemap'``. To create a geographic plot, simply pass the `PROJ <https://proj.org>`__
name to an axes-creation command, e.g. ``fig, ax = uplt.subplots(proj='pcarree')``
or ``fig.add_subplot(proj='pcarree')``. Alternatively, use the
:class:`~ultraplot.constructor.Proj` constructor function to quickly generate
a `cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap` instance.

Requesting geographic projections creates a `ultraplot.axes.GeoAxes`
with unified support for `cartopy`_ and `basemap`_ features via the
`ultraplot.axes.GeoAxes.format` command. This lets you quickly modify geographic
plot features like latitude and longitude gridlines, gridline labels, continents,
coastlines, and political boundaries. The syntax is conveniently analogous to the
syntax used for :func:`ultraplot.axes.CartesianAxes.format` and `ultraplot.axes.PolarAxes.format`.

The `~ultraplot.axes.GeoAxes` subclass also makes longitude-latitude coordinates
the "default" coordinate system by passing ``transform=ccrs.PlateCarree()``
or ``latlon=True`` to :class:`~ultraplot.axes.PlotAxes` commands (depending on whether cartopy
or basemap is the backend). And to enforce global coverage over the poles and across
longitude seams, you can pass ``globe=True`` to 2D :class:`~ultraplot.axes.PlotAxes` commands
like :func:`~ultraplot.axes.PlotAxes.contour` and :func:`~ultraplot.axes.PlotAxes.pcolormesh`.

Links
-----

* For an introduction,
  see :ref:`this page <ug_geo>`.
* For more on cartopy and basemap as backends,
  see :ref:`this page <ug_backends>`.
* For plotting in `~ultraplot.axes.GeoAxes`,
  see :ref:`this page <ug_geoplot>`.
* For formatting `~ultraplot.axes.GeoAxes`,
  see :ref:`this page <ug_geoformat>`.
* For changing the `~ultraplot.axes.GeoAxes` bounds,
  see :ref:`this page <ug_zoom>`.

.. _why_xarray_pandas:

Pandas and xarray integration
=============================

Limitation
----------

Scientific data is commonly stored in array-like containers
that include metadata -- namely, `xarray.DataArray`\ s, `pandas.DataFrame`\ s,
and `pandas.Series`. When matplotlib receives these objects, it ignores
the associated metadata. To create plots that are labeled with the metadata,
you must use the `xarray.DataArray.plot`, `pandas.DataFrame.plot`,
and `pandas.Series.plot` commands instead.

This approach is fine for quick plots, but not ideal for complex ones. It requires
learning a different syntax from matplotlib, and tends to encourage using the
`~matplotlib.pyplot` interface rather than the object-oriented interface. The
``plot`` commands also include features that would be useful additions to matplotlib
in their own right, without requiring special containers and a separate interface.

Changes
-------

UltraPlot reproduces many of the `xarray.DataArray.plot`,
`pandas.DataFrame.plot`, and `pandas.Series.plot`
features directly on the :class:`~ultraplot.axes.PlotAxes` commands.
This includes :ref:`grouped or stacked <ug_bar>` bar plots
and :ref:`layered or stacked <ug_bar>` area plots from two-dimensional
input data, auto-detection of :ref:`diverging datasets <ug_autonorm>` for
application of diverging colormaps and normalizers, and
:ref:`on-the-fly colorbars and legends <ug_guides_loc>` using `colorbar`
and `legend` keywords.

UltraPlot also handles metadata associated with `xarray.DataArray`, `pandas.DataFrame`,
`pandas.Series`, and `pint.Quantity` objects. When a plotting command receives these
objects, it updates the axis tick labels, axis labels, subplot title, and
colorbar and legend labels from the metadata. For `~pint.Quantity` arrays (including
`~pint.Quantity` those stored inside :class:`~xarray.DataArray` containers), a unit string
is generated from the `pint.Unit` according to the :rcraw:`unitformat` setting
(note UltraPlot also automatically calls `pint.UnitRegistry.setup_matplotlib`
whenever a `~pint.Quantity` is used for *x* and *y* coordinates and removes the
units from *z* coordinates to avoid the stripped-units warning message).
These features can be disabled by setting :rcraw:`autoformat` to ``False``
or passing ``autoformat=False`` to any plotting command.

Links
-----

* For integration with 1D :class:`~ultraplot.axes.PlotAxes` commands,
  see :ref:`this page <ug_1dintegration>`.
* For integration with 2D :class:`~ultraplot.axes.PlotAxes` commands,
  see :ref:`this page <ug_2dintegration>`.
* For bar and area plots,
  see :ref:`this page <ug_bar>`.
* For diverging datasets,
  see :ref:`this page <ug_autonorm>`.
* For on-the-fly colorbars and legends,
  see :ref:`this page <ug_guides_plot>`.

.. _why_aesthetics:

Aesthetic colors and fonts
==========================

Limitation
----------

A common problem with scientific visualizations is the use of "misleading"
colormaps like ``'jet'``. These colormaps have jarring jumps in
`hue, saturation, and luminance <rainbow_>`_ that can trick the human eye into seeing
non-existing patterns. It is important to use "perceptually uniform" colormaps
instead. Matplotlib comes packaged with `a few of its own <matplotlib_>`_, plus
the `ColorBrewer <brewer_>`_ colormap series, but external projects offer
a larger variety of aesthetically pleasing "perceptually uniform" colormaps
that would be nice to have in one place.

Matplotlib also "registers" the X11/CSS4 color names, but these are relatively
limited. The more numerous and arguably more intuitive `XKCD color survey <xkcd_>`_
names can only be accessed with the ``'xkcd:'`` prefix. As with colormaps, there
are also external projects with useful color names like `open color <opencolor_>`_.

Finally, matplotlib comes packaged with ``DejaVu Sans`` as the default font.
This font is open source and include glyphs for a huge variety of characters.
However in our opinion, it is not very aesthetically pleasing. It is also
difficult to switch to other fonts on limited systems or systems with fonts
stored in incompatible file formats (see :ref:`below <why_dotUltraPlot>`).

Changes
-------

UltraPlot adds new colormaps, colors, and fonts to help you make more
aesthetically pleasing figures.

* UltraPlot adds colormaps from the `seaborn <seacolor_>`_, `cmocean <cmocean_>`_,
  `SciVisColor <sciviscolor_>`_, and `Scientific Colour Maps <fabio_>`_ projects.
  It also defines a few default :ref:`perceptually uniform colormaps <ug_perceptual>`
  and includes a :class:`~ultraplot.colors.PerceptualColormap` class for generating
  new ones. A :ref:`table of colormap <ug_cmaps_included>` and
  :ref:`color cycles <ug_cycles_included>` can be shown using
  :func:`~ultraplot.demos.show_cmaps` and :func:`~ultraplot.demos.show_cycles`.
  Colormaps like ``'jet'`` can still be accessed, but this is discouraged.
* UltraPlot adds colors from the `open color <opencolor_>`_ project and adds
  `XKCD color survey <xkcd_>`_ names without the ``'xkcd:'`` prefix after
  *filtering* them to exclude perceptually-similar colors and *normalizing* the
  naming pattern to make them more self-consistent. Old X11/CSS4 colors can still be
  accessed, but this is discouraged. A :ref:`table of color names <ug_colors_included>`
  can be shown using :func:`~ultraplot.demos.show_colors`.
* UltraPlot comes packaged with several additional :ref:`sans-serif fonts
  <ug_fonts_included>` and the entire `TeX Gyre <texgyre_>`_ font series. TeX Gyre
  consists of open-source fonts designed to resemble more popular, commonly-used fonts
  like Helvetica and Century. They are used as the new default serif, sans-serif,
  monospace, cursive, and "fantasy" fonts, and they are available on all workstations.
  A :ref:`table of font names <ug_fonts_included>` can be shown
  using :func:`~ultraplot.demos.show_fonts`.

Links
-----

* For more on colormaps,
  see :ref:`this page <ug_cmaps>`.
* For more on color cycles,
  see :ref:`this page <ug_cycles>`.
* For more on fonts,
  see :ref:`this page <ug_fonts>`.
* For importing custom colormaps, colors, and fonts,
  see :ref:`this page <why_dotUltraPlot>`.

.. _why_colormaps_cycles:

Manipulating colormaps
======================

Limitation
----------

In matplotlib, colormaps are implemented with the
`~matplotlib.colors.LinearSegmentedColormap` class (representing "smooth"
color gradations) and the `~matplotlib.colors.ListedColormap` class (representing
"categorical" color sets). They are somewhat cumbersome to modify or create from
scratch. Meanwhile, property cycles used for individual plot elements are implemented
with the :class:`~cycler.Cycler` class. They are easier to modify but they cannot be
"registered" by name like colormaps.

The `seaborn`_ package includes "color palettes" to make working with colormaps
and property cycles easier, but it would be nice to have similar features
integrated more closely with matplotlib's colormap and property cycle constructs.

Changes
-------

UltraPlot tries to make it easy to manipulate colormaps and property cycles.

* All colormaps in UltraPlot are replaced with the :class:`~ultraplot.colors.ContinuousColormap`
  and :class:`~ultraplot.colors.DiscreteColormap` subclasses of
  `~matplotlib.colors.LinearSegmentedColormap` and `~matplotlib.colors.ListedColormap`.
  These classes include several useful features leveraged by the
  :ref:`constructor functions <why_constructor>`
  :class:`~ultraplot.constructor.Colormap` and :class:`~ultraplot.constructor.Cycle`.
* The :class:`~ultraplot.constructor.Colormap` function can merge, truncate, and
  modify existing colormaps or generate brand new colormaps. It can also
  create new :class:`~ultraplot.colors.PerceptualColormap`\ s -- a type of
  `ultraplot.colors.ContinuousColormap` with linear transitions in the
  :ref:`perceptually uniform-like <ug_perceptual>` hue, saturation,
  and luminance channels rather then the red, blue, and green channels.
* The :class:`~ultraplot.constructor.Cycle` function can make property cycles from
  scratch or retrieve "registered" color cycles from their associated
  :class:`~ultraplot.colors.DiscreteColormap` instances. It can also make property
  cycles by splitting up the colors from registered or on-the-fly
  :class:`~ultraplot.colors.ContinuousColormap`\ s and :class:`~ultraplot.colors.PerceptualColormap`\ s.

UltraPlot also makes all colormap and color cycle names case-insensitive, and
colormaps are automatically reversed or cyclically shifted 180 degrees if you
append ``'_r'`` or ``'_s'`` to any colormap name. These features are powered by
`~ultraplot.colors.ColormapDatabase`, which replaces matplotlib's native
colormap database.

Links
-----

* For making new colormaps,
  see :ref:`this page <ug_cmaps_new>`.
* For making new color cycles,
  see :ref:`this page <ug_cycles_new>`.
* For merging colormaps and cycles,
  see :ref:`this page <ug_cmaps_merge>`.
* For modifying colormaps and cycles,
  see :ref:`this page <ug_cmaps_mod>`.

.. _why_norm:

Physical units engine
=====================

Limitation
----------

Matplotlib uses figure-relative units for the margins `left`, `right`,
`bottom`, and `top`, and axes-relative units for the column and row spacing
`wspace` and `hspace`.  Relative units tend to require "tinkering" with
numbers until you find the right one. And since they are *relative*, if you
decide to change your figure size or add a subplot, they will have to be
readjusted.

Matplotlib also requires users to set the figure size `figsize` in inches.
This may be confusing for users outside of the United States.

Changes
-------

UltraPlot uses physical units for the :class:`~ultraplot.gridspec.GridSpec` keywords
`left`, `right`, `top`, `bottom`, `wspace`, `hspace`, `pad`, `outerpad`, and
`innerpad`. The default unit (assumed when a numeric argument is passed) is
`em-widths <https://en.wikipedia.org/wiki/Em_(typography)>`__. Em-widths are
particularly appropriate for this context, as plot text can be a useful "ruler"
when figuring out the amount of space you need. UltraPlot also permits arbitrary
string units for these keywords, for the :class:`~ultraplot.figure.Figure` keywords
`figsize`, `figwidth`, `figheight`, `refwidth`, and `refheight`, and in a
few other places. This is powered by the physical units engine :func:`~ultraplot.utils.units`.
Acceptable units include inches, centimeters, millimeters,
pixels, `points <https://en.wikipedia.org/wiki/Point_(typography)>`__, and `picas
<https://en.wikipedia.org/wiki/Pica_(typography)>`__ (a table of acceptable
units is found :ref:`here <units_table>`). Note the :func:`~ultraplot.utils.units` engine
also translates rc settings assigned to :func:`~ultraplot.config.rc_matplotlib` and
`~ultraplot.config.rc_UltraPlot`, e.g. :rcraw:`subplots.refwidth`,
:rcraw:`legend.columnspacing`, and :rcraw:`axes.labelpad`.

Links
-----

* For more on physical units,
  see :ref:`this page <ug_units>`.
* For more on :class:`~ultraplot.gridspec.GridSpec` spacing units,
  see :ref:`this page <ug_tight>`
* For more on colorbar width units,
  see :ref:`this page <ug_colorbars>`,
* For more on panel width units,
  see :ref:`this page <ug_panels>`,

.. _why_rc:

Flexible global settings
========================

Limitation
----------

In matplotlib, there are several `~matplotlib.rcParams` that would be
useful to set all at once, like spine and label colors. It might also
be useful to change these settings for individual subplots rather
than globally.

Changes
-------

In UltraPlot, you can use the :func:`~ultraplot.config.rc` object to change both native
matplotlib settings (found in :func:`~ultraplot.config.rc_matplotlib`) and added UltraPlot
settings (found in `~ultraplot.config.rc_UltraPlot`). Assigned settings are always
validated, and "meta" settings like ``meta.edgecolor``, ``meta.linewidth``, and
``font.smallsize`` can be used to update many settings all at once. Settings can
be changed with ``uplt.rc.key = value``, ``uplt.rc[key] = value``,
``uplt.rc.update(key=value)``, using `ultraplot.axes.Axes.format`, or using
`ultraplot.config.Configurator.context`. Settings that have changed during the
python session can be saved to a file with `ultraplot.config.Configurator.save`
(see :func:`~ultraplot.config.Configurator.changed`), and settings can be loaded from
files with `ultraplot.config.Configurator.load`.

Links
-----

* For an introduction,
  see :ref:`this page <ug_rc>`.
* For more on changing settings,
  see :ref:`this page <ug_config>`.
* For more on UltraPlot settings,
  see :ref:`this page <ug_rcUltraPlot>`.
* For more on meta settings,
  see :ref:`this page <ug_rcmeta>`.
* For a table of the new settings,
  see :ref:`this page <ug_rctable>`.

.. _why_dotUltraPlot:

Loading stuff
=============

Limitation
----------

Matplotlib `~matplotlib.rcParams` can be changed persistently by placing
`matplotlibrc :ref:`ug_mplrc` files in the same directory as your python script.
But it can be difficult to design and store your own colormaps and color cycles for
future use. It is also difficult to get matplotlib to use custom ``.ttf`` and
``.otf`` font files, which may be desirable when you are working on
Linux servers with limited font selections.

Changes
-------

UltraPlot settings can be changed persistently by editing the default ``ultraplotrc``
file in the location given by :func:`~ultraplot.config.Configurator.user_file` (this is
usually ``$HOME/.ultraplot/ultraplotrc``) or by adding loose ``ultraplotrc`` files to
either the current directory or an arbitrary parent directory. Adding files to
parent directories can be useful when working in projects with lots of subfolders.

UltraPlot also automatically registers colormaps, color cycles, colors, and font
files stored in subfolders named ``cmaps``,  ``cycles``, ``colors``, and ``fonts``
in the location given by :func:`~ultraplot.config.Configurator.user_folder` (this is usually
``$HOME/.ultraplot``), as well as loose subfolders named ``ultraplot_cmaps``,
``ultraplot_cycles``, ``ultraplot_colors``, and ``ultraplot_fonts`` in the current
directory or an arbitrary parent directory. You can save colormaps and color cycles to
:func:`~ultraplot.config.Configurator.user_folder` simply by passing ``save=True`` to
:class:`~ultraplot.constructor.Colormap` and :class:`~ultraplot.constructor.Cycle`. To re-register
these files during an active python session, or to register arbitrary input arguments,
you can use :func:`~ultraplot.config.register_cmaps`, :func:`~ultraplot.config.register_cycles`,
:func:`~ultraplot.config.register_colors`, or :func:`~ultraplot.config.register_fonts`.

Links
-----

* For the ``ultraplotrc`` file,
  see :ref:`this page <ug_ultraplotrc>`.
* For registering colormaps,
  see :ref:`this page <ug_cmaps_dl>`.
* For registering color cycles,
  see :ref:`this page <ug_cycles_dl>`.
* For registering colors,
  see :ref:`this page <ug_colors_user>`.
* For registering fonts,
  see :ref:`this page <ug_fonts_user>`.
