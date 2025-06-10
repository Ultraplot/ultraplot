#!/usr/bin/env python3
"""
The second-level axes subclass used for all ultraplot figures.
Implements plotting method overrides.
"""
import contextlib
import inspect
import itertools
import re
import sys
from numbers import Integral, Number

from typing import Any, Union, Iterable

from typing import Any, Union
from collections.abc import Callable
from collections.abc import Iterable

from ..utils import units
import matplotlib.artist as martist
import matplotlib.axes as maxes
import matplotlib.cbook as cbook
import matplotlib.cm as mcm
import matplotlib.collections as mcollections
import matplotlib.colors as mcolors
import matplotlib.contour as mcontour
import matplotlib.container as mcontainer
import matplotlib.image as mimage
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.pyplot as mplt
import matplotlib as mpl
from packaging import version
import numpy as np
import numpy.ma as ma

from .. import colors as pcolors
from .. import constructor, utils
from ..config import rc
from ..internals import ic  # noqa: F401
from ..internals import (
    _get_aliases,
    _not_none,
    _pop_kwargs,
    _pop_params,
    _pop_props,
    context,
    docstring,
    guides,
    inputs,
    warnings,
    _version_mpl,
)
from . import base

try:
    from cartopy.crs import PlateCarree
except ModuleNotFoundError:
    PlateCarree = object

__all__ = ["PlotAxes"]


# Constants
# NOTE: Increased from native linewidth of 0.25 matplotlib uses for grid box edges.
# This is half of rc['patch.linewidth'] of 0.6. Half seems like a nice default.
EDGEWIDTH = 0.3

# Data argument docstrings
_args_1d_docstring = """
*args : {y} or {x}, {y}
    The data passed as positional or keyword arguments. Interpreted as follows:

    * If only `{y}` coordinates are passed, try to infer the `{x}` coordinates
      from the `~pandas.Series` or :class:`~pandas.DataFrame` indices or the
      :class:`~xarray.DataArray` coordinates. Otherwise, the `{x}` coordinates
      are ``np.arange(0, {y}.shape[0])``.
    * If the `{y}` coordinates are a 2D array, plot each column of data in succession
      (except where each column of data represents a statistical distribution, as with
      ``boxplot``, ``violinplot``, or when using ``means=True`` or ``medians=True``).
    * If any arguments are `pint.Quantity`, auto-add the pint unit registry
      to matplotlib's unit registry using `~pint.UnitRegistry.setup_matplotlib`.
      A `pint.Quantity` embedded in an `xarray.DataArray` is also supported.
"""
_args_1d_multi_docstring = """
*args : {y}2 or {x}, {y}2, or {x}, {y}1, {y}2
    The data passed as positional or keyword arguments. Interpreted as follows:

    * If only `{y}` coordinates are passed, try to infer the `{x}` coordinates from
      the `~pandas.Series` or :class:`~pandas.DataFrame` indices or the :class:`~xarray.DataArray`
      coordinates. Otherwise, the `{x}` coordinates are ``np.arange(0, {y}2.shape[0])``.
    * If only `{x}` and `{y}2` coordinates are passed, set the `{y}1` coordinates
      to zero. This draws elements originating from the zero line.
    * If both `{y}1` and `{y}2` are provided, draw elements between these points. If
      either are 2D, draw elements by iterating over each column.
    * If any arguments are `pint.Quantity`, auto-add the pint unit registry
      to matplotlib's unit registry using `~pint.UnitRegistry.setup_matplotlib`.
      A `pint.Quantity` embedded in an `xarray.DataArray` is also supported.
"""
_args_2d_docstring = """
*args : {z} or x, y, {z}
    The data passed as positional or keyword arguments. Interpreted as follows:

    * If only {zvar} coordinates are passed, try to infer the `x` and `y` coordinates
      from the :class:`~pandas.DataFrame` indices and columns or the :class:`~xarray.DataArray`
      coordinates. Otherwise, the `y` coordinates are ``np.arange(0, y.shape[0])``
      and the `x` coordinates are ``np.arange(0, y.shape[1])``.
    * For ``pcolor`` and ``pcolormesh``, calculate coordinate *edges* using
      `~ultraplot.utils.edges` or `:func:`~ultraplot.utils.edges2d`` if *centers* were provided.
      For all other methods, calculate coordinate *centers* if *edges* were provided.
    * If the `x` or `y` coordinates are `pint.Quantity`, auto-add the pint unit registry
      to matplotlib's unit registry using `~pint.UnitRegistry.setup_matplotlib`. If the
      {zvar} coordinates are `pint.Quantity`, pass the magnitude to the plotting
      command. A `pint.Quantity` embedded in an `xarray.DataArray` is also supported.
"""
docstring._snippet_manager["plot.args_1d_y"] = _args_1d_docstring.format(x="x", y="y")
docstring._snippet_manager["plot.args_1d_x"] = _args_1d_docstring.format(x="y", y="x")
docstring._snippet_manager["plot.args_1d_multiy"] = _args_1d_multi_docstring.format(
    x="x", y="y"
)  # noqa: E501
docstring._snippet_manager["plot.args_1d_multix"] = _args_1d_multi_docstring.format(
    x="y", y="x"
)  # noqa: E501
docstring._snippet_manager["plot.args_2d"] = _args_2d_docstring.format(
    z="z", zvar="`z`"
)  # noqa: E501
docstring._snippet_manager["plot.args_2d_flow"] = _args_2d_docstring.format(
    z="u, v", zvar="`u` and `v`"
)  # noqa: E501


# Shared docstrings
_args_1d_shared_docstring = """
data : dict-like, optional
    A dict-like dataset container (e.g., :class:`~pandas.DataFrame` or
    `~xarray.Dataset`). If passed, each data argument can optionally
    be a string `key` and the arrays used for plotting are retrieved
    with ``data[key]``. This is a `native matplotlib feature
    <https://matplotlib.org/stable/gallery/misc/keyword_plotting.html>`__.
autoformat : bool, default: :rc:`autoformat`
    Whether the `x` axis labels, `y` axis labels, axis formatters, axes titles,
    legend titles, and colorbar labels are automatically configured when a
    `~pandas.Series`, :class:`~pandas.DataFrame`, :class:`~xarray.DataArray`, or `~pint.Quantity`
    is passed to the plotting command. Formatting of `pint.Quantity`
    unit strings is controlled by :rc:`unitformat`.
"""
_args_2d_shared_docstring = """
%(plot.args_1d_shared)s
transpose : bool, default: False
    Whether to transpose the input data. This should be used when
    passing datasets with column-major dimension order ``(x, y)``.
    Otherwise row-major dimension order ``(y, x)`` is expected.
order : {'C', 'F'}, default: 'C'
    Alternative to `transpose`. ``'C'`` corresponds to the default C-cyle
    row-major ordering (equivalent to ``transpose=False``). ``'F'`` corresponds
    to Fortran-style column-major ordering (equivalent to ``transpose=True``).
globe : bool, default: False
    For `ultraplot.axes.GeoAxes` only. Whether to enforce global
    coverage. When set to ``True`` this does the following:

    #. Interpolates input data to the North and South poles by setting the data
       values at the poles to the mean from latitudes nearest each pole.
    #. Makes meridional coverage "circular", i.e. the last longitude coordinate
       equals the first longitude coordinate plus 360\N{DEGREE SIGN}.
    #. When basemap is the backend, cycles 1D longitude vectors to fit within
       the map edges. For example, if the central longitude is 90\N{DEGREE SIGN},
       the data is shifted so that it spans -90\N{DEGREE SIGN} to 270\N{DEGREE SIGN}.
"""
docstring._snippet_manager["plot.args_1d_shared"] = _args_1d_shared_docstring
docstring._snippet_manager["plot.args_2d_shared"] = _args_2d_shared_docstring


# Auto colorbar and legend docstring
_guide_docstring = """
colorbar : bool, int, or str, optional
    If not ``None``, this is a location specifying where to draw an
    *inset* or *outer* colorbar from the resulting object(s). If ``True``,
    the default :rc:`colorbar.loc` is used. If the same location is
    used in successive plotting calls, object(s) will be added to the
    existing colorbar in that location (valid for colorbars built from lists
    of artists). Valid locations are shown in in `~ultraplot.axes.Axes.colorbar`.
colorbar_kw : dict-like, optional
    Extra keyword args for the call to `~ultraplot.axes.Axes.colorbar`.
legend : bool, int, or str, optional
    Location specifying where to draw an *inset* or *outer* legend from the
    resulting object(s). If ``True``, the default :rc:`legend.loc` is used.
    If the same location is used in successive plotting calls, object(s)
    will be added to existing legend in that location. Valid locations
    are shown in :class:`~ultraplot.axes.Axes.legend`.
legend_kw : dict-like, optional
    Extra keyword args for the call to :class:`~ultraplot.axes.Axes.legend`.
"""
docstring._snippet_manager["plot.guide"] = _guide_docstring


# Misc shared 1D plotting docstrings
_inbounds_docstring = """
inbounds : bool, default: :rc:`axes.inbounds`
    Whether to restrict the default `y` (`x`) axis limits to account for only
    in-bounds data when the `x` (`y`) axis limits have been locked.
    See also :rcraw:`axes.inbounds` and :rcraw:`cmap.inbounds`.
"""
_error_means_docstring = """
mean, means : bool, default: False
    Whether to plot the means of each column for 2D `{y}` coordinates. Means
    are calculated with `numpy.nanmean`. If no other arguments are specified,
    this also sets ``barstd=True`` (and ``boxstd=True`` for violin plots).
median, medians : bool, default: False
    Whether to plot the medians of each column for 2D `{y}` coordinates. Medians
    are calculated with `numpy.nanmedian`. If no other arguments arguments are
    specified, this also sets ``barstd=True`` (and ``boxstd=True`` for violin plots).
"""
_error_bars_docstring = """
bars : bool, default: None
    Shorthand for `barstd`, `barstds`.
barstd, barstds : bool, float, or 2-tuple of float, optional
    Valid only if `mean` or `median` is ``True``. Standard deviation multiples for
    *thin error bars* with optional whiskers (i.e., caps). If scalar, then +/- that
    multiple is used. If ``True``, the default standard deviation range of +/-3 is used.
barpctile, barpctiles : bool, float, or 2-tuple of float, optional
    Valid only if `mean` or `median` is ``True``. As with `barstd`, but instead
    using percentiles for the error bars. If scalar, that percentile range is
    used (e.g., ``90`` shows the 5th to 95th percentiles). If ``True``, the default
    percentile range of 0 to 100 is used.
bardata : array-like, optional
    Valid only if `mean` and `median` are ``False``. If shape is 2 x N, these
    are the lower and upper bounds for the thin error bars. If shape is N, these
    are the absolute, symmetric deviations from the central points.
boxes : bool, default: None
    Shorthand for `boxstd`, `boxstds`.
boxstd, boxstds, boxpctile, boxpctiles, boxdata : optional
    As with `barstd`, `barpctile`, and `bardata`, but for *thicker error bars*
    representing a smaller interval than the thin error bars. If `boxstds` is
    ``True``, the default standard deviation range of +/-1 is used. If `boxpctiles`
    is ``True``, the default percentile range of 25 to 75 is used (i.e., the
    interquartile range). When "boxes" and "bars" are combined, this has the
    effect of drawing miniature box-and-whisker plots.
capsize : float, default: :rc:`errorbar.capsize`
    The cap size for thin error bars in points.
barz, barzorder, boxz, boxzorder : float, default: 2.5
    The "zorder" for the thin and thick error bars.
barc, barcolor, boxc, boxcolor \
: color-spec, default: :rc:`boxplot.whiskerprops.color`
    Colors for the thin and thick error bars.
barlw, barlinewidth, boxlw, boxlinewidth \
: float, default: :rc:`boxplot.whiskerprops.linewidth`
    Line widths for the thin and thick error bars, in points. The default for boxes
    is 4 times :rcraw:`boxplot.whiskerprops.linewidth`.
boxm, boxmarker : bool or marker-spec, default: 'o'
    Whether to draw a small marker in the middle of the box denoting
    the mean or median position. Ignored if `boxes` is ``False``.
boxms, boxmarkersize : size-spec, default: ``(2 * boxlinewidth) ** 2``
    The marker size for the `boxmarker` marker in points ** 2.
boxmc, boxmarkercolor, boxmec, boxmarkeredgecolor : color-spec, default: 'w'
    Color, face color, and edge color for the `boxmarker` marker.
"""
_error_shading_docstring = """
shade : bool, default: None
    Shorthand for `shadestd`.
shadestd, shadestds, shadepctile, shadepctiles, shadedata : optional
    As with `barstd`, `barpctile`, and `bardata`, but using *shading* to indicate
    the error range. If `shadestds` is ``True``, the default standard deviation
    range of +/-2 is used. If `shadepctiles` is ``True``, the default
    percentile range of 10 to 90 is used.
fade : bool, default: None
    Shorthand for `fadestd`.
fadestd, fadestds, fadepctile, fadepctiles, fadedata : optional
    As with `shadestd`, `shadepctile`, and `shadedata`, but for an additional,
    more faded, *secondary* shaded region. If `fadestds` is ``True``, the default
    standard deviation range of +/-3 is used. If `fadepctiles` is ``True``,
    the default percentile range of 0 to 100 is used.
shadec, shadecolor, fadec, fadecolor : color-spec, default: None
    Colors for the different shaded regions. The parent artist color is used by default.
shadez, shadezorder, fadez, fadezorder : float, default: 1.5
    The "zorder" for the different shaded regions.
shadea, shadealpha, fadea, fadealpha : float, default: 0.4, 0.2
    The opacity for the different shaded regions.
shadelw, shadelinewidth, fadelw, fadelinewidth : float, default: :rc:`patch.linewidth`.
    The edge line width for the shading patches.
shdeec, shadeedgecolor, fadeec, fadeedgecolor : float, default: 'none'
    The edge color for the shading patches.
shadelabel, fadelabel : bool or str, optional
    Labels for the shaded regions to be used as separate legend entries. To toggle
    labels "on" and apply a *default* label, use e.g. ``shadelabel=True``. To apply
    a *custom* label, use e.g. ``shadelabel='label'``. Otherwise, the shading is
    drawn underneath the line and/or marker in the legend entry.
"""
docstring._snippet_manager["plot.inbounds"] = _inbounds_docstring
docstring._snippet_manager["plot.error_means_y"] = _error_means_docstring.format(y="y")
docstring._snippet_manager["plot.error_means_x"] = _error_means_docstring.format(y="x")
docstring._snippet_manager["plot.error_bars"] = _error_bars_docstring
docstring._snippet_manager["plot.error_shading"] = _error_shading_docstring


# Color docstrings
_cycle_docstring = """
cycle : cycle-spec, optional
    The cycle specifer, passed to the `~ultraplot.constructor.Cycle` constructor.
    If the returned cycler is unchanged from the current cycler, the axes
    cycler will not be reset to its first position. To disable property cycling
    and just use black for the default color, use ``cycle=False``, ``cycle='none'``,
    or ``cycle=()`` (analogous to disabling ticks with e.g. ``xformatter='none'``).
    To restore the default property cycler, use ``cycle=True``.
cycle_kw : dict-like, optional
    Passed to `~ultraplot.constructor.Cycle`.
"""
_cmap_norm_docstring = """
cmap : colormap-spec, default: \
:rc:`cmap.sequential` or :rc:`cmap.diverging`
    The colormap specifer, passed to the :class:`~ultraplot.constructor.Colormap` constructor
    function. If :rcraw:`cmap.autodiverging` is ``True`` and the normalization
    range contains negative and positive values then :rcraw:`cmap.diverging` is used.
    Otherwise :rcraw:`cmap.sequential` is used.
cmap_kw : dict-like, optional
    Passed to :class:`~ultraplot.constructor.Colormap`.
c, color, colors : color-spec or sequence of color-spec, optional
    The color(s) used to create a :class:`~ultraplot.colors.DiscreteColormap`.
    If not passed, `cmap` is used.
norm : norm-spec, default: \
`~matplotlib.colors.Normalize` or `~ultraplot.colors.DivergingNorm`
    The data value normalizer, passed to the `~ultraplot.constructor.Norm`
    constructor function. If `discrete` is ``True`` then 1) this affects the default
    level-generation algorithm (e.g. ``norm='log'`` builds levels in log-space) and
    2) this is passed to `~ultraplot.colors.DiscreteNorm` to scale the colors before they
    are discretized (if `norm` is not already a `~ultraplot.colors.DiscreteNorm`).
    If :rcraw:`cmap.autodiverging` is ``True`` and the normalization range contains
    negative and positive values then `~ultraplot.colors.DivergingNorm` is used.
    Otherwise `~matplotlib.colors.Normalize` is used.
norm_kw : dict-like, optional
    Passed to `~ultraplot.constructor.Norm`.
extend : {'neither', 'both', 'min', 'max'}, default: 'neither'
    Direction for drawing colorbar "extensions" indicating
    out-of-bounds data on the end of the colorbar.
discrete : bool, default: :rc:`cmap.discrete`
    If ``False``, then `~ultraplot.colors.DiscreteNorm` is not applied to the
    colormap. Instead, for non-contour plots, the number of levels will be
    roughly controlled by :rcraw:`cmap.lut`. This has a similar effect to
    using `levels=large_number` but it may improve rendering speed. Default is
    ``True`` only for contouring commands like `~ultraplot.axes.Axes.contourf`
    and pseudocolor commands like `~ultraplot.axes.Axes.pcolor`.
sequential, diverging, cyclic, qualitative : bool, default: None
    Boolean arguments used if `cmap` is not passed. Set these to ``True``
    to use the default :rcraw:`cmap.sequential`, :rcraw:`cmap.diverging`,
    :rcraw:`cmap.cyclic`, and :rcraw:`cmap.qualitative` colormaps.
    The `diverging` option also applies `~ultraplot.colors.DivergingNorm`
    as the default continuous normalizer.
"""
docstring._snippet_manager["plot.cycle"] = _cycle_docstring
docstring._snippet_manager["plot.cmap_norm"] = _cmap_norm_docstring

_log_doc = """
Plot {kind}

UltraPlot is optimized for visualizing logarithmic scales by default. For cases with large differences in magnitude,
we recommend setting `rc["formatter.log"] = True` to enhance axis label formatting.
{matplotlib_doc}
"""

docstring._snippet_manager["plot.loglog"] = _log_doc.format(
    kind="loglog", matplotlib_doc=mplt.loglog.__doc__
)

docstring._snippet_manager["plot.semilogy"] = _log_doc.format(
    kind="semilogy", matplotlib_doc=mplt.semilogy.__doc__
)

docstring._snippet_manager["plot.semilogx"] = _log_doc.format(
    kind="semilogx", matplotlib_doc=mplt.semilogx.__doc__
)

# Levels docstrings
# NOTE: In some functions we only need some components
_vmin_vmax_docstring = """
vmin, vmax : float, optional
    The minimum and maximum color scale values used with the `norm` normalizer.
    If `discrete` is ``False`` these are the absolute limits, and if `discrete`
    is ``True`` these are the approximate limits used to automatically determine
    `levels` or `values` lists at "nice" intervals. If `levels` or `values` were
    already passed as lists, these are ignored, and `vmin` and `vmax` are set to
    the minimum and maximum of the lists. If `robust` was passed, the default `vmin`
    and `vmax` are some percentile range of the data values. Otherwise, the default
    `vmin` and `vmax` are the minimum and maximum of the data values.
"""
_manual_levels_docstring = """
N
    Shorthand for `levels`.
levels : int or sequence of float, default: :rc:`cmap.levels`
    The number of level edges or a sequence of level edges. If the former, `locator`
    is used to generate this many level edges at "nice" intervals. If the latter,
    the levels should be monotonically increasing or decreasing (note decreasing
    levels fail with ``contour`` plots).
values : int or sequence of float, default: None
    The number of level centers or a sequence of level centers. If the former,
    `locator` is used to generate this many level centers at "nice" intervals.
    If the latter, levels are inferred using `~ultraplot.utils.edges`.
    This will override any `levels` input.
center_levels : bool, default False
    If set to true, the discrete color bar bins will be centered on the level values
    instead of using the level values as the edges of the discrete bins. This option
    can be used for diverging, discrete color bars with both positive and negative
    data to ensure data near zero is properly represented.
"""
_auto_levels_docstring = """
robust : bool, float, or 2-tuple, default: :rc:`cmap.robust`
    If ``True`` and `vmin` or `vmax` were not provided, they are
    determined from the 2nd and 98th data percentiles rather than the
    minimum and maximum. If float, this percentile range is used (for example,
    ``90`` corresponds to the 5th to 95th percentiles). If 2-tuple of float,
    these specific percentiles should be used. This feature is useful
    when your data has large outliers.
inbounds : bool, default: :rc:`cmap.inbounds`
    If ``True`` and `vmin` or `vmax` were not provided, when axis limits
    have been explicitly restricted with :func:`~matplotlib.axes.Axes.set_xlim`
    or :func:`~matplotlib.axes.Axes.set_ylim`, out-of-bounds data is ignored.
    See also :rcraw:`cmap.inbounds` and :rcraw:`axes.inbounds`.
locator : locator-spec, default: `matplotlib.ticker.MaxNLocator`
    The locator used to determine level locations if `levels` or `values` were not
    already passed as lists. Passed to the `~ultraplot.constructor.Locator` constructor.
    Default is `~matplotlib.ticker.MaxNLocator` with `levels` integer levels.
locator_kw : dict-like, optional
    Keyword arguments passed to `matplotlib.ticker.Locator` class.
symmetric : bool, default: False
    If ``True``, the normalization range or discrete colormap levels are
    symmetric about zero.
positive : bool, default: False
    If ``True``, the normalization range or discrete colormap levels are
    positive with a minimum at zero.
negative : bool, default: False
    If ``True``, the normaliation range or discrete colormap levels are
    negative with a minimum at zero.
nozero : bool, default: False
    If ``True``, ``0`` is removed from the level list. This is mainly useful for
    single-color `~matplotlib.axes.Axes.contour` plots.
"""
docstring._snippet_manager["plot.vmin_vmax"] = _vmin_vmax_docstring
docstring._snippet_manager["plot.levels_manual"] = _manual_levels_docstring
docstring._snippet_manager["plot.levels_auto"] = _auto_levels_docstring


# Labels docstrings
_label_docstring = """
label, value : float or str, optional
    The single legend label or colorbar coordinate to be used for
    this plotted element. Can be numeric or string. This is generally
    used with 1D positional arguments.
"""
_labels_1d_docstring = """
%(plot.label)s
labels, values : sequence of float or sequence of str, optional
    The legend labels or colorbar coordinates used for each plotted element.
    Can be numeric or string, and must match the number of plotted elements.
    This is generally used with 2D positional arguments.
"""
_labels_2d_docstring = """
label : str, optional
    The legend label to be used for this object. In the case of
    contours, this is paired with the the central artist in the artist
    list returned by `matplotlib.contour.ContourSet.legend_elements`.
labels : bool, optional
    Whether to apply labels to contours and grid boxes. The text will be
    white when the luminance of the underlying filled contour or grid box
    is less than 50 and black otherwise.
labels_kw : dict-like, optional
    Ignored if `labels` is ``False``. Extra keyword args for the labels.
    For contour plots, this is passed to `~matplotlib.axes.Axes.clabel`.
    Otherwise, this is passed to `~matplotlib.axes.Axes.text`.
formatter, fmt : formatter-spec, optional
    The `~matplotlib.ticker.Formatter` used to format number labels.
    Passed to the `~ultraplot.constructor.Formatter` constructor.
formatter_kw : dict-like, optional
    Keyword arguments passed to `matplotlib.ticker.Formatter` class.
precision : int, optional
    The maximum number of decimal places for number labels generated
    with the default formatter `~ultraplot.ticker.Simpleformatter`.
"""
docstring._snippet_manager["plot.label"] = _label_docstring
docstring._snippet_manager["plot.labels_1d"] = _labels_1d_docstring
docstring._snippet_manager["plot.labels_2d"] = _labels_2d_docstring


# Negative-positive colors
_negpos_docstring = """
negpos : bool, default: False
    Whether to shade {objects} where ``{pos}`` with `poscolor`
    and where ``{neg}`` with `negcolor`. If ``True`` this
    function will return a length-2 silent list of handles.
negcolor, poscolor : color-spec, default: :rc:`negcolor`, :rc:`poscolor`
    Colors to use for the negative and positive {objects}. Ignored if
    `negpos` is ``False``.
"""
docstring._snippet_manager["plot.negpos_fill"] = _negpos_docstring.format(
    objects="patches", neg="y2 < y1", pos="y2 >= y1"
)
docstring._snippet_manager["plot.negpos_lines"] = _negpos_docstring.format(
    objects="lines", neg="ymax < ymin", pos="ymax >= ymin"
)
docstring._snippet_manager["plot.negpos_bar"] = _negpos_docstring.format(
    objects="bars", neg="height < 0", pos="height >= 0"
)


# Plot docstring
_plot_docstring = """
Plot standard lines.

Parameters
----------
%(plot.args_1d_{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.line)s
%(plot.error_means_{y})s
%(plot.error_bars)s
%(plot.error_shading)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to :func:`~matplotlib.axes.Axes.plot`.

See also
--------
PlotAxes.plot
PlotAxes.plotx
matplotlib.axes.Axes.plot
"""
docstring._snippet_manager["plot.plot"] = _plot_docstring.format(y="y")
docstring._snippet_manager["plot.plotx"] = _plot_docstring.format(y="x")


# Step docstring
# NOTE: Internally matplotlib implements step with thin wrapper of plot
_step_docstring = """
Plot step lines.

Parameters
----------
%(plot.args_1d_{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.line)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.step`.

See also
--------
PlotAxes.step
PlotAxes.stepx
matplotlib.axes.Axes.step
"""
docstring._snippet_manager["plot.step"] = _step_docstring.format(y="y")
docstring._snippet_manager["plot.stepx"] = _step_docstring.format(y="x")


# Stem docstring
_stem_docstring = """
Plot stem lines.

Parameters
----------
%(plot.args_1d_{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(plot.inbounds)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.stem`.
"""
docstring._snippet_manager["plot.stem"] = _stem_docstring.format(y="x")
docstring._snippet_manager["plot.stemx"] = _stem_docstring.format(y="x")


# Lines docstrings
_lines_docstring = """
Plot {orientation} lines.

Parameters
----------
%(plot.args_1d_multi{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
stack, stacked : bool, default: False
    Whether to "stack" lines from successive columns of {y} data
    or plot lines on top of each other.
%(plot.cycle)s
%(artist.line)s
%(plot.negpos_lines)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.{prefix}lines`.

See also
--------
PlotAxes.vlines
PlotAxes.hlines
matplotlib.axes.Axes.vlines
matplotlib.axes.Axes.hlines
"""
docstring._snippet_manager["plot.vlines"] = _lines_docstring.format(
    y="y", prefix="v", orientation="vertical"
)
docstring._snippet_manager["plot.hlines"] = _lines_docstring.format(
    y="x", prefix="h", orientation="horizontal"
)


# Scatter docstring
_parametric_docstring = """
Plot a parametric line.

Parameters
----------
%(plot.args_1d_y)s
c, color, colors, values, labels : sequence of float, str, or color-spec, optional
    The parametric coordinate(s). These can be passed as a third positional
    argument or as a keyword argument. If they are float, the colors will be
    determined from `norm` and `cmap`. If they are strings, the color values
    will be ``np.arange(len(colors))`` and eventual colorbar ticks will
    be labeled with the strings. If they are colors, they are used for the
    line segments and `cmap` is ignored -- for example, ``colors='blue'``
    makes a monochromatic "parametric" line.
interp : int, default: 0
    Interpolate to this many additional points between the parametric
    coordinates. This can be increased to make the color gradations
    between a small number of coordinates appear "smooth".
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.inbounds)s
scalex, scaley : bool, optional
    Whether the view limits are adapted to the data limits. The values are
    passed on to `~matplotlib.axes.Axes.autoscale_view`.
%(plot.label)s
%(plot.guide)s
**kwargs
    Valid :class:`~matplotlib.collections.LineCollection` properties.

Returns
-------
:class:`~matplotlib.collections.LineCollection`
    The parametric line. See `this matplotlib example \
<https://matplotlib.org/stable/gallery/lines_bars_and_markers/multicolored_line>`__.

See also
--------
PlotAxes.plot
PlotAxes.plotx
matplotlib.collections.LineCollection
"""
docstring._snippet_manager["plot.parametric"] = _parametric_docstring


# Scatter function docstring
_scatter_docstring = """
Plot markers with flexible keyword arguments.

Parameters
----------
%(plot.args_1d_{y})s
s, size, ms, markersize : float or array-like or unit-spec, optional
    The marker size area(s). If this is an array matching the shape of `x` and `y`,
    the units are scaled by `smin` and `smax`. If this contains unit string(s), it
    is processed by `~ultraplot.utils.units` and represents the width rather than area.
c, color, colors, mc, markercolor, markercolors, fc, facecolor, facecolors \
: array-like or color-spec, optional
    The marker color(s). If this is an array matching the shape of `x` and `y`,
    the colors are generated using `cmap`, `norm`, `vmin`, and `vmax`. Otherwise,
    this should be a valid matplotlib color.
smin, smax : float, optional
    The minimum and maximum marker size area in units ``points ** 2``. Ignored
    if `absolute_size` is ``True``. Default value for `smin` is ``1`` and for
    `smax` is the square of :rc:`lines.markersize`.
area_size : bool, default: True
    Whether the marker sizes `s` are scaled by area or by radius. The default
    ``True`` is consistent with matplotlib. When `absolute_size` is ``True``,
    the `s` units are ``points ** 2`` if `area_size` is ``True`` and ``points``
    if `area_size` is ``False``.
absolute_size : bool, default: True or False
    Whether `s` should be taken to represent "absolute" marker sizes in units
    ``points`` or ``points ** 2`` or "relative" marker sizes scaled by `smin`
    and `smax`. Default is ``True`` if `s` is scalar and ``False`` if `s` is
    array-like or `smin` or `smax` were passed.
%(plot.vmin_vmax)s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(plot.cycle)s
lw, linewidth, linewidths, mew, markeredgewidth, markeredgewidths \
: float or sequence, optional
    The marker edge width(s).
edgecolors, markeredgecolor, markeredgecolors \
: color-spec or sequence, optional
    The marker edge color(s).
%(plot.error_means_{y})s
%(plot.error_bars)s
%(plot.error_shading)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.scatter`.

See also
--------
PlotAxes.scatter
PlotAxes.scatterx
matplotlib.axes.Axes.scatter
"""
docstring._snippet_manager["plot.scatter"] = _scatter_docstring.format(y="y")
docstring._snippet_manager["plot.scatterx"] = _scatter_docstring.format(y="x")

_beeswarm_docstring = """
Beeswarm plot with `SHAP-style <https://shap.readthedocs.io/en/latest/generated/shap.plots.beeswarm.html#shap.plots.beeswarm>`_ feature value coloring.

%(plot.scatter)s
color_values : array-like, optional
    Values to use for coloring points. Should match the shape of the data.
    Enables SHAP-style feature value coloring.
color_by_feature : array-like, optional
    Alias for color_values. Values to color points by (e.g., feature values).
n_iter: int, default: 50
    Number of iterations for the beeswarm algorithm. More iterations can lead long time to plot but better point separation.
"""
docstring._snippet_manager["plot.beeswarm"] = _scatter_docstring.format(y="y")

# Bar function docstring
_bar_docstring = """
Plot individual, grouped, or stacked bars.

Parameters
----------
%(plot.args_1d_{y})s
width : float or array-like, default: 0.8
    The width(s) of the bars. Can be passed as a third positional argument. If
    `absolute_width` is ``True`` (the default) these are in units relative to the
    {x} coordinate step size. Otherwise these are in {x} coordinate units.
{bottom} : float or array-like, default: 0
    The coordinate(s) of the {bottom} edge of the bars.
    Can be passed as a fourth positional argument.
absolute_width : bool, default: False
    Whether to make the `width` units *absolute*. If ``True``,
    this restores the default matplotlib behavior.
stack, stacked : bool, default: False
    Whether to "stack" bars from successive columns of {y}
    data or plot bars side-by-side in groups.
bar_labels : bool, default rc["bar.bar_labels"]
    Whether to show the height values for vertical bars or width values for horizontal bars.
bar_labels_kw : dict, default None
    Keywords to format the bar_labels, see :func:`~matplotlib.pyplot.bar_label`.
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.patch)s
%(plot.negpos_bar)s
%(axes.edgefix)s
%(plot.error_means_{y})s
%(plot.error_bars)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.bar{suffix}`.

See also
--------
PlotAxes.bar
PlotAxes.barh
matplotlib.axes.Axes.bar
matplotlib.axes.Axes.barh
"""
docstring._snippet_manager["plot.bar"] = _bar_docstring.format(
    x="x", y="y", bottom="bottom", suffix=""
)
docstring._snippet_manager["plot.barh"] = _bar_docstring.format(
    x="y", y="x", bottom="left", suffix="h"
)


_lollipop_docstring = """
Plot individual or group lollipop graphs.

A lollipop graph is a bar graph with the bars replaced by dots connected to the {which}-axis by lines.

Inputs such as arrays (`x` or `y`) or dataframes (`pandas` or `xarray`) are passed through :func:`~ultraplot.PlotAxes.bar`. Colors are inferred from the bar objects and parsed automatically. Formatting of the lollipop consists of controlling the `stem` and the `marker`. The stem properties can be set for the width, size, or color. Marker formatting follows the same inputs to :func:`~ultraplot.PlotAxes.scatter`.

Parameters
----------
%(plot.args_1d_{which})s
stemlinewdith: str, default `rc["lollipop.stemlinewidth"]`
stemcolor: str, default `rc["lollipop.stemcolor"]`
    Line color of the lines connecting the dots to the {which}-axis. Defaults to `rc["lollipop.linecolor"]`.
stemlinestyle: str, default: `rc["lollipop.stemlinestyle"]`
    The style of the lines connecting the dots to the {which}-axis. Defaults to `rc["lollipop.linestyle"]`.
s, size, ms, markersize : float or array-like or unit-spec, optional
    The marker size area(s). If this is an array matching the shape of `x` and `y`,
    the units are scaled by `smin` and `smax`. If this contains unit string(s), it
    is processed by `~ultraplot.utils.units` and represents the width rather than area.
c, color, colors, mc, markercolor, markercolors, fc, facecolor, facecolors \
: array-like or color-spec, optional
    The marker color(s). If this is an array matching the shape of `x` and `y`,
    the colors are generated using `cmap`, `norm`, `vmin`, and `vmax`. Otherwise,
    this should be a valid matplotlib color.
smin, smax : float, optional
    The minimum and maximum marker size area in units ``points ** 2``. Ignored
    if `absolute_size` is ``True``. Default value for `smin` is ``1`` and for
    `smax` is the square of :rc:`lines.markersize`.
area_size : bool, default: True
    Whether the marker sizes `s` are scaled by area or by radius. The default
    ``True`` is consistent with matplotlib. When `absolute_size` is ``True``,
    the `s` units are ``points ** 2`` if `area_size` is ``True`` and ``points``
    if `area_size` is ``False``.
absolute_size : bool, default: True or False
    Whether `s` should be taken to represent "absolute" marker sizes in units
    ``points`` or ``points ** 2`` or "relative" marker sizes scaled by `smin`
    and `smax`. Default is ``True`` if `s` is scalar and ``False`` if `s` is
    array-like or `smin` or `smax` were passed.
%(plot.vmin_vmax)s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(plot.cycle)s
lw, linewidth, linewidths, mew, markeredgewidth, markeredgewidths \
: float or sequence, optional
    The marker edge width(s).
edgecolors, markeredgecolor, markeredgecolors \
: color-spec or sequence, optional
    The marker edge color(s).
%(plot.error_means_{which})s
%(plot.error_bars)s
%(plot.error_shading)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.scatter`.

See for more info on the grouping behavior :func:`~ultraplot.PlotAxes.bar`, and for formatting :func:~ultraplot.PlotAxes.scatter`.
Returns
-------
List of ~matplotlib.collections.PatchCollection, and a ~matplotlib.collections.LineCollection
"""
docstring._snippet_manager["plot.lollipop"] = _lollipop_docstring.format(which="x")
docstring._snippet_manager["plot.lollipoph"] = _lollipop_docstring.format(which="y")


# Area plot docstring
_fill_docstring = """
Plot individual, grouped, or overlaid shading patches.

Parameters
----------
%(plot.args_1d_multi{y})s
stack, stacked : bool, default: False
    Whether to "stack" area patches from successive columns of {y}
    data or plot area patches on top of each other.
%(plot.args_1d_shared)s

Other parameters
----------------
where : ndarray, optional
    A boolean mask for the points that should be shaded.
    See `this matplotlib example \
<https://matplotlib.org/stable/gallery/pyplots/whats_new_98_4_fill_between.html>`__.
%(plot.cycle)s
%(artist.patch)s
%(plot.negpos_fill)s
%(axes.edgefix)s
%(plot.inbounds)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.fill_between{suffix}`.

See also
--------
PlotAxes.area
PlotAxes.areax
PlotAxes.fill_between
PlotAxes.fill_betweenx
matplotlib.axes.Axes.fill_between
matplotlib.axes.Axes.fill_betweenx
"""
docstring._snippet_manager["plot.fill_between"] = _fill_docstring.format(
    x="x", y="y", suffix=""
)
docstring._snippet_manager["plot.fill_betweenx"] = _fill_docstring.format(
    x="y", y="x", suffix="x"
)


# Box plot docstrings
_boxplot_docstring = """
Plot {orientation} boxes and whiskers with a nice default style.

Parameters
----------
%(plot.args_1d_{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
fill : bool, default: True
    Whether to fill the box with a color.
mean, means : bool, default: False
    If ``True``, this passes ``showmeans=True`` and ``meanline=True`` to
    `matplotlib.axes.Axes.boxplot`. Adds mean lines alongside the median.
%(plot.cycle)s
%(artist.patch_black)s
m, marker, ms, markersize : float or str, optional
    Marker style and size for the 'fliers', i.e. outliers. See the
    ``boxplot.flierprops`` `~matplotlib.rcParams` settings.
meanls, medianls, meanlinestyle, medianlinestyle, meanlinestyles, medianlinestyles \
: str, optional
    Line style for the mean and median lines drawn across the box.
    See the ``boxplot.meanprops`` and ``boxplot.medianprops``
    `~matplotlib.rcParams` settings.
boxc, capc, whiskerc, flierc, meanc, medianc, \
boxcolor, capcolor, whiskercolor, fliercolor, meancolor, mediancolor \
boxcolors, capcolors, whiskercolors, fliercolors, meancolors, mediancolors \
: color-spec or sequence, optional
    Color of various boxplot components. If a sequence, should be the same length as
    the number of boxes. These are shorthands so you don't have to pass e.g. a
    `boxprops` dictionary keyword. See the ``boxplot.boxprops``, ``boxplot.capprops``,
    ``boxplot.whiskerprops``, ``boxplot.flierprops``, ``boxplot.meanprops``, and
    ``boxplot.medianprops`` `~matplotlib.rcParams` settings.
boxlw, caplw, whiskerlw, flierlw, meanlw, medianlw, boxlinewidth, caplinewidth, \
meanlinewidth, medianlinewidth, whiskerlinewidth, flierlinewidth, boxlinewidths, \
caplinewidths, meanlinewidths, medianlinewidths, whiskerlinewidths, flierlinewidths \
: float, optional
    Line width of various boxplot components. These are shorthands so
    you don't have to pass e.g. a `boxprops` dictionary keyword.
    See the ``boxplot.boxprops``, ``boxplot.capprops``, ``boxplot.whiskerprops``,
    ``boxplot.flierprops``, ``boxplot.meanprops``, and ``boxplot.medianprops``
    `~matplotlib.rcParams` settings.
%(plot.labels_1d)s
**kwargs
    Passed to `matplotlib.axes.Axes.boxplot`.

See also
--------
PlotAxes.boxes
PlotAxes.boxesh
PlotAxes.boxplot
PlotAxes.boxploth
matplotlib.axes.Axes.boxplot
"""
docstring._snippet_manager["plot.boxplot"] = _boxplot_docstring.format(
    y="y", orientation="vertical"
)
docstring._snippet_manager["plot.boxploth"] = _boxplot_docstring.format(
    y="x", orientation="horizontal"
)


# Violin plot docstrings
_violinplot_docstring = """
Plot {orientation} violins with a nice default style matching
`this matplotlib example \
<https://matplotlib.org/stable/gallery/statistics/customized_violin.html>`__.

Parameters
----------
%(plot.args_1d_{y})s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.patch_black)s
%(plot.labels_1d)s
showmeans, showmedians : bool, optional
    Interpreted as ``means=True`` and ``medians=True`` when passed.
showextrema : bool, optional
    Interpreted as ``barpctiles=True`` when passed (i.e. shows minima and maxima).
%(plot.error_bars)s
**kwargs
    Passed to `matplotlib.axes.Axes.violinplot`.

See also
--------
PlotAxes.violin
PlotAxes.violinh
PlotAxes.violinplot
PlotAxes.violinploth
matplotlib.axes.Axes.violinplot
"""
docstring._snippet_manager["plot.violinplot"] = _violinplot_docstring.format(
    y="y", orientation="vertical"
)
docstring._snippet_manager["plot.violinploth"] = _violinplot_docstring.format(
    y="x", orientation="horizontal"
)


# 1D histogram docstrings
_hist_docstring = """
Plot {orientation} histograms.

Parameters
----------
%(plot.args_1d_{y})s
bins : int or sequence of float, optional
    The bin count or exact bin edges.
%(plot.weights)s
histtype : {{'bar', 'barstacked', 'step', 'stepfilled'}}, optional
    The histogram type. See `matplotlib.axes.Axes.hist` for details.
width, rwidth : float, default: 0.8 or 1
    The bar width(s) for bar-type histograms relative to the bin size. Default
    is ``0.8`` for multiple columns of unstacked data and ``1`` otherwise.
stack, stacked : bool, optional
    Whether to "stack" successive columns of {y} data for bar-type histograms
    or show side-by-side in groups. Setting this to ``False`` is equivalent to
    ``histtype='bar'`` and to ``True`` is equivalent to ``histtype='barstacked'``.
fill, filled : bool, optional
    Whether to "fill" step-type histograms or just plot the edges. Setting
    this to ``False`` is equivalent to ``histtype='step'`` and to ``True``
    is equivalent to ``histtype='stepfilled'``.
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.patch)s
%(axes.edgefix)s
%(plot.labels_1d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.hist`.

See also
--------
PlotAxes.hist
PlotAxes.histh
matplotlib.axes.Axes.hist
"""
_weights_docstring = """
weights : array-like, optional
    The weights associated with each point. If string this
    can be retrieved from `data` (see below).
"""
docstring._snippet_manager["plot.weights"] = _weights_docstring
docstring._snippet_manager["plot.hist"] = _hist_docstring.format(
    y="x", orientation="vertical"
)
docstring._snippet_manager["plot.histh"] = _hist_docstring.format(
    y="x", orientation="horizontal"
)


# 2D histogram docstrings
_hist2d_docstring = """
Plot a {descrip}.
standard 2D histogram.

Parameters
----------
%(plot.args_1d_y)s{bins}
%(plot.weights)s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(plot.labels_2d)s
%(plot.guide)s
**kwargs
    Passed to `~matplotlib.axes.Axes.{command}`.

See also
--------
PlotAxes.hist2d
PlotAxes.hexbin
matplotlib.axes.Axes.{command}
"""
_bins_docstring = """
bins : int or 2-tuple of int, or array-like or 2-tuple of array-like, optional
    The bin count or exact bin edges for each dimension or both dimensions.
""".rstrip()
docstring._snippet_manager["plot.hist2d"] = _hist2d_docstring.format(
    command="hist2d", descrip="standard 2D histogram", bins=_bins_docstring
)
docstring._snippet_manager["plot.hexbin"] = _hist2d_docstring.format(
    command="hexbin", descrip="2D hexagonally binned histogram", bins=""
)


# Pie chart docstring
_pie_docstring = """
Plot a pie chart.

Parameters
----------
%(plot.args_1d_y)s
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cycle)s
%(artist.patch)s
%(axes.edgefix)s
%(plot.labels_1d)s
labelpad, labeldistance : float, optional
    The distance at which labels are drawn in radial coordinates.

See also
--------
matplotlib.axes.Axes.pie
"""
docstring._snippet_manager["plot.pie"] = _pie_docstring


# Contour docstrings
_contour_docstring = """
Plot {descrip}.

Parameters
----------
%(plot.args_2d)s

%(plot.args_2d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(artist.collection_contour)s{edgefix}
%(plot.labels_2d)s
%(plot.guide)s
**kwargs
    Passed to `matplotlib.axes.Axes.{command}`.

See also
--------
PlotAxes.contour
PlotAxes.contourf
PlotAxes.tricontour
PlotAxes.tricontourf
matplotlib.axes.Axes.{command}
"""
docstring._snippet_manager["plot.contour"] = _contour_docstring.format(
    descrip="contour lines", command="contour", edgefix=""
)
docstring._snippet_manager["plot.contourf"] = _contour_docstring.format(
    descrip="filled contours",
    command="contourf",
    edgefix="%(axes.edgefix)s\n",
)
docstring._snippet_manager["plot.tricontour"] = _contour_docstring.format(
    descrip="contour lines on a triangular grid", command="tricontour", edgefix=""
)
docstring._snippet_manager["plot.tricontourf"] = _contour_docstring.format(
    descrip="filled contours on a triangular grid",
    command="tricontourf",
    edgefix="\n%(axes.edgefix)s",  # noqa: E501
)

_graph_docstring = r"""
Plot a networkx graph with flexible node, edge, and label options.

Parameters
----------
g : networkx.Graph
    The graph object to be plotted. Can be any subclass of :class:`networkx.Graph`, such as
    :class:`networkx.DiGraph` or :class:`networkx.MultiGraph`.
layout : callable or dict, optional
    A layout function or a precomputed dict mapping nodes to 2D positions. If a function
    is given, it is called as ``layout(g, **layout_kw)`` to compute positions. See :func:`networkx.drawing.nx_pylab.draw` for more information.
nodes : bool or iterable, default: rc["graph.draw_nodes"]
    Which nodes to draw. If `True`, all nodes are drawn. If an iterable is provided, only
    the specified nodes are included. This effectively acts as `nodelist` in :func:`networkx.drawing.nx_pylab.draw_networkx_nodes`.
edges : bool or iterable, default: rc["graph.draw_edges"]
    Which edges to draw. If `True`, all edges are drawn. If an iterable of edge tuples is
    provided, only those edges are included. This effectively acts as `edgelist` in :func:`networkx.drawing.nx_pylab.draw_networkx_edges`.
labels : bool or iterable, default: `rc["graph.draw_labels`]
    Whether to show node labels. If `True`, labels are drawn using node names. If an
    iterable is given, only those nodes are labeled.
layout_kw : dict, default: {}
    Keyword arguments passed to the layout function, if `layout` is callable, see `networkx's drawing functions <https://networkx.org/documentation/stable/reference/drawing.html>`_ for more information.
node_kw : dict, default: {}
    Additional keyword arguments passed to the node drawing function (see :func:`networkx.drawing.nx_pylab.draw_networkx_nodes`). These can include
    size, color, edgecolor, cmap, alpha, etc., depending on the backend used, see :func:`networkx.drawing.nx_pylab.draw_networkx_nodes`.
edge_kw : dict, default: {}
    Additional keyword arguments passed to the edge drawing function. These can include
    width, color, style, alpha, arrows, etc (see :func:`networkx.drawing.nx_pylab.draw_networkx_edges`).
label_kw : dict, default: {}
    Additional keyword arguments passed to the label drawing function, such as font size,
    font color, background color, alignment, etc (see :func:`networkx.drawing.nx_pylab.draw_networkx_labels`).
rescale : bool,  None, default: None.
    When set to none it checks for `rc["graph.rescale"]` which defaults to `True`. This performs a rescale such that the node position is within a [0, 1] x [0, 1] box.
Returns
-------
Nodes, edges, labels output from the networkx drawing functions.

See also
--------
networkx.draw
networkx.draw_networkx
networkx.draw_networkx_nodes
networkx.draw_networkx_edges
networkx.draw_networkx_labels
"""

docstring._snippet_manager["plot.graph"] = _graph_docstring


# Pcolor docstring
_pcolor_docstring = """
Plot {descrip}.

Parameters
----------
%(plot.args_2d)s

%(plot.args_2d_shared)s{aspect}

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(artist.collection_pcolor)s
%(axes.edgefix)s
%(plot.labels_2d)s
%(plot.guide)s
**kwargs
    Passed to `matplotlib.axes.Axes.{command}`.

See also
--------
PlotAxes.pcolor
PlotAxes.pcolormesh
PlotAxes.pcolorfast
PlotAxes.heatmap
PlotAxes.tripcolor
matplotlib.axes.Axes.{command}
"""
_heatmap_descrip = """
grid boxes with formatting suitable for heatmaps. Ensures square grid
boxes, adds major ticks to the center of each grid box, disables minor
ticks and gridlines, and sets :rcraw:`cmap.discrete` to ``False`` by default
""".strip()
_heatmap_aspect = """
aspect : {'equal', 'auto'} or float, default: :rc:`image.aspet`
    Modify the axes aspect ratio. The aspect ratio is of particular relevance for
    heatmaps since it may lead to non-square grid boxes. This parameter is a shortcut
    for calling `~matplotlib.axes.set_aspect`. The options are as follows:

    * Number: The data aspect ratio.
    * ``'equal'``: A data aspect ratio of 1.
    * ``'auto'``: Allows the data aspect ratio to change depending on
      the layout. In general this results in non-square grid boxes.
""".rstrip()
docstring._snippet_manager["plot.pcolor"] = _pcolor_docstring.format(
    descrip="irregular grid boxes", command="pcolor", aspect=""
)
docstring._snippet_manager["plot.pcolormesh"] = _pcolor_docstring.format(
    descrip="regular grid boxes", command="pcolormesh", aspect=""
)
docstring._snippet_manager["plot.pcolorfast"] = _pcolor_docstring.format(
    descrip="grid boxes quickly", command="pcolorfast", aspect=""
)
docstring._snippet_manager["plot.tripcolor"] = _pcolor_docstring.format(
    descrip="triangular grid boxes", command="tripcolor", aspect=""
)
docstring._snippet_manager["plot.heatmap"] = _pcolor_docstring.format(
    descrip=_heatmap_descrip, command="pcolormesh", aspect=_heatmap_aspect
)


# Image docstring
_show_docstring = """
Plot {descrip}.

Parameters
----------
z : array-like
    The data passed as a positional argument or keyword argument.
%(plot.args_1d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.levels_manual)s
%(plot.levels_auto)s
%(plot.guide)s
**kwargs
    Passed to `matplotlib.axes.Axes.{command}`.

See also
--------
ultraplot.axes.PlotAxes
matplotlib.axes.Axes.{command}
"""
docstring._snippet_manager["plot.imshow"] = _show_docstring.format(
    descrip="an image", command="imshow"
)
docstring._snippet_manager["plot.matshow"] = _show_docstring.format(
    descrip="a matrix", command="matshow"
)
docstring._snippet_manager["plot.spy"] = _show_docstring.format(
    descrip="a sparcity pattern", command="spy"
)


# Flow function docstring
_flow_docstring = """
Plot {descrip}.

Parameters
----------
%(plot.args_2d_flow)s

c, color, colors : array-like or color-spec, optional
    The colors of the {descrip} passed as either a keyword argument
    or a fifth positional argument. This can be a single color or
    a color array to be scaled by `cmap` and `norm`.
%(plot.args_2d_shared)s

Other parameters
----------------
%(plot.cmap_norm)s
%(plot.vmin_vmax)s
%(plot.levels_manual)s
%(plot.levels_auto)s
**kwargs
    Passed to `matplotlib.axes.Axes.{command}`

See also
--------
PlotAxes.barbs
PlotAxes.quiver
PlotAxes.stream
PlotAxes.streamplot
matplotlib.axes.Axes.{command}
"""
docstring._snippet_manager["plot.barbs"] = _flow_docstring.format(
    descrip="wind barbs", command="barbs"
)
docstring._snippet_manager["plot.quiver"] = _flow_docstring.format(
    descrip="quiver arrows", command="quiver"
)
docstring._snippet_manager["plot.stream"] = _flow_docstring.format(
    descrip="streamlines", command="streamplot"
)


def _get_vert(vert=None, orientation=None, **kwargs):
    """
    Get the orientation specified as either `vert` or `orientation`. This is
    used internally by various helper functions.
    """
    if vert is not None:
        return kwargs, vert
    elif orientation is not None:
        return kwargs, orientation != "horizontal"  # should already be validated
    else:
        return kwargs, True  # fallback


def _parse_vert(
    vert=None, orientation=None, default_vert=None, default_orientation=None, **kwargs
):
    """
    Interpret both 'vert' and 'orientation' and add to outgoing keyword args
    if a default is provided.
    """
    # NOTE: Users should only pass these to hist, boxplot, or violinplot. To change
    # the plot, scatter, area, or bar orientation users should use the differently
    # named functions. Internally, however, they use these keyword args.
    if default_vert is not None:
        kwargs["vert"] = _not_none(
            vert=vert,
            orientation=None if orientation is None else orientation == "vertical",
            default=default_vert,
        )
    if default_orientation is not None:
        kwargs["orientation"] = _not_none(
            orientation=orientation,
            vert=None if vert is None else "vertical" if vert else "horizontal",
            default=default_orientation,
        )
    if kwargs.get("orientation", None) not in (None, "horizontal", "vertical"):
        raise ValueError("Orientation must be either 'horizontal' or 'vertical'.")
    return kwargs


def _inside_seaborn_call():
    """
    Try to detect `seaborn` calls to `scatter` and `bar` and then automatically
    apply `absolute_size` and `absolute_width`.
    """
    frame = sys._getframe()
    absolute_names = (
        "seaborn.distributions",
        "seaborn.categorical",
        "seaborn.relational",
        "seaborn.regression",
    )
    while frame is not None:
        if frame.f_globals.get("__name__", "") in absolute_names:
            return True
        frame = frame.f_back
    return False


class PlotAxes(base.Axes):
    """
    The second lowest-level `~matplotlib.axes.Axes` subclass used by ultraplot.
    Implements all plotting overrides.
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args, **kwargs
            Passed to `ultraplot.axes.Axes`.

        See also
        --------
        matplotlib.axes.Axes
        ultraplot.axes.Axes
        ultraplot.axes.CartesianAxes
        ultraplot.axes.PolarAxes
        ultraplot.axes.GeoAxes
        """
        super().__init__(*args, **kwargs)

    def _call_native(self, name, *args, **kwargs):
        """
        Call the plotting method and redirect internal calls to native methods.
        """
        # NOTE: Previously allowed internal matplotlib plotting function calls to run
        # through ultraplot overrides then avoided awkward conflicts in piecemeal fashion.
        # Now prevent internal calls from running through overrides using preprocessor
        kwargs.pop("distribution", None)  # remove stat distributions
        with context._state_context(self, _internal_call=True):
            if self._name == "basemap":
                obj = getattr(self.projection, name)(*args, ax=self, **kwargs)
            else:
                obj = getattr(super(), name)(*args, **kwargs)
        return obj

    def _call_negpos(
        self,
        name,
        x,
        *ys,
        negcolor=None,
        poscolor=None,
        colorkey="facecolor",
        use_where=False,
        use_zero=False,
        **kwargs,
    ):
        """
        Call the plotting method separately for "negative" and "positive" data.
        """
        if use_where:
            kwargs.setdefault("interpolate", True)  # see fill_between docs
        for key in ("color", "colors", "facecolor", "facecolors", "where"):
            value = kwargs.pop(key, None)
            if value is not None:
                warnings._warn_ultraplot(
                    f"{name}() argument {key}={value!r} is incompatible with negpos=True. Ignoring."  # noqa: E501
                )
        # Negative component
        yneg = list(ys)  # copy
        if use_zero:  # filter bar heights
            yneg[0] = inputs._safe_mask(ys[0] < 0, ys[0])
        elif use_where:  # apply fill_between mask
            kwargs["where"] = ys[1] < ys[0]
        else:
            yneg = inputs._safe_mask(ys[1] < ys[0], *ys)
        kwargs[colorkey] = _not_none(negcolor, rc["negcolor"])
        negobj = self._call_native(name, x, *yneg, **kwargs)
        # Positive component
        ypos = list(ys)  # copy
        if use_zero:  # filter bar heights
            ypos[0] = inputs._safe_mask(ys[0] >= 0, ys[0])
        elif use_where:  # apply fill_between mask
            kwargs["where"] = ys[1] >= ys[0]
        else:
            ypos = inputs._safe_mask(ys[1] >= ys[0], *ys)
        kwargs[colorkey] = _not_none(poscolor, rc["poscolor"])
        posobj = self._call_native(name, x, *ypos, **kwargs)
        return cbook.silent_list(type(negobj).__name__, (negobj, posobj))

    def _add_auto_labels(
        self,
        obj,
        cobj=None,
        labels=False,
        labels_kw=None,
        fmt=None,
        formatter=None,
        formatter_kw=None,
        precision=None,
    ):
        """
        Add number labels. Default formatter is `~ultraplot.ticker.SimpleFormatter`
        with a default maximum precision of ``3`` decimal places.
        """
        # TODO: Add quiverkey to this!
        if not labels:
            return
        labels_kw = labels_kw or {}
        formatter_kw = formatter_kw or {}
        formatter = _not_none(
            fmt_labels_kw=labels_kw.pop("fmt", None),
            formatter_labels_kw=labels_kw.pop("formatter", None),
            fmt=fmt,
            formatter=formatter,
            default="simple",
        )
        precision = _not_none(
            formatter_kw_precision=formatter_kw.pop("precision", None),
            precision=precision,
            default=3,  # should be lower than the default intended for tick labels
        )
        formatter = constructor.Formatter(
            formatter, precision=precision, **formatter_kw
        )  # noqa: E501
        match obj:
            case mcontour.ContourSet():
                self._add_contour_labels(obj, cobj, formatter, **labels_kw)
            case mcollections.QuadMesh():
                self._add_quadmesh_labels(obj, formatter, **labels_kw)
            case mcollections.Collection():
                self._add_collection_labels(obj, formatter, **labels_kw)
            case _:
                raise RuntimeError(f"Not possible to add labels to object {obj!r}.")

    def _add_quadmesh_labels(
        self,
        obj,
        fmt,
        *,
        c=None,
        color=None,
        colors=None,
        size=None,
        fontsize=None,
        **kwargs,
    ):
        """
        Add labels to QuadMesh cells with support for shade-dependent text colors.
        Values are inferred from the unnormalized mesh cell color.
        """
        # Parse input args
        obj.update_scalarmappable()
        color = _not_none(c=c, color=color, colors=colors)
        fontsize = _not_none(size=size, fontsize=fontsize, default=rc["font.smallsize"])
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")

        # Get the mesh data
        array = obj.get_array()
        coords = obj.get_coordinates()  # This gives vertices (11x11x2)

        # Calculate cell centers by averaging the four corners of each cell
        x_centers = (coords[:-1, :-1, 0] + coords[1:, 1:, 0]) / 2
        y_centers = (coords[:-1, :-1, 1] + coords[1:, 1:, 1]) / 2

        # Apply colors and create labels
        labs = []
        for i, ((x, y), value) in enumerate(
            zip(zip(x_centers.flat, y_centers.flat), array.flat)
        ):
            # Skip masked or invalid values
            if value is ma.masked or not np.isfinite(value):
                continue

            # Handle discrete normalization if present
            if isinstance(obj.norm, pcolors.DiscreteNorm):
                value = obj.norm._norm.inverse(obj.norm(value))

            # Determine text color based on background
            icolor = color
            if color is None:
                _, _, lum = utils.to_xyz(obj.cmap(obj.norm(value)), "hcl")
                icolor = "w" if lum < 50 else "k"

            # Create text label
            lab = self.text(x, y, fmt(value), color=icolor, size=fontsize, **kwargs)
            labs.append(lab)

        return labs

    def _add_collection_labels(
        self,
        obj,
        fmt,
        *,
        c=None,
        color=None,
        colors=None,
        size=None,
        fontsize=None,
        **kwargs,
    ):
        """
        Add labels to pcolor boxes with support for shade-dependent text colors.
        Values are inferred from the unnormalized grid box color.
        """
        # Parse input args
        # NOTE: This function also hides grid boxes filled with NaNs to avoid ugly
        # issue where edge colors surround NaNs. Should maybe move this somewhere else.
        obj.update_scalarmappable()  # update 'edgecolors' list
        color = _not_none(c=c, color=color, colors=colors)
        fontsize = _not_none(size=size, fontsize=fontsize, default=rc["font.smallsize"])
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")

        # Apply colors and hide edge colors for empty grids
        labs = []
        array = obj.get_array()
        paths = obj.get_paths()
        edgecolors = inputs._to_numpy_array(obj.get_edgecolors())
        if len(edgecolors) == 1:
            edgecolors = np.repeat(edgecolors, len(array), axis=0)
        for i, (path, value) in enumerate(zip(paths, array)):
            # Round to the number corresponding to the *color* rather than
            # the exact data value. Similar to contour label numbering.
            if value is ma.masked or not np.any(np.isfinite(value) == False):
                edgecolors[i, :] = 0
                continue
            if isinstance(obj.norm, pcolors.DiscreteNorm):
                value = obj.norm._norm.inverse(obj.norm(value))
            icolor = color
            if color is None:
                _, _, lum = utils.to_xyz(obj.cmap(obj.norm(value)), "hcl")
                icolor = "w" if lum < 50 else "k"
            bbox = path.get_extents()
            x = (bbox.xmin + bbox.xmax) / 2
            y = (bbox.ymin + bbox.ymax) / 2
            lab = self.text(x, y, fmt(value), color=icolor, size=fontsize, **kwargs)
            labs.append(lab)
        obj.set_edgecolors(edgecolors)
        return labs

    def _add_contour_labels(
        self,
        obj,
        cobj,
        fmt,
        *,
        c=None,
        color=None,
        colors=None,
        size=None,
        fontsize=None,
        inline_spacing=None,
        **kwargs,
    ):
        """
        Add labels to contours with support for shade-dependent filled contour labels.
        Text color is inferred from filled contour object and labels are always drawn
        on unfilled contour object (otherwise errors crop up).
        """
        # Parse input args
        zorder = max(3, obj.get_zorder() + 1)
        kwargs.setdefault("zorder", zorder)
        colors = _not_none(c=c, color=color, colors=colors)
        fontsize = _not_none(size=size, fontsize=fontsize, default=rc["font.smallsize"])
        inline_spacing = _not_none(inline_spacing, 2.5)

        # Separate clabel args from text Artist args
        text_kw = {}
        clabel_keys = ("levels", "inline", "manual", "rightside_up", "use_clabeltext")
        for key in tuple(kwargs):  # allow dict to change size
            if key not in clabel_keys:
                text_kw[key] = kwargs.pop(key)

        # Draw hidden additional contour for filled contour labels
        cobj = _not_none(cobj, obj)
        if obj.filled and colors is None:
            colors = []
            for level in obj.levels:
                _, _, lum = utils.to_xyz(obj.cmap(obj.norm(level)))
                colors.append("w" if lum < 50 else "k")

        # Draw the labels
        labs = cobj.clabel(
            fmt=fmt,
            colors=colors,
            fontsize=fontsize,
            inline_spacing=inline_spacing,
            **kwargs,
        )
        if labs is not None:  # returns None if no contours
            for lab in labs:
                lab.update(text_kw)

        return labs

    def _add_error_bars(
        self,
        x,
        y,
        *_,
        distribution=None,
        default_barstds=False,
        default_boxstds=False,
        default_barpctiles=False,
        default_boxpctiles=False,
        default_marker=False,
        bars=None,
        boxes=None,
        barstd=None,
        barstds=None,
        barpctile=None,
        barpctiles=None,
        bardata=None,
        boxstd=None,
        boxstds=None,
        boxpctile=None,
        boxpctiles=None,
        boxdata=None,
        capsize=None,
        **kwargs,
    ):
        """
        Add up to 2 error indicators: thick "boxes" and thin "bars". The ``default``
        keywords toggle default range indicators when distributions are passed.
        """
        # Parse input args
        # NOTE: Want to keep _add_error_bars() and _add_error_shading() separate.
        # But also want default behavior where some default error indicator is shown
        # if user requests means/medians only. Result is the below kludge.
        kwargs, vert = _get_vert(**kwargs)
        barstds = _not_none(bars=bars, barstd=barstd, barstds=barstds)
        boxstds = _not_none(boxes=boxes, boxstd=boxstd, boxstds=boxstds)
        barpctiles = _not_none(barpctile=barpctile, barpctiles=barpctiles)
        boxpctiles = _not_none(boxpctile=boxpctile, boxpctiles=boxpctiles)
        if distribution is not None and not any(
            typ + mode in key
            for key in kwargs
            for typ in ("shade", "fade")
            for mode in ("", "std", "pctile", "data")
        ):  # ugly kludge to check for shading
            if all(_ is None for _ in (bardata, barstds, barpctiles)):
                barstds, barpctiles = default_barstds, default_barpctiles
            if all(_ is None for _ in (boxdata, boxstds, boxpctile)):
                boxstds, boxpctiles = default_boxstds, default_boxpctiles
        showbars = any(
            _ is not None and _ is not False for _ in (barstds, barpctiles, bardata)
        )
        showboxes = any(
            _ is not None and _ is not False for _ in (boxstds, boxpctiles, boxdata)
        )

        # Error bar properties
        edgecolor = kwargs.get("edgecolor", rc["boxplot.whiskerprops.color"])
        barprops = _pop_props(kwargs, "line", ignore="marker", prefix="bar")
        barprops["capsize"] = _not_none(capsize, rc["errorbar.capsize"])
        barprops["linestyle"] = "none"
        barprops.setdefault("color", edgecolor)
        barprops.setdefault("zorder", 2.5)
        barprops.setdefault("linewidth", rc["boxplot.whiskerprops.linewidth"])

        # Error box properties
        # NOTE: Includes 'markerfacecolor' and 'markeredgecolor' props
        boxprops = _pop_props(kwargs, "line", prefix="box")
        boxprops["capsize"] = 0
        boxprops["linestyle"] = "none"
        boxprops.setdefault("color", barprops["color"])
        boxprops.setdefault("zorder", barprops["zorder"])
        boxprops.setdefault("linewidth", 4 * barprops["linewidth"])

        # Box marker properties
        boxmarker = {
            key: boxprops.pop(key) for key in tuple(boxprops) if "marker" in key
        }  # noqa: E501
        boxmarker["c"] = _not_none(boxmarker.pop("markerfacecolor", None), "white")
        boxmarker["s"] = _not_none(
            boxmarker.pop("markersize", None), boxprops["linewidth"] ** 0.5
        )  # noqa: E501
        boxmarker["zorder"] = boxprops["zorder"]
        boxmarker["edgecolor"] = boxmarker.pop("markeredgecolor", None)
        boxmarker["linewidth"] = boxmarker.pop("markerlinewidth", None)
        if boxmarker.get("marker") is True:
            boxmarker["marker"] = "o"
        elif default_marker:
            boxmarker.setdefault("marker", "o")

        # Draw thin or thick error bars from distributions or explicit errdata
        # NOTE: Now impossible to make thin bar width different from cap width!
        # NOTE: Boxes must go after so scatter point can go on top
        sy = "y" if vert else "x"  # yerr
        ex, ey = (x, y) if vert else (y, x)
        eobjs = []
        if showbars:  # noqa: E501
            edata, _ = inputs._dist_range(
                y,
                distribution,
                stds=barstds,
                pctiles=barpctiles,
                errdata=bardata,
                stds_default=(-3, 3),
                pctiles_default=(0, 100),
            )
            if edata is not None:
                obj = self.errorbar(ex, ey, **barprops, **{sy + "err": edata})
                eobjs.append(obj)
        if showboxes:  # noqa: E501
            edata, _ = inputs._dist_range(
                y,
                distribution,
                stds=boxstds,
                pctiles=boxpctiles,
                errdata=boxdata,
                stds_default=(-1, 1),
                pctiles_default=(25, 75),
            )
            if edata is not None:
                obj = self.errorbar(ex, ey, **boxprops, **{sy + "err": edata})
                if boxmarker.get("marker", None):
                    self.scatter(ex, ey, **boxmarker)
                eobjs.append(obj)

        kwargs["distribution"] = distribution
        return (*eobjs, kwargs)

    def _add_error_shading(
        self,
        x,
        y,
        *_,
        distribution=None,
        color_key="color",
        shade=None,
        shadestd=None,
        shadestds=None,
        shadepctile=None,
        shadepctiles=None,
        shadedata=None,
        fade=None,
        fadestd=None,
        fadestds=None,
        fadepctile=None,
        fadepctiles=None,
        fadedata=None,
        shadelabel=False,
        fadelabel=False,
        **kwargs,
    ):
        """
        Add up to 2 error indicators: more opaque "shading" and less opaque "fading".
        """
        kwargs, vert = _get_vert(**kwargs)
        shadestds = _not_none(shade=shade, shadestd=shadestd, shadestds=shadestds)
        fadestds = _not_none(fade=fade, fadestd=fadestd, fadestds=fadestds)
        shadepctiles = _not_none(shadepctile=shadepctile, shadepctiles=shadepctiles)
        fadepctiles = _not_none(fadepctile=fadepctile, fadepctiles=fadepctiles)
        drawshade = any(
            _ is not None and _ is not False
            for _ in (shadestds, shadepctiles, shadedata)
        )
        drawfade = any(
            _ is not None and _ is not False for _ in (fadestds, fadepctiles, fadedata)
        )

        # Shading properties
        shadeprops = _pop_props(kwargs, "patch", prefix="shade")
        shadeprops.setdefault("alpha", 0.4)
        shadeprops.setdefault("zorder", 1.5)
        shadeprops.setdefault("linewidth", rc["patch.linewidth"])
        shadeprops.setdefault("edgecolor", "none")
        # Fading properties
        fadeprops = _pop_props(kwargs, "patch", prefix="fade")
        fadeprops.setdefault("zorder", shadeprops["zorder"])
        fadeprops.setdefault("alpha", 0.5 * shadeprops["alpha"])
        fadeprops.setdefault("linewidth", shadeprops["linewidth"])
        fadeprops.setdefault("edgecolor", "none")
        # Get default color then apply to outgoing keyword args so
        # that plotting function will not advance to next cycler color.
        # TODO: More robust treatment of 'color' vs. 'facecolor'
        if (
            drawshade
            and shadeprops.get("facecolor", None) is None
            or drawfade
            and fadeprops.get("facecolor", None) is None
        ):
            color = kwargs.get(color_key, None)
            if color is None:  # add to outgoing
                color = kwargs[color_key] = self._get_lines.get_next_color()
            shadeprops.setdefault("facecolor", color)
            fadeprops.setdefault("facecolor", color)

        # Draw dark and light shading from distributions or explicit errdata
        eobjs = []
        fill = self.fill_between if vert else self.fill_betweenx
        if drawfade:
            edata, label = inputs._dist_range(
                y,
                distribution,
                stds=fadestds,
                pctiles=fadepctiles,
                errdata=fadedata,
                stds_default=(-3, 3),
                pctiles_default=(0, 100),
                label=fadelabel,
                absolute=True,
            )
            if edata is not None:
                eobj = fill(x, *edata, label=label, **fadeprops)
                eobjs.append(eobj)
        if drawshade:
            edata, label = inputs._dist_range(
                y,
                distribution,
                stds=shadestds,
                pctiles=shadepctiles,
                errdata=shadedata,
                stds_default=(-2, 2),
                pctiles_default=(10, 90),
                label=shadelabel,
                absolute=True,
            )
            if edata is not None:
                eobj = fill(x, *edata, label=label, **shadeprops)
                eobjs.append(eobj)

        kwargs["distribution"] = distribution
        return (*eobjs, kwargs)

    def _fix_contour_edges(self, method, *args, **kwargs):
        """
        Fix the filled contour edges by secretly adding solid contours with
        the same input data.
        """
        # NOTE: This is used to provide an object that can be used by 'clabel' for
        # auto-labels. Filled contours create strange artifacts.
        # NOTE: Make the default 'line width' identical to one used for pcolor plots
        # rather than rc['contour.linewidth']. See mpl pcolor() source code
        if not any(key in kwargs for key in ("linewidths", "linestyles", "edgecolors")):
            kwargs["linewidths"] = 0  # for clabel
        kwargs.setdefault("linewidths", EDGEWIDTH)
        kwargs.pop("cmap", None)
        kwargs["colors"] = kwargs.pop("edgecolors", "k")
        return self._call_native(method, *args, **kwargs)

    def _fix_sticky_edges(self, objs, axis, *args, only=None):
        """
        Fix sticky edges for the input artists using the minimum and maximum of the
        input coordinates. This is used to copy `bar` behavior to `area` and `lines`.
        """
        for array in args:
            min_, max_ = inputs._safe_range(array)
            if min_ is None or max_ is None:
                continue
            for obj in guides._iter_iterables(objs):
                if only and not isinstance(obj, only):
                    continue  # e.g. ignore error bars
                convert = getattr(self, "convert_" + axis + "units")
                edges = getattr(obj.sticky_edges, axis)
                edges.extend(convert((min_, max_)))

    @staticmethod
    def _fix_patch_edges(obj, edgefix=None, **kwargs):
        """
        Fix white lines between between filled patches and fix issues
        with colormaps that are transparent. If keyword args passed by user
        include explicit edge properties then we skip this step.
        """
        # NOTE: Use default edge width used for pcolor grid box edges. This is thick
        # enough to hide lines but thin enough to not add 'nubs' to corners of boxes.
        # See: https://github.com/jklymak/contourfIssues
        # See: https://stackoverflow.com/q/15003353/4970632
        edgefix = _not_none(edgefix, rc.edgefix, True)
        linewidth = EDGEWIDTH if edgefix is True else 0 if edgefix is False else edgefix
        if not linewidth:
            return
        keys = ("linewidth", "linestyle", "edgecolor")  # patches and collections
        if any(key + suffix in kwargs for key in keys for suffix in ("", "s")):
            return
        rasterized = obj.get_rasterized() if isinstance(obj, martist.Artist) else False
        if rasterized:
            return

        # Skip when cmap has transparency
        if hasattr(obj, "get_alpha"):  # collections and contour sets use singular
            alpha = obj.get_alpha()
            if alpha is not None and alpha < 1:
                return
        if isinstance(obj, mcm.ScalarMappable):
            cmap = obj.cmap
            if not cmap._isinit:
                cmap._init()
            if not all(cmap._lut[:-1, 3] == 1):  # skip for cmaps with transparency
                return

        # Apply fixes
        # NOTE: This also covers TriContourSet returned by tricontour
        if isinstance(obj, mcontour.ContourSet):
            if obj.filled:
                obj.set_linestyle("-")
                obj.set_linewidth(linewidth)
                obj.set_edgecolor("face")
        elif isinstance(obj, mcollections.Collection):  # e.g. QuadMesh, PolyCollection
            obj.set_linewidth(linewidth)
            obj.set_edgecolor("face")
        elif isinstance(obj, mpatches.Patch):  # e.g. Rectangle
            obj.set_linewidth(linewidth)
            obj.set_edgecolor(obj.get_facecolor())
        elif np.iterable(obj):  # e.g. silent_list of BarContainer
            for element in obj:
                PlotAxes._fix_patch_edges(element, edgefix=edgefix)
        else:
            warnings._warn_ultraplot(
                f"Unexpected obj {obj} passed to _fix_patch_edges."
            )

    @contextlib.contextmanager
    def _keep_grid_bools(self):
        """
        Preserve the gridline booleans during the operation. This prevents `pcolor`
        methods from disabling grids (mpl < 3.5) and emitting warnings (mpl >= 3.5).
        """
        # NOTE: Modern matplotlib uses _get_axis_list() but this is only to support
        # Axes3D which PlotAxes does not subclass. Safe to use xaxis and yaxis.
        bools = []
        for axis, which in itertools.product(
            (self.xaxis, self.yaxis), ("major", "minor")
        ):
            kw = getattr(axis, f"_{which}_tick_kw", {})
            bools.append(kw.get("gridOn", None))
            kw["gridOn"] = False  # prevent deprecation warning
        yield
        for b, (axis, which) in zip(bools, itertools.product("xy", ("major", "minor"))):
            if b is not None:
                self.grid(b, axis=axis, which=which)

    def _inbounds_extent(self, *, inbounds=None, **kwargs):
        """
        Capture the `inbounds` keyword arg and return data limit
        extents if it is ``True``. Otherwise return ``None``. When
        ``_inbounds_xylim`` gets ``None`` it will silently exit.
        """
        extents = None
        inbounds = _not_none(inbounds, rc["axes.inbounds"])
        if inbounds:
            extents = list(self.dataLim.extents)  # ensure modifiable
        return kwargs, extents

    def _inbounds_vlim(self, x, y, z, *, to_centers=False):
        """
        Restrict the sample data used for automatic `vmin` and `vmax` selection
        based on the existing x and y axis limits.
        """
        # Get masks
        # WARNING: Experimental, seems robust but this is not mission-critical so
        # keep this in a try-except clause for now. However *internally* we should
        # not reach this block unless everything is an array so raise that error.
        xmask = ymask = None
        if self._name != "cartesian":
            return z  # TODO: support geographic projections when input is PlateCarree()
        if not all(getattr(a, "ndim", None) in (1, 2) for a in (x, y, z)):
            raise ValueError("Invalid input coordinates. Must be 1D or 2D arrays.")
        try:
            # Get centers and masks
            if to_centers and z.ndim == 2:
                x, y = inputs._to_centers(x, y, z)
            if not self.get_autoscalex_on():
                xlim = self.get_xlim()
                xmask = (x >= min(xlim)) & (x <= max(xlim))
            if not self.get_autoscaley_on():
                ylim = self.get_ylim()
                ymask = (y >= min(ylim)) & (y <= max(ylim))
            # Get subsample
            if xmask is not None and ymask is not None:
                z = (
                    z[np.ix_(ymask, xmask)]
                    if z.ndim == 2 and xmask.ndim == 1
                    else z[ymask & xmask]
                )  # noqa: E501
            elif xmask is not None:
                z = z[:, xmask] if z.ndim == 2 and xmask.ndim == 1 else z[xmask]
            elif ymask is not None:
                z = z[ymask, :] if z.ndim == 2 and ymask.ndim == 1 else z[ymask]
            return z
        except Exception as err:
            warnings._warn_ultraplot(
                "Failed to restrict automatic colormap normalization "
                f"to in-bounds data only. Error message: {err}"
            )
            return z

    def _inbounds_xylim(self, extents, x, y, **kwargs):
        """
        Restrict the `dataLim` to exclude out-of-bounds data when x (y) limits
        are fixed and we are determining default y (x) limits. This modifies
        the mutable input `extents` to support iteration over columns.
        """
        # WARNING: This feature is still experimental. But seems obvious. Matplotlib
        # updates data limits in ad hoc fashion differently for each plotting command
        # but since ultraplot standardizes inputs we can easily use them for dataLim.
        if extents is None:
            return
        if self._name != "cartesian":
            return
        if not x.size or not y.size:
            return
        kwargs, vert = _get_vert(**kwargs)
        if not vert:
            x, y = y, x
        trans = self.dataLim
        autox, autoy = self.get_autoscalex_on(), self.get_autoscaley_on()
        try:
            if autoy and not autox and x.shape == y.shape:
                # Reset the y data limits
                xmin, xmax = sorted(self.get_xlim())
                mask = (x >= xmin) & (x <= xmax)
                ymin, ymax = inputs._safe_range(inputs._safe_mask(mask, y))
                convert = self.convert_yunits  # handle datetime, pint units
                if ymin is not None:
                    trans.y0 = extents[1] = min(convert(ymin), extents[1])
                if ymax is not None:
                    trans.y1 = extents[3] = max(convert(ymax), extents[3])
                getattr(self, "_request_autoscale_view", self.autoscale_view)()
            if autox and not autoy and y.shape == x.shape:
                # Reset the x data limits
                ymin, ymax = sorted(self.get_ylim())
                mask = (y >= ymin) & (y <= ymax)
                xmin, xmax = inputs._safe_range(inputs._safe_mask(mask, x))
                convert = self.convert_xunits  # handle datetime, pint units
                if xmin is not None:
                    trans.x0 = extents[0] = min(convert(xmin), extents[0])
                if xmax is not None:
                    trans.x1 = extents[2] = max(convert(xmax), extents[2])
                getattr(self, "_request_autoscale_view", self.autoscale_view)()
        except Exception as err:
            warnings._warn_ultraplot(
                "Failed to restrict automatic y (x) axis limit algorithm to "
                f"data within locked x (y) limits only. Error message: {err}"
            )

    def _parse_1d_args(self, x, *ys, **kwargs):
        """
        Interpret positional arguments for all 1D plotting commands.
        """
        # Standardize values
        zerox = not ys
        if zerox or all(y is None for y in ys):  # pad with remaining Nones
            x, *ys = None, x, *ys[1:]
        if len(ys) == 2:  # 'lines' or 'fill_between'
            if ys[1] is None:
                ys = (np.array([0.0]), ys[0])  # user input 1 or 2 positional args
            elif ys[0] is None:
                ys = (np.array([0.0]), ys[1])  # user input keyword 'y2' but no y1
        if any(y is None for y in ys):
            raise ValueError("Missing required data array argument.")
        ys = tuple(map(inputs._to_duck_array, ys))
        if x is not None:
            x = inputs._to_duck_array(x)
        x, *ys, kwargs = self._parse_1d_format(x, *ys, zerox=zerox, **kwargs)

        # Geographic corrections
        if self._name == "cartopy" and isinstance(
            kwargs.get("transform"), PlateCarree
        ):  # noqa: E501
            x, *ys = inputs._geo_cartopy_1d(x, *ys)
        elif self._name == "basemap" and kwargs.get("latlon", None):
            xmin, xmax = self._lonaxis.get_view_interval()
            x, *ys = inputs._geo_basemap_1d(x, *ys, xmin=xmin, xmax=xmax)

        return (x, *ys, kwargs)

    def _parse_1d_format(
        self,
        x,
        *ys,
        zerox=False,
        autox=True,
        autoy=True,
        autoformat=None,
        autoreverse=True,
        autolabels=True,
        autovalues=False,
        autoguide=True,
        label=None,
        labels=None,
        value=None,
        values=None,
        **kwargs,
    ):
        """
        Try to retrieve default coordinates from array-like objects and apply default
        formatting. Also update the keyword arguments.
        """
        # Parse input
        y = max(ys, key=lambda y: y.size)  # find a non-scalar y for inferring metadata
        autox = autox and not zerox  # so far just relevant for hist()
        autoformat = _not_none(autoformat, rc["autoformat"])
        kwargs, vert = _get_vert(**kwargs)
        labels = _not_none(
            label=label,
            labels=labels,
            value=value,
            values=values,
            legend_kw_labels=kwargs.get("legend_kw", {}).pop("labels", None),
            colorbar_kw_values=kwargs.get("colorbar_kw", {}).pop("values", None),
        )

        # Retrieve the x coords
        # NOTE: Where columns represent distributions, like for box and violinplot or
        # where we use 'means' or 'medians', columns coords (axis 1) are 'x' coords.
        # Otherwise, columns represent e.g. lines and row coords (axis 0) are 'x'
        # coords. Exception is passing "ragged arrays" to boxplot and violinplot.
        dists = any(kwargs.get(s) for s in ("mean", "means", "median", "medians"))
        raggd = any(getattr(y, "dtype", None) == "object" for y in ys)
        xaxis = 0 if raggd else 1 if dists or not autoy else 0
        if autox and x is None:
            x = inputs._meta_labels(y, axis=xaxis)  # use the first one

        # Retrieve the labels. We only want default legend labels if this is an
        # object with 'title' metadata and/or the coords are string.
        # WARNING: Confusing terminology differences here -- for box and violin plots
        # labels refer to indices along x axis.
        if autolabels and labels is None:
            laxis = 0 if not autox and not autoy else xaxis if not autoy else xaxis + 1
            if laxis >= y.ndim:
                labels = inputs._meta_title(y)
            else:
                labels = inputs._meta_labels(y, axis=laxis, always=False)
            notitle = not inputs._meta_title(labels)
            if labels is None:
                pass
            elif notitle and not any(isinstance(_, str) for _ in labels):
                labels = None

        # Apply the labels or values
        if labels is not None:
            if autovalues:
                kwargs["values"] = inputs._to_numpy_array(labels)
            elif autolabels:
                kwargs["labels"] = inputs._to_numpy_array(labels)

        # Apply title for legend or colorbar that uses the labels or values
        if autoguide and autoformat:
            title = inputs._meta_title(labels)
            if title:  # safely update legend_kw and colorbar_kw
                guides._add_guide_kw("legend", kwargs, title=title)
                guides._add_guide_kw("colorbar", kwargs, title=title)

        # Apply the basic x and y settings
        autox = autox and self._name == "cartesian"
        autoy = autoy and self._name == "cartesian"
        sx, sy = "xy" if vert else "yx"
        kw_format = {}
        if autox and autoformat:  # 'x' axis
            title = inputs._meta_title(x)
            if title:
                axis = getattr(self, sx + "axis")
                if axis.isDefault_label:
                    kw_format[sx + "label"] = title
        if autoy and autoformat:  # 'y' axis
            sy = sx if zerox else sy  # hist() 'y' values are along 'x' axis
            title = inputs._meta_title(y)
            if title:
                axis = getattr(self, sy + "axis")
                if axis.isDefault_label:
                    kw_format[sy + "label"] = title

        # Convert string-type coordinates to indices
        # NOTE: This should even allow qualitative string input to hist()
        if autox:
            x, kw_format = inputs._meta_coords(x, which=sx, **kw_format)
        if autoy:
            *ys, kw_format = inputs._meta_coords(*ys, which=sy, **kw_format)
        if autox and autoreverse and inputs._is_descending(x):
            if getattr(self, f"get_autoscale{sx}_on")():
                kw_format[sx + "reverse"] = True

        # Finally apply formatting and strip metadata
        # WARNING: Most methods that accept 2D arrays use columns of data, but when
        # pandas DataFrame specifically is passed to hist, boxplot, or violinplot, rows
        # of data assumed! Converting to ndarray necessary.
        if kw_format:
            self.format(**kw_format)
        ys = tuple(map(inputs._to_numpy_array, ys))
        if x is not None:  # pie() and hist()
            x = inputs._to_numpy_array(x)
        return (x, *ys, kwargs)

    def _parse_2d_args(
        self,
        x,
        y,
        *zs,
        globe=False,
        edges=False,
        allow1d=False,
        transpose=None,
        order=None,
        **kwargs,
    ):
        """
        Interpret positional arguments for all 2D plotting commands.
        """
        # Standardize values
        # NOTE: Functions pass two 'zs' at most right now
        if all(z is None for z in zs):
            x, y, zs = None, None, (x, y)[: len(zs)]
        if any(z is None for z in zs):
            raise ValueError("Missing required data array argument(s).")
        zs = tuple(inputs._to_duck_array(z, strip_units=True) for z in zs)
        if x is not None:
            x = inputs._to_duck_array(x)
        if y is not None:
            y = inputs._to_duck_array(y)
        if order is not None:
            if not isinstance(order, str) or order not in "CF":
                raise ValueError(f"Invalid order={order!r}. Options are 'C' or 'F'.")
            transpose = _not_none(
                transpose=transpose, transpose_order=bool("CF".index(order))
            )
        if transpose:
            zs = tuple(z.T for z in zs)
            if x is not None:
                x = x.T
            if y is not None:
                y = y.T
        x, y, *zs, kwargs = self._parse_2d_format(x, y, *zs, **kwargs)
        if edges:
            # NOTE: These functions quitely pass through 1D inputs, e.g. barb data
            x, y = inputs._to_edges(x, y, zs[0])
        else:
            x, y = inputs._to_centers(x, y, zs[0])

        # Geographic corrections
        if allow1d:
            pass
        elif self._name == "cartopy" and isinstance(
            kwargs.get("transform"), PlateCarree
        ):  # noqa: E501
            x, y, *zs = inputs._geo_cartopy_2d(x, y, *zs, globe=globe)
        elif self._name == "basemap" and kwargs.get("latlon", None):
            xmin, xmax = self._lonaxis.get_view_interval()
            x, y, *zs = inputs._geo_basemap_2d(
                x, y, *zs, xmin=xmin, xmax=xmax, globe=globe
            )  # noqa: E501
            x, y = np.meshgrid(x, y)  # WARNING: required always

        return (x, y, *zs, kwargs)

    def _parse_2d_format(
        self, x, y, *zs, autoformat=None, autoguide=True, autoreverse=True, **kwargs
    ):
        """
        Try to retrieve default coordinates from array-like objects and apply default
        formatting. Also apply optional transpose and update the keyword arguments.
        """
        # Retrieve coordinates
        autoformat = _not_none(autoformat, rc["autoformat"])
        if x is None and y is None:
            z = zs[0]
            if z.ndim == 1:
                x = inputs._meta_labels(z, axis=0)
                y = np.zeros(z.shape)  # default barb() and quiver() behavior in mpl
            else:
                x = inputs._meta_labels(z, axis=1)
                y = inputs._meta_labels(z, axis=0)

        # Apply labels and XY axis settings
        if self._name == "cartesian":
            # Apply labels
            # NOTE: Do not overwrite existing labels!
            kw_format = {}
            if autoformat:
                for s, d in zip("xy", (x, y)):
                    title = inputs._meta_title(d)
                    if title:
                        axis = getattr(self, s + "axis")
                        if axis.isDefault_label:
                            kw_format[s + "label"] = title

            # Handle string-type coordinates
            x, kw_format = inputs._meta_coords(x, which="x", **kw_format)
            y, kw_format = inputs._meta_coords(y, which="y", **kw_format)
            for s, d in zip("xy", (x, y)):
                if autoreverse and inputs._is_descending(d):
                    if getattr(self, f"get_autoscale{s}_on")():
                        kw_format[s + "reverse"] = True

            # Apply formatting
            if kw_format:
                self.format(**kw_format)

        # Apply title for legend or colorbar
        if autoguide and autoformat:
            title = inputs._meta_title(zs[0])
            if title:  # safely update legend_kw and colorbar_kw
                guides._add_guide_kw("legend", kwargs, title=title)
                guides._add_guide_kw("colorbar", kwargs, title=title)

        # Finally strip metadata
        x = inputs._to_numpy_array(x)
        y = inputs._to_numpy_array(y)
        zs = tuple(map(inputs._to_numpy_array, zs))
        return (x, y, *zs, kwargs)

    def _parse_color(self, x, y, c, *, apply_cycle=True, infer_rgb=False, **kwargs):
        """
        Parse either a colormap or color cycler. Colormap will be discrete and fade
        to subwhite luminance by default. Returns a HEX string if needed so we don't
        get ambiguous color warnings. Used with scatter, streamplot, quiver, barbs.
        """
        # NOTE: This function is positioned above the _parse_cmap and _parse_cycle
        # functions and helper functions.
        parsers = (self._parse_cmap, *self._level_parsers)
        if c is None or mcolors.is_color_like(c):
            if infer_rgb and c is not None:
                c = pcolors.to_hex(c)  # avoid scatter() ambiguous color warning
            if apply_cycle:  # False for scatter() so we can wait to get correct 'N'
                kwargs = self._parse_cycle(**kwargs)
        else:
            c = np.atleast_1d(c)  # should only have effect on 'scatter' input
            if infer_rgb and (
                inputs._is_categorical(c) or c.ndim == 2 and c.shape[1] in (3, 4)
            ):  # noqa: E501
                c = list(map(pcolors.to_hex, c))  # avoid iterating over columns
            else:
                center_levels = kwargs.pop("center_levels", None)
                kwargs = self._parse_cmap(
                    x,
                    y,
                    c,
                    plot_lines=True,
                    default_discrete=False,
                    center_levels=center_levels,
                    **kwargs,
                )  # noqa: E501
                parsers = (self._parse_cycle,)
        pop = _pop_params(kwargs, *parsers, ignore_internal=True)
        if pop:
            warnings._warn_ultraplot(f"Ignoring unused keyword arg(s): {pop}")
        return (c, kwargs)

    @warnings._rename_kwargs("0.6.0", centers="values")
    def _parse_cmap(
        self,
        *args,
        cmap=None,
        cmap_kw=None,
        c=None,
        color=None,
        colors=None,
        norm=None,
        norm_kw=None,
        extend=None,
        vmin=None,
        vmax=None,
        discrete=None,
        default_cmap=None,
        default_discrete=True,
        skip_autolev=False,
        min_levels=None,
        plot_lines=False,
        plot_contours=False,
        center_levels=None,
        **kwargs,
    ):
        """
        Parse colormap and normalizer arguments.

        Parameters
        ----------
        c, color, colors : sequence of color-spec, optional
            Build a `DiscreteColormap` from the input color(s).
        cmap, cmap_kw : optional
            Colormap specs.
        norm, norm_kw : optional
            Normalize specs.
        extend : optional
            The colormap extend setting.
        vmin, vmax : float, optional
            The normalization range.
        sequential, diverging, cyclic, qualitative : bool, optional
            Toggle various colormap types.
        discrete : bool, optional
            Whether to apply `DiscreteNorm` to the colormap.
        default_discrete : bool, optional
            The default `discrete`. Depends on plotting method.
        skip_autolev : bool, optional
            Whether to skip automatic level generation.
        min_levels : int, optional
            The minimum number of valid levels. 1 for line contour plots 2 otherwise.
        plot_lines : bool, optional
            Whether these are lines. If so the default monochromatic luminance is 90.
        plot_contours : bool, optional
            Whether these are contours. If so then a discrete of `True` is required.
        """
        # Parse keyword args
        cmap_kw = cmap_kw or {}
        norm_kw = norm_kw or {}
        # If norm is given we use it to set vmin and vmax
        if (vmin is not None or vmax is not None) and norm is not None:
            raise ValueError("If 'norm' is given, 'vmin' and 'vmax' must not be set.")
        if isinstance(norm, mcolors.Normalize):
            vmin = norm.vmin
            vmax = norm.vmax
        vmin = _not_none(vmin=vmin, norm_kw_vmin=norm_kw.pop("vmin", None))
        vmax = _not_none(vmax=vmax, norm_kw_vmax=norm_kw.pop("vmax", None))
        extend = _not_none(extend, "neither")
        colors = _not_none(c=c, color=color, colors=colors)  # in case untranslated
        modes = {
            key: kwargs.pop(key, None)
            for key in ("sequential", "diverging", "cyclic", "qualitative")
        }  # noqa: E501
        trues = {key: b for key, b in modes.items() if b}
        if len(trues) > 1:  # noqa: E501
            warnings._warn_ultraplot(
                f"Conflicting colormap arguments: {trues!r}. Using the first one."
            )
            for key in tuple(trues)[1:]:
                del trues[key]
                modes[key] = None

        # Create user-input colormap and potentially disable autodiverging
        # NOTE: Let people use diverging=False with diverging cmaps because some
        # use them (wrongly IMO but to each their own) for increased color contrast.
        # WARNING: Previously 'colors' set the edgecolors. To avoid all-black
        # colormap make sure to ignore 'colors' if 'cmap' was also passed.
        # WARNING: Previously tried setting number of levels to len(colors), but this
        # makes single-level single-color contour plots, and since _parse_level_num is
        # only generates approximate level counts, the idea failed anyway. Users should
        # pass their own levels to avoid truncation/cycling in these very special cases.
        autodiverging = rc["cmap.autodiverging"]
        if colors is not None:
            if cmap is not None:
                warnings._warn_ultraplot(
                    f"you specified both cmap={cmap!s} and the qualitative-colormap "
                    f"colors={colors!r}. Ignoring 'colors'. If you meant to specify "
                    f"the edge color please use e.g. edgecolor={colors!r} instead."
                )
            else:
                if mcolors.is_color_like(colors):
                    colors = [colors]  # RGB[A] tuple possibly
                cmap = colors = np.atleast_1d(colors)
                cmap_kw["listmode"] = "discrete"
        if cmap is not None:
            if plot_lines:
                cmap_kw["default_luminance"] = constructor.DEFAULT_CYCLE_LUMINANCE
            cmap = constructor.Colormap(cmap, **cmap_kw)
            name = re.sub(r"\A_*(.*?)(?:_r|_s|_copy)*\Z", r"\1", cmap.name.lower())
            if not any(name in opts for opts in pcolors.CMAPS_DIVERGING.items()):
                autodiverging = False  # avoid auto-truncation of sequential colormaps

        # Force default options in special cases
        # NOTE: Delay application of 'sequential', 'diverging', 'cyclic', 'qualitative'
        # until after level generation so 'diverging' can be automatically applied.
        if "cyclic" in trues or getattr(cmap, "_cyclic", None):
            if extend is not None and extend != "neither":
                warnings._warn_ultraplot(
                    f"Cyclic colormaps require extend='neither'. Ignoring extend={extend!r}"  # noqa: E501
                )
            extend = "neither"
        if "qualitative" in trues or isinstance(cmap, pcolors.DiscreteColormap):
            if discrete is not None and not discrete:  # noqa: E501
                warnings._warn_ultraplot(
                    "Qualitative colormaps require discrete=True. Ignoring discrete=False."  # noqa: E501
                )
            discrete = True
        if plot_contours:
            if discrete is not None and not discrete:
                warnings._warn_ultraplot(
                    "Contoured plots require discrete=True. Ignoring discrete=False."
                )
            discrete = True
        keys = ("levels", "values", "locator", "negative", "positive", "symmetric")
        if any(key in kwargs for key in keys):  # override
            discrete = _not_none(discrete, True)
        else:  # use global boolean rc['cmap.discrete'] or command-specific default
            discrete = _not_none(discrete, rc["cmap.discrete"], default_discrete)

        # Determine the appropriate 'vmin', 'vmax', and/or 'levels'
        # NOTE: Unlike xarray, but like matplotlib, vmin and vmax only approximately
        # determine level range. Levels are selected with Locator.tick_values().
        levels = None  # unused
        isdiverging = False
        if not discrete and not skip_autolev:
            vmin, vmax, kwargs = self._parse_level_lim(
                *args, vmin=vmin, vmax=vmax, **kwargs
            )
            if autodiverging and vmin is not None and vmax is not None:
                if abs(np.sign(vmax) - np.sign(vmin)) == 2:
                    isdiverging = True
        if discrete:
            levels, vmin, vmax, norm, norm_kw, kwargs = self._parse_level_vals(
                *args,
                vmin=vmin,
                vmax=vmax,
                norm=norm,
                norm_kw=norm_kw,
                extend=extend,
                min_levels=min_levels,
                center_levels=center_levels,
                skip_autolev=skip_autolev,
                **kwargs,
            )
            if autodiverging and levels is not None:
                _, counts = np.unique(np.sign(levels), return_counts=True)
                if counts[counts > 1].size > 1:
                    isdiverging = True
        if not trues and isdiverging and modes["diverging"] is None:
            trues["diverging"] = modes["diverging"] = True

        # Create the continuous normalizer.
        norm = _not_none(norm, "div" if "diverging" in trues else "linear")
        if isinstance(norm, mcolors.Normalize):
            norm.vmin, norm.vmax = vmin, vmax
        else:
            norm = constructor.Norm(norm, vmin=vmin, vmax=vmax, **norm_kw)
        isdiverging = autodiverging and isinstance(norm, pcolors.DivergingNorm)
        if not trues and isdiverging and modes["diverging"] is None:
            trues["diverging"] = modes["diverging"] = True

        # Create the final colormap
        if cmap is None:
            if default_cmap is not None:  # used internally
                cmap = default_cmap
            elif trues:
                cmap = rc["cmap." + tuple(trues)[0]]
            else:
                cmap = rc["image.cmap"]
            cmap = constructor.Colormap(cmap, **cmap_kw)

        # Create the discrete normalizer
        # Then finally warn and remove unused args
        if levels is not None:
            norm, cmap, kwargs = self._parse_level_norm(
                levels,
                norm,
                cmap,
                center_levels=center_levels,
                extend=extend,
                min_levels=min_levels,
                **kwargs,
            )
        params = _pop_params(kwargs, *self._level_parsers, ignore_internal=True)
        if "N" in params:  # use this for lookup table N instead of levels N
            cmap = cmap.copy(N=params.pop("N"))
        if params:
            warnings._warn_ultraplot(f"Ignoring unused keyword args(s): {params}")

        # Update outgoing args
        # NOTE: ContourSet natively stores 'extend' on the result but for other
        # classes we need to hide it on the object.
        kwargs.update({"cmap": cmap, "norm": norm})

        if plot_contours:
            kwargs.update({"levels": levels, "extend": extend})
        else:
            guides._add_guide_kw("colorbar", kwargs, extend=extend)
        return kwargs

    def _parse_cycle(
        self,
        ncycle=None,
        *,
        cycle=None,
        cycle_kw=None,
        cycle_manually=None,
        return_cycle=False,
        **kwargs,
    ):
        """
        Parse property cycle-related arguments.

        Parameters
        ----------
        ncycle : int, optional
            The number of samples to draw for the cycle.
        cycle : cycle-spec, optional
            The property cycle specifier.
        cycle_kw : dict-like, optional
            The property cycle keyword arguments
        cycle_manually : dict-like, optional
            Mapping of property cycle keys to plotting function keys. Used
            to translate property cycle line properties to scatter properties.
        return_cycle : bool, optional
            Whether to simply return the property cycle or apply it. The cycle is
            only applied (and therefore reset) if it differs from the current one.
        """
        cycle_kw = cycle_kw or {}
        # Ignore singular column plotting
        if ncycle != 1:
            cycle_kw.setdefault("N", ncycle)
        cycle_manually = cycle_manually or {}

        # Match-case for cycle resolution
        match cycle:
            case None if not cycle_kw:
                resolved_cycle = None
            case True:
                resolved_cycle = constructor.Cycle(rc["axes.prop_cycle"])
            case constructor.Cycle():
                resolved_cycle = constructor.Cycle(cycle, **cycle_kw)
            case str() if cycle.lower() == "none":
                resolved_cycle = None
            case str() | int() | Iterable():
                resolved_cycle = constructor.Cycle(cycle, **cycle_kw)
            case _:
                resolved_cycle = None

        # Ignore cycle for single-column plotting unless cycle is different
        if resolved_cycle and resolved_cycle != self._active_cycle:
            self.set_prop_cycle(resolved_cycle)

        # Apply manual cycle properties
        if cycle_manually:
            current_prop = self._get_lines._cycler_items[self._get_lines._idx]
            self._get_lines._idx = (self._get_lines._idx + 1) % len(self._active_cycle)
            for prop, key in cycle_manually.items():
                if kwargs.get(key) is None and prop in current_prop:
                    value = current_prop[prop]
                    kwargs[key] = pcolors.to_hex(value) if key == "c" else value
        # Return or apply cycle
        if return_cycle:
            return resolved_cycle, kwargs
        return kwargs

    def _parse_level_lim(
        self,
        *args,
        vmin=None,
        vmax=None,
        robust=None,
        inbounds=None,
        negative=None,
        positive=None,
        symmetric=None,
        to_centers=False,
        **kwargs,
    ):
        """
        Return a suitable vmin and vmax based on the input data.

        Parameters
        ----------
        *args
            The sample data.
        vmin, vmax : float, optional
            The user input minimum and maximum.
        robust : bool, optional
            Whether to limit the default range to exclude outliers.
        inbounds : bool, optional
            Whether to filter to in-bounds data.
        negative, positive, symmetric : bool, optional
            Whether limits should be negative, positive, or symmetric.
        to_centers : bool, optional
            Whether to convert coordinates to 'centers'.

        Returns
        -------
        vmin, vmax : float
            The minimum and maximum.
        **kwargs
            Unused arguemnts.
        """
        # Parse vmin and vmax
        automin = vmin is None
        automax = vmax is None
        if not automin and not automax:
            return vmin, vmax, kwargs

        # Parse input args
        inbounds = _not_none(inbounds, rc["cmap.inbounds"])
        robust = _not_none(robust, rc["cmap.robust"], False)
        robust = 96 if robust is True else 100 if robust is False else robust
        robust = np.atleast_1d(robust)
        if robust.size == 1:
            pmin, pmax = 50 + 0.5 * np.array([-robust.item(), robust.item()])
        elif robust.size == 2:
            pmin, pmax = robust.flat  # pull out of array
        else:
            raise ValueError(
                f"Unexpected robust={robust!r}. Must be bool, float, or 2-tuple."
            )  # noqa: E501

        # Get sample data
        # NOTE: Critical to use _to_numpy_array here because some
        # commands are unstandardized.
        # NOTE: Try to get reasonable *count* levels for hexbin/hist2d, but in general
        # have no way to select nice ones a priori (why we disable discretenorm).
        # NOTE: Currently we only ever use this function with *single* array input
        # but in future could make this public as a way for users (me) to get
        # automatic synced contours for a bunch of arrays in a grid.
        vmins, vmaxs = [], []
        if len(args) > 2:
            x, y, *zs = args
        else:
            x, y, *zs = None, None, *args
        for z in zs:
            if z is None:  # e.g. empty scatter color
                continue
            if z.ndim > 2:  # e.g. imshow data
                continue
            z = inputs._to_numpy_array(z)
            if inbounds and x is not None and y is not None:  # ignore if None coords
                z = self._inbounds_vlim(x, y, z, to_centers=to_centers)
            imin, imax = inputs._safe_range(z, pmin, pmax)
            if automin and imin is not None:
                vmins.append(imin)
            if automax and imax is not None:
                vmaxs.append(imax)
        if automin:
            vmin = min(vmins, default=0)
        if automax:
            vmax = max(vmaxs, default=1)

        # Apply modifications
        # NOTE: This is also applied to manual input levels lists in _parse_level_vals
        if negative:
            if automax:
                vmax = 0
            else:
                warnings._warn_ultraplot(
                    f"Incompatible arguments vmax={vmax!r} and negative=True. "
                    "Ignoring the latter."
                )
        if positive:
            if automin:
                vmin = 0
            else:
                warnings._warn_ultraplot(
                    f"Incompatible arguments vmin={vmin!r} and positive=True. "
                    "Ignoring the latter."
                )
        if symmetric:
            if automin and not automax:
                vmin = -vmax
            elif automax and not automin:
                vmax = -vmin
            elif automin and automax:
                vmin, vmax = -np.max(np.abs((vmin, vmax))), np.max(np.abs((vmin, vmax)))
            else:
                warnings._warn_ultraplot(
                    f"Incompatible arguments vmin={vmin!r}, vmax={vmax!r}, and "
                    "symmetric=True. Ignoring the latter."
                )

        return vmin, vmax, kwargs

    def _parse_level_num(
        self,
        *args,
        levels=None,
        locator=None,
        locator_kw=None,
        vmin=None,
        vmax=None,
        norm=None,
        norm_kw=None,
        extend=None,
        symmetric=None,
        center_levels=None,
        **kwargs,
    ):
        """
        Return a suitable level list given the input data, normalizer,
        locator, and vmin and vmax.

        Parameters
        ----------
        *args
            The sample data. Passed to `_parse_level_lim`.
        levels : int
            The approximate number of levels.
        locator, locator_kw
            The tick locator used to draw levels.
        vmin, vmax : float, optional
            The minimum and maximum values passed to the tick locator.
        norm, norm_kw : optional
            The continuous normalizer. Affects the default locator used to draw levels.
        extend : str, optional
            The extend setting. Affects level trimming settings.
        symmetric : bool, optional
            Whether the resulting levels should be symmetric about zero.

        Returns
        -------
        levels : list of float
            The level edges.
        **kwargs
            Unused arguments.
        """
        # Input args
        # NOTE: Some of this is adapted from the hidden contour.ContourSet._autolev
        # NOTE: We use 'symmetric' with MaxNLocator to ensure boundaries include a
        # zero level but may trim many of these below.
        norm_kw = norm_kw or {}
        locator_kw = locator_kw or {}
        extend = _not_none(extend, "neither")
        levels = _not_none(levels, rc["cmap.levels"])
        center_levels = _not_none(center_levels, rc["colorbar.center_levels"])
        vmin = _not_none(vmin=vmin, norm_kw_vmin=norm_kw.pop("vmin", None))
        vmax = _not_none(vmax=vmax, norm_kw_vmax=norm_kw.pop("vmax", None))
        norm = constructor.Norm(norm or "linear", **norm_kw)
        symmetric = _not_none(
            symmetric=symmetric,
            locator_kw_symmetric=locator_kw.pop("symmetric", None),
            default=False,
        )

        # Get default locator from input norm
        # NOTE: This normalizer is only temporary for inferring level locs
        norm = constructor.Norm(norm or "linear", **norm_kw)
        if locator is not None:
            locator = constructor.Locator(locator, **locator_kw)
        elif isinstance(norm, mcolors.LogNorm):
            locator = mticker.LogLocator(**locator_kw)
        elif isinstance(norm, mcolors.SymLogNorm):
            for key, default in (("base", 10), ("linthresh", 1)):
                val = _not_none(
                    getattr(norm, key, None), getattr(norm, "_" + key, None), default
                )  # noqa: E501
                locator_kw.setdefault(key, val)
            locator = mticker.SymmetricalLogLocator(**locator_kw)
        else:
            locator_kw["symmetric"] = symmetric
            locator = mticker.MaxNLocator(levels, min_n_ticks=1, **locator_kw)

        # Get default level locations
        nlevs = levels
        automin = vmin is None
        automax = vmax is None
        vmin, vmax, kwargs = self._parse_level_lim(
            *args, vmin=vmin, vmax=vmax, symmetric=symmetric, **kwargs
        )
        try:
            levels = locator.tick_values(vmin, vmax)
        except TypeError:  # e.g. due to datetime arrays
            return None, kwargs
        except RuntimeError:  # too-many-ticks error
            levels = np.linspace(vmin, vmax, levels)  # TODO: _autolev used N + 1

        # Possibly trim levels far outside of 'vmin' and 'vmax'
        # NOTE: This part is mostly copied from matplotlib _autolev
        if not symmetric:
            i0, i1 = 0, len(levels)  # defaults
            (under,) = np.where(levels < vmin)
            if len(under):
                i0 = under[-1]
                if not automin or extend in ("min", "both"):
                    i0 += 1  # permit out-of-bounds data
            (over,) = np.where(levels > vmax)
            if len(over):
                i1 = over[0] + 1 if len(over) else len(levels)
                if not automax or extend in ("max", "both"):
                    i1 -= 1  # permit out-of-bounds data
            if i1 - i0 < 3:
                i0, i1 = 0, len(levels)  # revert
            levels = levels[i0:i1]

        # Compare the no. of levels we got (levels) to what we wanted (nlevs)
        # If we wanted more than 2 times the result, then add nn - 1 extra
        # levels in-between the returned levels in normalized space (e.g. LogNorm).
        nn = nlevs // len(levels)
        if nn >= 2:
            olevels = norm(levels)
            nlevels = []
            for i in range(len(levels) - 1):
                l1, l2 = olevels[i], olevels[i + 1]
                nlevels.extend(np.linspace(l1, l2, nn + 1)[:-1])
            nlevels.append(olevels[-1])
            levels = norm.inverse(nlevels)

        # Center the bin edges around the center of the bin
        # rather than its edges
        if center_levels:
            # Shift the entire range but correct the range
            # later
            width = np.diff(levels)[0]
            levels -= width * 0.5
            # Add another bin edge at the width
            levels = np.append(levels, levels[-1] + width * np.sign(levels[-1]))
        return levels, kwargs

    def _parse_level_vals(
        self,
        *args,
        N=None,
        levels=None,
        values=None,
        extend=None,
        positive=False,
        negative=False,
        nozero=False,
        norm=None,
        norm_kw=None,
        skip_autolev=False,
        min_levels=None,
        center_levels=None,
        **kwargs,
    ):
        """
        Return levels resulting from a wide variety of keyword options.

        Parameters
        ----------
        *args
            The sample data. Passed to `_parse_level_lim`.
        N
            Shorthand for `levels`.
        levels : int or sequence of float, optional
            The levels list or (approximate) number of levels to create.
        values : int or sequence of float, optional
            The level center list or (approximate) number of level centers to create.
        positive, negative, nozero : bool, optional
            Whether to remove out non-positive, non-negative, and zero-valued
            levels. The latter is useful for single-color contour plots.
        norm, norm_kw : optional
            Passed to `Norm`. Used to possbily infer levels or to convert values.
        skip_autolev : bool, optional
            Whether to skip automatic level generation.
        min_levels : int, optional
            The minimum number of levels allowed.

        Returns
        -------
        levels : list of float
            The level edges.
        **kwargs
            Unused arguments.
        """

        # Helper function that restricts levels
        # NOTE: This should have no effect if levels were generated automatically.
        # However want to apply these to manual-input levels as well.
        def _restrict_levels(levels):
            kw = {}
            levels = np.asarray(levels)
            if len(levels) > 2:
                kw["atol"] = 1e-5 * np.min(np.diff(levels))
            if nozero:
                levels = levels[~np.isclose(levels, 0, **kw)]
            if positive:
                levels = levels[(levels > 0) | np.isclose(levels, 0, **kw)]
            if negative:
                levels = levels[(levels < 0) | np.isclose(levels, 0, **kw)]
            return levels

        # Helper function to sanitize input levels
        # NOTE: Include special case where color levels are referenced by string labels
        def _sanitize_levels(key, array, minsize):
            if np.iterable(array):
                array, _ = pcolors._sanitize_levels(array, minsize)
            elif isinstance(array, Integral):
                pass
            elif array is not None:
                raise ValueError(f"Invalid {key}={array}. Must be list or integer.")
            if isinstance(norm, (mcolors.BoundaryNorm, pcolors.SegmentedNorm)):
                if isinstance(array, Integral):
                    warnings._warn_ultraplot(
                        f"Ignoring {key}={array}. Using norm={norm!r} {key} instead."
                    )
                array = norm.boundaries if key == "levels" else None
            return array

        # Parse input arguments and resolve incompatibilities
        vmin = vmax = None
        levels = _not_none(N=N, levels=levels, norm_kw_levs=norm_kw.pop("levels", None))
        if positive and negative:
            warnings._warn_ultraplot(
                "Incompatible args positive=True and negative=True. Using former."
            )
            negative = False
        if levels is not None and values is not None:
            warnings._warn_ultraplot(
                f"Incompatible args levels={levels!r} and values={values!r}. Using former."  # noqa: E501
            )
            values = None

        # Infer level edges from level centers if possible
        # NOTE: The only way for user to manually impose BoundaryNorm is by
        # passing one -- users cannot create one using Norm constructor key.
        if isinstance(values, Integral):
            levels = values + 1
            values = None
        if values is None:
            levels = _sanitize_levels("levels", levels, _not_none(min_levels, 2))
            levels = _not_none(levels, rc["cmap.levels"])
        else:
            values = _sanitize_levels("values", values, 1)
            kwargs["discrete_ticks"] = values  # passed to _parse_level_norm
            if len(values) == 1:
                levels = [values[0] - 1, values[0] + 1]  # weird but why not
            elif norm is not None and norm not in ("segments", "segmented"):
                # Generate levels by finding in-between points in the
                # normalized numeric space, e.g. LogNorm space.
                norm_kw = norm_kw or {}
                convert = constructor.Norm(norm, **norm_kw)
                levels = convert.inverse(utils.edges(convert(values)))
            else:
                # Generate levels so that ticks will be centered between edges
                # Solve: (x1 + x2) / 2 = y --> x2 = 2 * y - x1 with arbitrary init x1
                descending = values[1] < values[0]
                if descending:  # e.g. [100, 50, 20, 10, 5, 2, 1] successful if reversed
                    values = values[::-1]
                levels = [1.5 * values[0] - 0.5 * values[1]]  # arbitrary starting point
                for value in values:
                    levels.append(2 * value - levels[-1])
                if np.any(np.diff(levels) < 0):  # never happens for evenly spaced levs
                    levels = utils.edges(values)
                if descending:  # then revert back below
                    levels = levels[::-1]

        # Process level edges and infer defaults
        # NOTE: Matplotlib colorbar algorithm *cannot* handle descending levels so
        # this function reverses them and adds special attribute to the normalizer.
        # Then colorbar() reads this attr and flips the axis and the colormap direction
        if np.iterable(levels):
            pop = _pop_params(kwargs, self._parse_level_num, ignore_internal=True)
            if pop:
                warnings._warn_ultraplot(f"Ignoring unused keyword arg(s): {pop}")
        elif not skip_autolev:
            levels, kwargs = self._parse_level_num(
                *args,
                levels=levels,
                norm=norm,
                norm_kw=norm_kw,
                extend=extend,
                negative=negative,
                positive=positive,
                center_levels=center_levels,
                **kwargs,
            )
        else:
            levels = values = None

        # Determine default colorbar locator and norm and apply filters
        # NOTE: DiscreteNorm does not currently support vmin and
        # vmax different from level list minimum and maximum.
        # NOTE: The level restriction should have no effect if levels were generated
        # automatically. However want to apply these to manual-input levels as well.
        if levels is not None:
            levels = _restrict_levels(levels)
            if len(levels) == 0:  # skip
                pass
            elif len(levels) == 1:  # use central colormap color
                vmin, vmax = levels[0] - 1, levels[0] + 1
            else:  # use minimum and maximum
                vmin, vmax = np.min(levels), np.max(levels)
                if not np.allclose(levels[1] - levels[0], np.diff(levels)):
                    norm = _not_none(norm, "segmented")
            if norm in ("segments", "segmented"):
                norm_kw["levels"] = levels

        return levels, vmin, vmax, norm, norm_kw, kwargs

    @staticmethod
    def _parse_level_norm(
        levels,
        norm,
        cmap,
        *,
        extend=None,
        min_levels=None,
        discrete_ticks=None,
        discrete_labels=None,
        center_levels=None,
        **kwargs,
    ):
        """
        Create a `~ultraplot.colors.DiscreteNorm` or `~ultraplot.colors.BoundaryNorm`
        from the input colormap and normalizer.

        Parameters
        ----------
        levels : sequence of float
            The level boundaries.
        norm : `~matplotlib.colors.Normalize`
            The continuous normalizer.
        cmap : `~matplotlib.colors.Colormap`
            The colormap.
        extend : str, optional
            The extend setting.
        min_levels : int, optional
            The minimum number of levels.
        discrete_ticks : array-like, optional
            The colorbar locations to tick.
        discrete_labels : array-like, optional
            The colorbar tick labels.

        Returns
        -------
        norm : `~ultraplot.colors.DiscreteNorm`
            The discrete normalizer.
        cmap : `~matplotlib.colors.Colormap`
            The possibly-modified colormap.
        kwargs
            Unused arguments.
        """
        # Reverse the colormap if input levels or values were descending
        # See _parse_level_vals for details
        min_levels = _not_none(min_levels, 2)  # 1 for contour plots
        unique = extend = _not_none(extend, "neither")
        under = cmap._rgba_under
        over = cmap._rgba_over
        cyclic = getattr(cmap, "_cyclic", None)
        qualitative = isinstance(cmap, pcolors.DiscreteColormap)  # see _parse_cmap
        if len(levels) < min_levels:
            raise ValueError(
                f"Invalid levels={levels!r}. Must be at least length {min_levels}."
            )

        # Ensure end colors are unique by scaling colors as if extend='both'
        # NOTE: Inside _parse_cmap should have enforced extend='neither'
        if cyclic:
            step = 0.5  # try to allocate space for unique end colors
            unique = "both"

        # Ensure color list length matches level list length using rotation
        # NOTE: No harm if not enough colors, we just end up with the same
        # color for out-of-bounds extensions. This is a gentle failure
        elif qualitative:
            step = 0.5  # try to sample the central index for safety
            unique = "both"
            auto_under = under is None and extend in ("min", "both")
            auto_over = over is None and extend in ("max", "both")
            ncolors = len(levels) - min_levels + 1 + auto_under + auto_over
            colors = list(itertools.islice(itertools.cycle(cmap.colors), ncolors))
            if auto_under and len(colors) > 1:
                under, *colors = colors
            if auto_over and len(colors) > 1:
                *colors, over = colors
            cmap = cmap.copy(colors, N=len(colors))
            if under is not None:
                cmap.set_under(under)
            if over is not None:
                cmap.set_over(over)

        # Ensure middle colors sample full range when extreme colors are present
        # by scaling colors as if extend='neither'
        else:
            step = 1.0
            if over is not None and under is not None:
                unique = "neither"
            elif over is not None:  # turn off over-bounds unique bin
                if extend == "both":
                    unique = "min"
                elif extend == "max":
                    unique = "neither"
            elif under is not None:  # turn off under-bounds unique bin
                if extend == "both":
                    unique = "min"
                elif extend == "max":
                    unique = "neither"

        # Generate DiscreteNorm and update "child" norm with vmin and vmax from
        # levels. This lets the colorbar set tick locations properly!
        center_levels = _not_none(center_levels, rc["colorbar.center_levels"])
        if not isinstance(norm, mcolors.BoundaryNorm) and len(levels) > 1:
            norm = pcolors.DiscreteNorm(
                levels,
                norm=norm,
                unique=unique,
                step=step,
                ticks=discrete_ticks,
                labels=discrete_labels,
            )
        return norm, cmap, kwargs

    def _apply_plot(self, *pairs, vert=True, **kwargs):
        """
        Plot standard lines.
        """
        # Plot the lines
        objs, xsides = [], []
        kws = kwargs.copy()
        kws.update(_pop_props(kws, "line"))
        kws, extents = self._inbounds_extent(**kws)
        for xs, ys, fmt in self._iter_arg_pairs(*pairs):
            xs, ys, kw = self._parse_1d_args(xs, ys, vert=vert, **kws)
            ys, kw = inputs._dist_reduce(ys, **kw)
            guide_kw = _pop_params(kw, self._update_guide)  # after standardize
            for _, n, x, y, kw in self._iter_arg_cols(xs, ys, **kw):
                kw = self._parse_cycle(n, **kw)
                *eb, kw = self._add_error_bars(
                    x, y, vert=vert, default_barstds=True, **kw
                )  # noqa: E501
                *es, kw = self._add_error_shading(x, y, vert=vert, **kw)
                xsides.append(x)
                if not vert:
                    x, y = y, x
                a = [x, y]
                if fmt is not None:  # x1, y1, fmt1, x2, y2, fm2... style input
                    a.append(fmt)
                (obj,) = self._call_native("plot", *a, **kw)
                self._inbounds_xylim(extents, x, y)
                objs.append((*eb, *es, obj) if eb or es else obj)

        # Add sticky edges
        self._fix_sticky_edges(objs, "x" if vert else "y", *xsides, only=mlines.Line2D)
        self._update_guide(objs, **guide_kw)
        return cbook.silent_list("Line2D", objs)  # always return list

    @docstring._snippet_manager
    def line(self, *args, **kwargs):
        """
        %(plot.plot)s
        """
        return self.plot(*args, **kwargs)

    @docstring._snippet_manager
    def linex(self, *args, **kwargs):
        """
        %(plot.plotx)s
        """
        return self.plotx(*args, **kwargs)

    def _apply_lollipop(
        self,
        xs,
        hs,
        ws,
        bs,
        *,
        horizontal=False,
        **kwargs,
    ):
        """
        Lollipop graphs are an alternative way to visualize bar charts. We can utilize the bar internal mechanics to generate the charts and then replace the look with the lollipop graphs
        """

        # Filter the props for the stem and marker out
        stemcolor = kwargs.pop("stemcolor", rc["lollipop.stemcolor"])
        stemwidth = units(kwargs.pop("stemwidth", rc["lollipop.stemwidth"]))
        stemlinestyle = kwargs.pop("stemstyle", rc["lollipop.stemlinestyle"])

        # For the markers we can filter out all the props
        marker_props = _pop_props(kwargs, "collection")

        if horizontal:
            bars = self.barh(xs, hs, ws, bs, **kwargs)
        else:
            bars = self.bar(xs, hs, ws, bs, **kwargs)

        xmin = np.inf
        xmax = -np.inf
        all_lines = []
        patch_collection = []

        # If we have a singular (non-grouped) data
        # we have to wrap the container in a list
        if isinstance(bars, mcontainer.BarContainer):
            bars = [bars]

        for bar in bars:
            xy = np.zeros((len(bar.patches), 2))
            for idx, patch in enumerate(bar.patches):
                patch.set_visible(False)
                color = patch.get_facecolor()

                x0, y0 = patch.xy
                if horizontal:
                    x, y = bar.datavalues[idx], y0
                    y += 0.5 * patch.get_height()
                    all_lines.append([(0, y), (x, y)])
                else:
                    x, y = x0, bar.datavalues[idx]
                    x += 0.5 * patch.get_width()
                    all_lines.append([(x, 0), (x, y)])
                xy[idx] = x, y

                pos = y if horizontal else x
                if pos < xmin:
                    xmin = pos
                if pos > xmax:
                    xmax = pos
            color = bar.patches[0].get_facecolor()
            bar_patch = self.scatter(*xy.T, color=color, **marker_props)
            patch_collection.append(bar_patch)

        line_collection = mcollections.LineCollection(
            all_lines,
            colors=stemcolor,
            linestyles=stemlinestyle,
            lw=stemwidth,
            zorder=bar.patches[0].zorder - 1,
        )
        self.add_collection(line_collection)

        # Add some padding to make it look nicer
        pad = 0
        if horizontal:
            max_height = max(
                patch.get_height() for bar in bars for patch in bar.patches
            )
            pad = 2 * max_height
        else:
            max_width = max(patch.get_width() for bar in bars for patch in bar.patches)
            pad = 2 * max_width

        if horizontal:
            self.set_ylim(xmin - pad, xmax + pad)
        else:
            self.set_xlim(xmin - pad, xmax + pad)

        return patch_collection, line_collection

    @docstring._snippet_manager
    def beeswarm(self, *args, color_values=None, color_by_feature=None, **kwargs):
        """
        %(plot.beeswarm)s

        Parameters
        ----------
        color_values : array-like, optional
            Values to use for coloring points. Should match the shape of the data.
            Enables SHAP-style feature value coloring.
        color_by_feature : array-like, optional
            Alias for color_values. Values to color points by (e.g., feature values).
        """
        # Allow orientation to be overridden in kwargs
        orientation = kwargs.pop("orientation", "horizontal")
        return self._apply_beeswarm(
            *args,
            orientation=orientation,
            color_values=color_values,
            color_by_feature=color_by_feature,
            **kwargs,
        )

    @inputs._preprocess_or_redirect("x", "y", allow_extra=True)
    def _apply_beeswarm(
        self,
        x: np.ndarray,
        y: np.ndarray,
        orientation: str = "horizontal",
        n_iter: int = 50,
        *args,
        **kwargs,
    ) -> "Collection":

        cmap = kwargs.pop("cmap", rc["cmap.diverging"])
        size = kwargs.pop("s", kwargs.pop("size", 20))  # Default marker size
        colorbar = kwargs.pop("colorbar", False)
        colorbar_kw = kwargs.pop("colorbar_kw", {})

        # Feature value coloring support (SHAP-style)
        color_values = kwargs.pop("color_values", None)
        color_by_feature = kwargs.pop("color_by_feature", None)
        if color_by_feature is not None:
            color_values = color_by_feature  # Alias for SHAP-style naming

        # Convert to numpy arrays
        x = np.asarray(x)
        y = np.asarray(y)

        # Handle 2D y array (multiple series)
        if y.ndim == 2:
            # x should be 1D with length matching y.shape[1]
            if x.shape[-1] != y.shape[1]:
                raise ValueError(
                    "For 2D y array, x must be 1D with length matching y.shape[1]"
                )

            # Flatten y and repeat x for each series
            n_series, n_points = y.shape
            x_flat = x.flatten()
            if x.ndim == 1:
                x_flat = np.tile(x, n_series)

            y_flat = y.flatten()

            # Handle color values for 2D case
            if color_values is not None:
                color_values = np.asarray(color_values)
                if color_values.shape == y.shape:
                    # Color values match y shape - flatten them
                    color_flat = color_values.flatten()
                elif len(color_values) == len(y_flat):
                    # Already flattened
                    color_flat = color_values
                else:
                    raise ValueError(
                        "color_values must match the shape of y or be flattened to match flattened y"
                    )
            else:
                # Create series labels for coloring when no color_values provided
                color_flat = np.repeat(np.arange(n_series), n_points)
        else:
            # Standard 1D case
            x_flat = x.flatten()
            y_flat = y.flatten()

            # Handle color values for 1D case
            if color_values is not None:
                color_values = np.asarray(color_values).flatten()
                if len(color_values) != len(y_flat):
                    raise ValueError("color_values must have the same length as y")
                color_flat = color_values
            else:
                color_flat = np.zeros(len(x_flat))

        if len(x_flat) != len(y_flat):
            raise ValueError("x and y must have compatible dimensions")

        # Group data by unique x values (categories)
        unique_x = np.unique(x_flat)
        swarm_x = np.zeros_like(x_flat, dtype=float)
        swarm_y = np.zeros_like(y_flat, dtype=float)

        # Calculate point radius from marker size (approximate)
        # Marker size is in points^2, so radius is sqrt(size/pi)
        point_radius = np.sqrt(size / np.pi) * 0.01  # Scale factor for data units

        for i, cat_x in enumerate(unique_x):
            # Get indices for this category
            mask = x_flat == cat_x
            cat_y = y_flat[mask]
            n_points = len(cat_y)

            if n_points == 0:
                continue

            # Sort by y-value to process from bottom to top
            sorted_indices = np.argsort(cat_y)
            sorted_y = cat_y[sorted_indices]

            # Initialize positions
            positions = []

            for j, y_val in enumerate(sorted_y):
                # Try to place point at category center first
                best_x = cat_x
                best_collision = True

                # Check for collisions with existing points
                for attempt in range(
                    n_iter
                ):  # Max attempts to find non-overlapping position
                    collision = False

                    for pos_x, pos_y in positions:
                        # Calculate distance between points
                        dx = best_x - pos_x
                        dy = y_val - pos_y
                        distance = np.sqrt(dx**2 + dy**2)

                        # Check if points would overlap
                        if distance < 2 * point_radius:
                            collision = True
                            break

                    if not collision:
                        best_collision = False
                        break

                    # If collision, try moving horizontally
                    # Alternate between left and right, increasing distance
                    side = 1 if attempt % 2 == 0 else -1
                    offset = (attempt // 2 + 1) * point_radius * 0.5
                    best_x = cat_x + side * offset

                # Store the final position
                positions.append((best_x, y_val))

                # Map back to original indices
                original_idx = np.where(mask)[0][sorted_indices[j]]
                swarm_x[original_idx] = best_x
                swarm_y[original_idx] = y_val

        # Handle orientation
        if orientation == "horizontal":
            plot_x, plot_y = swarm_y, swarm_x
        else:  # vertical
            plot_x, plot_y = swarm_x, swarm_y

        # Create the scatter plot with appropriate coloring
        guide_kw = _pop_params(kwargs, self._update_guide)
        if "c" not in kwargs and "color" not in kwargs:
            # Use our computed color values (either feature values or series labels)
            objs = self.scatter(
                plot_x, plot_y, s=size, c=color_flat, cmap=cmap, **kwargs
            )
        else:
            # User provided explicit colors
            objs = self.scatter(plot_x, plot_y, s=size, **kwargs)

        self._update_guide(objs, queue_colorbar=False, **guide_kw)
        if colorbar:
            self.colorbar(objs, loc=colorbar, **colorbar_kw)
        return objs

    @inputs._preprocess_or_redirect("x", "height", "width", "bottom")
    @docstring._snippet_manager
    def lollipop(self, *args, **kwargs):
        """
        %(plot.lollipop)s
        """
        return self._apply_lollipop(*args, horizontal=False, **kwargs)

    @inputs._preprocess_or_redirect("x", "height", "width", "bottom")
    @docstring._snippet_manager
    def lollipoph(self, *args, **kwargs):
        """
        %(plot.lollipop)s (horizontal lollipop)
        """
        return self._apply_lollipop(*args, horizontal=True, **kwargs)

    @docstring._snippet_manager
    def loglog(self, *args, **kwargs):
        """
        %(plot.loglog)s
        """
        objs = self._call_native("loglog", *args, **kwargs)
        if rc["formatter.log"]:
            self.format(
                xformatter="log",
                yformatter="log",
            )
        return objs

    @docstring._snippet_manager
    def semilogy(self, *args, **kwargs):
        """
        %(plot.semilogy)s
        """

        objs = self._call_native("semilogy", *args, **kwargs)
        if rc["formatter.log"]:
            self.format(
                yformatter="log",
            )
        return objs

    @docstring._snippet_manager
    def semilogx(self, *args, **kwargs):
        """
        %(plot.semilogx)s
        """
        objs = self._call_native("semilogx", *args, **kwargs)
        if rc["formatter.log"]:
            self.format(
                xformatter="log",
            )
        return objs

    @inputs._preprocess_or_redirect("x", "y", allow_extra=True)
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def plot(self, *args, **kwargs):
        """
        %(plot.plot)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_plot(*args, **kwargs)

    @inputs._preprocess_or_redirect("y", "x", allow_extra=True)
    @docstring._snippet_manager
    def plotx(self, *args, **kwargs):
        """
        %(plot.plotx)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_plot(*args, **kwargs)

    def _apply_step(self, *pairs, vert=True, where="pre", **kwargs):
        """
        Plot the steps.
        """
        # Plot the steps
        # NOTE: Internally matplotlib plot() calls step() so we could use that
        # approach... but instead repeat _apply_plot internals here so we can
        # disable error indications that make no sense for 'step' plots.
        kws = kwargs.copy()
        opts = ("pre", "post", "mid")
        if where not in opts:
            raise ValueError(f"Invalid where={where!r}. Options are {opts!r}.")
        kws.update(_pop_props(kws, "line"))
        kws.setdefault("drawstyle", "steps-" + where)
        kws, extents = self._inbounds_extent(**kws)
        objs = []
        for xs, ys, fmt in self._iter_arg_pairs(*pairs):
            xs, ys, kw = self._parse_1d_args(xs, ys, vert=vert, **kws)
            guide_kw = _pop_params(kw, self._update_guide)  # after standardize
            if fmt is not None:
                kw["fmt"] = fmt
            for _, n, x, y, *a, kw in self._iter_arg_cols(xs, ys, **kw):
                kw = self._parse_cycle(n, **kw)
                if not vert:
                    x, y = y, x
                (obj,) = self._call_native("step", x, y, *a, **kw)
                self._inbounds_xylim(extents, x, y)
                objs.append(obj)

        self._update_guide(objs, **guide_kw)
        return cbook.silent_list("Line2D", objs)  # always return list

    @inputs._preprocess_or_redirect("x", "y", allow_extra=True)
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def step(self, *args, **kwargs):
        """
        %(plot.step)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_step(*args, **kwargs)

    @inputs._preprocess_or_redirect("y", "x", allow_extra=True)
    @docstring._snippet_manager
    def stepx(self, *args, **kwargs):
        """
        %(plot.stepx)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_step(*args, **kwargs)

    def _apply_stem(
        self,
        x,
        y,
        *,
        linefmt=None,
        markerfmt=None,
        basefmt=None,
        orientation=None,
        **kwargs,
    ):
        """
        Plot stem lines and markers.
        """
        # Parse input
        kw = kwargs.copy()
        kw, extents = self._inbounds_extent(**kw)
        x, y, kw = self._parse_1d_args(x, y, **kw)
        guide_kw = _pop_params(kw, self._update_guide)

        # Set default colors
        # NOTE: 'fmt' strings can only be 2 to 3 characters and include color
        # shorthands like 'r' or cycle colors like 'C0'. Cannot use full color names.
        # NOTE: Matplotlib defaults try to make a 'reddish' color the base and 'bluish'
        # color the stems. To make this more robust we temporarily replace the cycler.
        # Bizarrely stem() only reads from the global cycler() so have to update it.
        fmts = (linefmt, basefmt, markerfmt)
        orientation = _not_none(orientation, "vertical")
        if not any(isinstance(fmt, str) and re.match(r"\AC[0-9]", fmt) for fmt in fmts):
            cycle = constructor.Cycle((rc["negcolor"], rc["poscolor"]), name="_no_name")
            kw.setdefault("cycle", cycle)
        kw["basefmt"] = _not_none(basefmt, "C1-")  # red base
        kw["linefmt"] = linefmt = _not_none(linefmt, "C0-")  # blue stems
        kw["markerfmt"] = _not_none(markerfmt, linefmt[:-1] + "o")  # blue marker
        sig = inspect.signature(maxes.Axes.stem)
        if "use_line_collection" in sig.parameters:
            kw.setdefault("use_line_collection", True)

        # Call function then restore property cycle
        # WARNING: Horizontal stem plots are only supported in recent versions of
        # matplotlib. Let matplotlib raise an error if need be.
        ctx = {}
        cycle, kw = self._parse_cycle(return_cycle=True, **kw)  # allow re-application
        if cycle is not None:
            ctx["axes.prop_cycle"] = cycle
        if orientation == "horizontal":  # may raise error
            kw["orientation"] = orientation
        with rc.context(ctx):
            obj = self._call_native("stem", x, y, **kw)
        self._inbounds_xylim(extents, x, y, orientation=orientation)
        self._update_guide(obj, **guide_kw)
        return obj

    @inputs._preprocess_or_redirect("x", "y")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def stem(self, *args, **kwargs):
        """
        %(plot.stem)s
        """
        kwargs = _parse_vert(default_orientation="vertical", **kwargs)
        return self._apply_stem(*args, **kwargs)

    @inputs._preprocess_or_redirect("x", "y")
    @docstring._snippet_manager
    def stemx(self, *args, **kwargs):
        """
        %(plot.stemx)s
        """
        kwargs = _parse_vert(default_orientation="horizontal", **kwargs)
        return self._apply_stem(*args, **kwargs)

    @inputs._preprocess_or_redirect("x", "y", ("c", "color", "colors", "values"))
    @docstring._snippet_manager
    def parametric(self, x, y, c, *, interp=0, scalex=True, scaley=True, **kwargs):
        """
        %(plot.parametric)s
        """
        # Standardize arguments
        # NOTE: Values are inferred in _auto_format() the same way legend labels are
        # inferred. Will not always return an array like inferred coordinates do.
        # NOTE: We want to be able to think of 'c' as a scatter color array and
        # as a colormap color list. Try to support that here.
        kw = kwargs.copy()
        kw.update(_pop_props(kw, "collection"))
        kw, extents = self._inbounds_extent(**kw)
        label = _not_none(**{key: kw.pop(key, None) for key in ("label", "value")})
        x, y, kw = self._parse_1d_args(
            x, y, values=c, autovalues=True, autoreverse=False, **kw
        )
        c = kw.pop("values", None)  # permits auto-inferring values
        c = np.arange(y.size) if c is None else inputs._to_numpy_array(c)
        if (
            c.size in (3, 4)
            and y.size not in (3, 4)
            and mcolors.is_color_like(tuple(c.flat))
            or all(map(mcolors.is_color_like, c))
        ):
            c, kw["colors"] = np.arange(c.shape[0]), c  # convert color specs

        # Interpret color values
        # NOTE: This permits string label input for 'values'
        c, guide_kw = inputs._meta_coords(c, which="")  # convert string labels
        if c.size == 1 and y.size != 1:
            c = np.arange(y.size)  # convert dummy label for single color
        if guide_kw:
            guides._add_guide_kw("colorbar", kw, **guide_kw)
        else:
            guides._add_guide_kw("colorbar", kw, locator=c)

        # Interpolate values to allow for smooth gradations between values or just
        # to color siwtchover halfway between points (interp True, False respectively)
        if interp > 0:
            x_orig, y_orig, v_orig = x, y, c
            x, y, c = [], [], []
            for j in range(x_orig.shape[0] - 1):
                idx = slice(None)
                if j + 1 < x_orig.shape[0] - 1:
                    idx = slice(None, -1)
                x.extend(np.linspace(x_orig[j], x_orig[j + 1], interp + 2)[idx].flat)
                y.extend(np.linspace(y_orig[j], y_orig[j + 1], interp + 2)[idx].flat)
                c.extend(np.linspace(v_orig[j], v_orig[j + 1], interp + 2)[idx].flat)
            x, y, c = np.array(x), np.array(y), np.array(c)

        # Get coordinates and values for points to the 'left' and 'right' of joints
        coords = []
        for i in range(y.shape[0]):
            icoords = np.empty((3, 2))
            for j, arr in enumerate((x, y)):
                icoords[:, j] = (
                    arr[0] if i == 0 else 0.5 * (arr[i - 1] + arr[i]),
                    arr[i],
                    arr[-1] if i + 1 == y.shape[0] else 0.5 * (arr[i + 1] + arr[i]),
                )
            coords.append(icoords)
        coords = np.array(coords)

        # Get the colormap accounting for 'discrete' mode
        discrete = kw.get("discrete", None)
        if discrete is not None and not discrete:
            a = (x, y, c)  # pick levels from vmin and vmax, possibly limiting range
        else:
            a, kw["values"] = (), c
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(*a, center_levels=center_levels, plot_lines=True, **kw)
        cmap, norm = kw.pop("cmap"), kw.pop("norm")

        # Add collection with some custom attributes
        # NOTE: Modern API uses self._request_autoscale_view but this is
        # backwards compatible to earliest matplotlib versions.
        guide_kw = _pop_params(kw, self._update_guide)
        obj = mcollections.LineCollection(
            coords,
            cmap=cmap,
            norm=norm,
            label=label,
            linestyles="-",
            capstyle="butt",
            joinstyle="miter",
        )
        obj.set_array(c)  # the ScalarMappable method
        obj.update({key: value for key, value in kw.items() if key not in ("color",)})
        self.add_collection(obj)  # also adjusts label
        self.autoscale_view(scalex=scalex, scaley=scaley)
        self._update_guide(obj, **guide_kw)
        return obj

    def _apply_lines(
        self,
        xs,
        ys1,
        ys2,
        colors,
        *,
        vert=True,
        stack=None,
        stacked=None,
        negpos=False,
        **kwargs,
    ):
        """
        Plot vertical or hotizontal lines at each point.
        """
        # Parse input arguments
        kw = kwargs.copy()
        name = "vlines" if vert else "hlines"
        if colors is not None:
            kw["colors"] = colors
        kw.update(_pop_props(kw, "collection"))
        kw, extents = self._inbounds_extent(**kw)
        stack = _not_none(stack=stack, stacked=stacked)
        xs, ys1, ys2, kw = self._parse_1d_args(xs, ys1, ys2, vert=vert, **kw)
        guide_kw = _pop_params(kw, self._update_guide)

        # Support "negative" and "positive" lines
        # TODO: Ensure 'linewidths' etc. are applied! For some reason
        # previously thought they had to be manually applied.
        y0 = 0
        objs, sides = [], []
        for _, n, x, y1, y2, kw in self._iter_arg_cols(xs, ys1, ys2, **kw):
            kw = self._parse_cycle(n, **kw)
            if stack:
                y1 = y1 + y0  # avoid in-place modification
                y2 = y2 + y0
                y0 = y0 + y2 - y1  # irrelevant that we added y0 to both
            if negpos:
                obj = self._call_negpos(name, x, y1, y2, colorkey="colors", **kw)
            else:
                obj = self._call_native(name, x, y1, y2, **kw)
            for y in (y1, y2):
                self._inbounds_xylim(extents, x, y, vert=vert)
                if y.size == 1:  # add sticky edges if bounds are scalar
                    sides.append(y)
            objs.append(obj)

        # Draw guide and add sticky edges
        self._fix_sticky_edges(objs, "y" if vert else "x", *sides)
        self._update_guide(objs, **guide_kw)
        return objs[0] if len(objs) == 1 else cbook.silent_list("LineCollection", objs)

    # WARNING: breaking change from native 'ymin' and 'ymax'
    @inputs._preprocess_or_redirect("x", "y1", "y2", ("c", "color", "colors"))
    @docstring._snippet_manager
    def vlines(self, *args, **kwargs):
        """
        %(plot.vlines)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_lines(*args, **kwargs)

    # WARNING: breaking change from native 'xmin' and 'xmax'
    @inputs._preprocess_or_redirect("y", "x1", "x2", ("c", "color", "colors"))
    @docstring._snippet_manager
    def hlines(self, *args, **kwargs):
        """
        %(plot.hlines)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_lines(*args, **kwargs)

    def _parse_markersize(
        self, s, *, smin=None, smax=None, area_size=True, absolute_size=None, **kwargs
    ):
        """
        Scale the marker sizes with optional keyword args.
        """
        if s is not None:
            s = inputs._to_numpy_array(s)
            if absolute_size is None:
                absolute_size = s.size == 1 or _inside_seaborn_call()
            if not absolute_size or smin is not None or smax is not None:
                smin = _not_none(smin, 1)
                smax = _not_none(smax, rc["lines.markersize"] ** (1, 2)[area_size])
                dmin, dmax = inputs._safe_range(s)  # data value range
                if dmin is not None and dmax is not None and dmin != dmax:
                    s = smin + (smax - smin) * (s - dmin) / (dmax - dmin)
            s = s ** (2, 1)[area_size]
        return s, kwargs

    def _apply_scatter(self, xs, ys, ss, cc, *, vert=True, **kwargs):
        """
        Apply scatter or scatterx markers.
        """
        # Manual property cycling. Converts Line2D keywords used in property
        # cycle to PathCollection keywords that can be passed to scatter.
        # NOTE: Matplotlib uses the property cycler in _get_patches_for_fill for
        # scatter() plots. It only ever inherits color from that. We instead use
        # _get_lines to help overarching goal of unifying plot() and scatter().
        cycle_manually = {
            "alpha": "alpha",
            "color": "c",
            "markerfacecolor": "c",
            "markeredgecolor": "edgecolors",
            "marker": "marker",
            "markersize": "s",
            "markeredgewidth": "linewidths",
            "linestyle": "linestyles",
            "linewidth": "linewidths",
        }

        kw = kwargs.copy()
        inbounds = kw.pop("inbounds", None)
        kw.update(_pop_props(kw, "collection"))
        kw, extents = self._inbounds_extent(inbounds=inbounds, **kw)
        xs, ys, kw = self._parse_1d_args(xs, ys, vert=vert, autoreverse=False, **kw)
        ys, kw = inputs._dist_reduce(ys, **kw)
        ss, kw = self._parse_markersize(ss, **kw)  # parse 's'

        # Only parse color if explicitly provided
        infer_rgb = True
        if cc is not None:
            if not isinstance(cc, str):
                test = np.atleast_1d(cc)
                if (
                    any(_.ndim == 2 and _.shape[1] in (3, 4) for _ in (xs, ys))
                    and test.ndim == 2
                    and test.shape[1] in (3, 4)
                ):
                    infer_rgb = False
            cc, kw = self._parse_color(
                xs,
                ys,
                cc,
                inbounds=inbounds,
                apply_cycle=False,
                infer_rgb=infer_rgb,
                **kw,
            )
        # Create the cycler object by manually cycling and sanitzing the inputs
        guide_kw = _pop_params(kw, self._update_guide)
        objs = []
        for _, n, x, y, s, c, kw in self._iter_arg_cols(xs, ys, ss, cc, **kw):
            # Cycle s and c as they are in cycle_manually
            # Note: they could be None
            kw["s"], kw["c"] = s, c
            kw = self._parse_cycle(n, cycle_manually=cycle_manually, **kw)
            *eb, kw = self._add_error_bars(x, y, vert=vert, default_barstds=True, **kw)
            *es, kw = self._add_error_shading(x, y, vert=vert, color_key="c", **kw)
            if not vert:
                x, y = y, x
            obj = self._call_native("scatter", x, y, **kw)
            self._inbounds_xylim(extents, x, y)
            objs.append((*eb, *es, obj) if eb or es else obj)

        self._update_guide(objs, queue_colorbar=False, **guide_kw)
        return objs[0] if len(objs) == 1 else cbook.silent_list("PathCollection", objs)

    # NOTE: Matplotlib internally applies scatter 'c' arguments as the
    # 'facecolors' argument to PathCollection. So perfectly reasonable to
    # point both 'color' and 'facecolor' arguments to the 'c' keyword here.
    @inputs._preprocess_or_redirect(
        "x",
        "y",
        _get_aliases("collection", "sizes"),
        _get_aliases("collection", "colors", "facecolors"),
        keywords=_get_aliases("collection", "linewidths", "edgecolors"),
    )
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def scatter(self, *args, **kwargs):
        """
        %(plot.scatter)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_scatter(*args, **kwargs)

    @inputs._preprocess_or_redirect(
        "y",
        "x",
        _get_aliases("collection", "sizes"),
        _get_aliases("collection", "colors", "facecolors"),
        keywords=_get_aliases("collection", "linewidths", "edgecolors"),
    )
    @docstring._snippet_manager
    def scatterx(self, *args, **kwargs):
        """
        %(plot.scatterx)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_scatter(*args, **kwargs)

    def _apply_fill(
        self,
        xs,
        ys1,
        ys2,
        where,
        *,
        vert=True,
        negpos=None,
        stack=None,
        stacked=None,
        **kwargs,
    ):
        """
        Apply area shading.
        """
        # Parse input arguments
        kw = kwargs.copy()
        kw.update(_pop_props(kw, "patch"))
        kw, extents = self._inbounds_extent(**kw)
        name = "fill_between" if vert else "fill_betweenx"
        stack = _not_none(stack=stack, stacked=stacked)
        xs, ys1, ys2, kw = self._parse_1d_args(xs, ys1, ys2, vert=vert, **kw)
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)

        # Draw patches with default edge width zero
        y0 = 0
        objs, xsides, ysides = [], [], []
        guide_kw = _pop_params(kw, self._update_guide)
        for _, n, x, y1, y2, w, kw in self._iter_arg_cols(xs, ys1, ys2, where, **kw):
            kw = self._parse_cycle(n, **kw)
            if stack:
                y1 = y1 + y0  # avoid in-place modification
                y2 = y2 + y0
                y0 = y0 + y2 - y1  # irrelevant that we added y0 to both
            if negpos:  # NOTE: if user passes 'where' will issue a warning
                obj = self._call_negpos(name, x, y1, y2, where=w, use_where=True, **kw)
            else:
                obj = self._call_native(name, x, y1, y2, where=w, **kw)
            self._fix_patch_edges(obj, **edgefix_kw, **kw)
            xsides.append(x)
            for y in (y1, y2):
                self._inbounds_xylim(extents, x, y, vert=vert)
                if y.size == 1:  # add sticky edges if bounds are scalar
                    ysides.append(y)
            objs.append(obj)

        # Draw guide and add sticky edges
        self._update_guide(objs, **guide_kw)
        for axis, sides in zip("xy" if vert else "yx", (xsides, ysides)):
            self._fix_sticky_edges(objs, axis, *sides)
        return objs[0] if len(objs) == 1 else cbook.silent_list("PolyCollection", objs)

    @docstring._snippet_manager
    def area(self, *args, **kwargs):
        """
        %(plot.fill_between)s
        """
        return self.fill_between(*args, **kwargs)

    @docstring._snippet_manager
    def areax(self, *args, **kwargs):
        """
        %(plot.fill_betweenx)s
        """
        return self.fill_betweenx(*args, **kwargs)

    @inputs._preprocess_or_redirect("x", "y1", "y2", "where")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def fill_between(self, *args, **kwargs):
        """
        %(plot.fill_between)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_fill(*args, **kwargs)

    @inputs._preprocess_or_redirect("y", "x1", "x2", "where")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def fill_betweenx(self, *args, **kwargs):
        """
        %(plot.fill_betweenx)s
        """
        # NOTE: The 'horizontal' orientation will be inferred by downstream
        # wrappers using the function name.
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_fill(*args, **kwargs)

    @docstring._snippet_manager
    def graph(
        self,
        g: Union["nx.Graph", np.ndarray],
        layout: Union[str, dict, Callable] = None,
        nodes: Union[None, bool, Iterable] = None,
        edges: Union[None, bool, Iterable] = None,
        labels: Union[None, bool, Iterable] = None,
        layout_kw={},
        node_kw={},
        edge_kw={},
        label_kw={},
        rescale: Union[None, bool] = None,
    ):
        """
        %(plot.graph)s
        """
        import networkx as nx

        labels = _not_none(labels, rc["graph.draw_labels"])
        nodes = _not_none(nodes, rc["graph.draw_nodes"])
        edges = _not_none(edges, rc["graph.draw_edges"])
        rescale = _not_none(rescale, rc["graph.rescale"])

        match g:
            case np.ndarray():
                # Check if g is an adjacency matrix
                assert len(g.shape) == 2
                x, y = g.shape[:2]
                if x == y:
                    g = nx.from_numpy_array(g)
                else:
                    # Assume edgelist
                    g = nx.from_edgelist(g)
            case nx.Graph() | nx.DiGraph() | nx.MultiGraph() | nx.MultiDiGraph():
                pass
            case _:
                raise TypeError(f"Unsupported graph type: {type(g)}")

        match layout:
            case str():
                layout_name = (
                    layout if layout.endswith("_layout") else layout + "_layout"
                )
                pos = getattr(nx, layout_name)(g, **layout_kw)
            case layout if isinstance(layout, Callable):
                pos = layout(g, **layout_kw)
            case dict():
                pos = layout
            case _:
                pos = nx.kamada_kawai_layout(g)

        if rescale:
            # Normalize node positions to fit in a [0, 1] x [0, 1] box.

            xs = [x for x, y in pos.values()]
            ys = [y for x, y in pos.values()]

            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            width = max_x - min_x
            height = max_y - min_y
            pos = {
                k: (
                    (x - min_x) / width if width else 0.5,
                    (y - min_y) / height if height else 0.5,
                )
                for k, (x, y) in pos.items()
            }
        # Set a sensible default if not given
        if "node_size" not in node_kw:
            coords = np.array(list(pos.values()))
            xlim = self.get_xlim()
            ylim = self.get_ylim()

            # Size of data space shown
            data_span = np.array([xlim[1] - xlim[0], ylim[1] - ylim[0]])
            axis_bbox = self.get_window_extent().transformed(
                self.figure.dpi_scale_trans.inverted()
            )
            axis_size_inch = np.array([axis_bbox.width, axis_bbox.height])
            dpi = self.figure.dpi
            axis_size_px = axis_size_inch * dpi

            # Convert a fixed pixel diameter  into data units
            desired_px_diameter = 7  # px
            data_units_per_px = data_span / axis_size_px
            data_diameter = np.mean(data_units_per_px) * desired_px_diameter

            # Convert to `node_size` in pt² (as required by nx.draw)
            # 1 point = 1/72 inch → diameter in points = (desired_px / dpi) * 72
            diameter_inch = desired_px_diameter / dpi
            diameter_pt = diameter_inch * 72
            radius_pt = diameter_pt / 2
            node_size = np.pi * radius_pt**2  # area in pt²
            node_kw["node_size"] = node_size

        # By default soften the edge alpha to prevent "hairball " effect
        if "alpha" not in edge_kw:
            n_edges = g.number_of_edges()
            n = g.number_of_nodes()
            # For more edges reduce the alpha for the edges
            alpha = 1 - np.exp(-n_edges / (n - 1))
            edge_kw["alpha"] = max(
                alpha, 0.1
            )  # with a cutt-off to prevent dissapearence for complete graphs

        # Draw the graph using networks functions
        if nodes:
            if np.iterable(nodes):
                node_kw["nodelist"] = nodes
            nodes = nx.draw_networkx_nodes(g, pos=pos, ax=self, **node_kw)
        if edges:
            if np.iterable(edges):
                edge_kw["edgelist"] = edges
            edges = nx.draw_networkx_edges(g, pos=pos, ax=self, **edge_kw)
        if labels:
            if np.iterable(labels):
                label_kw["labels"] = labels
            labels = nx.draw_networkx_labels(g, pos=pos, ax=self, **label_kw)

        # Apply styling
        self.set_aspect(rc["graph.aspect"])
        self.grid(rc["graph.draw_grid"])
        self.set_facecolor(rc["graph.facecolor"])
        self._toggle_spines(rc["graph.draw_spines"])
        return nodes, edges, labels

    @staticmethod
    def _convert_bar_width(x, width=1):
        """
        Convert bar plot widths from relative to coordinate spacing. Relative
        widths are much more convenient for users.
        """
        # WARNING: This will fail for non-numeric non-datetime64 singleton
        # datatypes but this is good enough for vast majority of cases.
        x_test = inputs._to_numpy_array(x)
        if len(x_test) >= 2:
            x_step = x_test[1:] - x_test[:-1]
            x_step = np.concatenate((x_step, x_step[-1:]))
        elif x_test.dtype == np.datetime64:
            x_step = np.timedelta64(1, "D")
        else:
            x_step = np.array(0.5)
        if np.issubdtype(x_test.dtype, np.datetime64):
            # Avoid integer timedelta truncation
            x_step = x_step.astype("timedelta64[ns]")
        return width * x_step

    def _apply_bar(
        self,
        xs,
        hs,
        ws,
        bs,
        *,
        absolute_width=None,
        stack=None,
        stacked=None,
        negpos=False,
        orientation="vertical",
        **kwargs,
    ):
        """
        Apply bar or barh command. Support default "minima" at zero.
        """
        # Parse args
        kw = kwargs.copy()
        kw, extents = self._inbounds_extent(**kw)
        bar_labels = kw.pop("bar_labels", rc["bar.bar_labels"])
        bar_labels_kw = kw.pop("bar_labels_kw", {})
        name = "barh" if orientation == "horizontal" else "bar"
        stack = _not_none(stack=stack, stacked=stacked)
        xs, hs, kw = self._parse_1d_args(xs, hs, orientation=orientation, **kw)
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        if absolute_width is None:
            absolute_width = _inside_seaborn_call()

        # Call func after converting bar width
        b0 = 0
        objs = []
        kw.update(_pop_props(kw, "patch"))
        hs, kw = inputs._dist_reduce(hs, **kw)
        guide_kw = _pop_params(kw, self._update_guide)
        alphas = kw.pop("alpha", None)

        # We apply alphas over the columns
        ncols = hs.shape[-1]
        if alphas is None:
            alphas = ncols * [None]
        elif isinstance(alphas, Number):
            alphas = ncols * [alphas]
        elif len(alphas) != ncols:
            raise ValueError(
                f"Received {len(alphas)} values for alpha but needed {ncols}"
            )
        for i, n, x, h, w, b, kw in self._iter_arg_cols(xs, hs, ws, bs, **kw):
            kw = self._parse_cycle(n, **kw)
            # Adjust x or y coordinates for grouped and stacked bars
            w = _not_none(w, np.array([0.8]))  # same as mpl but in *relative* units
            b = _not_none(b, np.array([0.0]))  # same as mpl
            if not absolute_width:
                w = self._convert_bar_width(x, w)
            if stack:
                b = b + b0
                b0 = b0 + h
            else:  # instead "group" the bars (this is no-op if we have 1 column)
                w = w / n  # rescaled
                o = 0.5 * (n - 1)  # center coordinate
                x = x + w * (i - o)  # += may cause integer/float casting issue
            # Draw simple bars
            *eb, kw = self._add_error_bars(
                x, b + h, default_barstds=True, orientation=orientation, **kw
            )  # noqa: E501
            if negpos:
                obj = self._call_negpos(name, x, h, w, b, use_zero=True, **kw)
            else:
                obj = self._call_native(name, x, h, w, b, **kw)
            if bar_labels:
                if isinstance(obj, mcontainer.BarContainer):
                    self._add_bar_labels(obj, orientation=orientation, **bar_labels_kw)

            self._fix_patch_edges(obj, **edgefix_kw, **kw)
            for y in (b, b + h):
                self._inbounds_xylim(extents, x, y, orientation=orientation)

            if alphas[i] is not None:
                for child in obj.get_children():
                    child.set_alpha(alphas[i])
            objs.append((*eb, obj) if eb else obj)

        self._update_guide(objs, **guide_kw)
        return objs[0] if len(objs) == 1 else cbook.silent_list("BarContainer", objs)

    def _add_bar_labels(
        self,
        container,
        *,
        orientation="horizontal",
        **kwargs,
    ):
        """
        Automatically add bar labels and rescale the
        limits to produce a striking visual image.
        """
        # Drawing the labels does not rescale the limits to account
        # for the labels. We therefore first draw them and then
        # adjust the range for x or y depending on the orientation of the bar
        bar_labels = self._call_native("bar_label", container, **kwargs)

        which = "x" if orientation == "horizontal" else "y"
        other_which = "y" if orientation == "horizontal" else "x"

        # Get current limits
        current_lim = getattr(self, f"get_{which}lim")()
        other_lim = getattr(self, f"get_{other_which}lim")()

        # Find the maximum extent of text + bar position
        max_extent = current_lim[1]  # Start with current upper limit

        for label, bar in zip(bar_labels, container):
            # Get text bounding box
            bbox = label.get_window_extent(renderer=self.figure.canvas.get_renderer())
            bbox_data = bbox.transformed(self.transData.inverted())

            if orientation == "horizontal":
                # For horizontal bars, check if text extends beyond right edge
                bar_end = bar.get_width() + bar.get_x()
                text_end = bar_end + bbox_data.width
                max_extent = max(max_extent, text_end)
            else:
                # For vertical bars, check if text extends beyond top edge
                bar_end = bar.get_height() + bar.get_y()
                text_end = bar_end + bbox_data.height
                max_extent = max(max_extent, text_end)

        # Only adjust limits if text extends beyond current range
        if max_extent > current_lim[1]:
            padding = (max_extent - current_lim[1]) * 1.25  # Add a bit of padding
            new_lim = (current_lim[0], max_extent + padding)
            getattr(self, f"set_{which}lim")(new_lim)

        # Keep the other axis unchanged
        getattr(self, f"set_{other_which}lim")(other_lim)

        return bar_labels

    @inputs._preprocess_or_redirect("x", "height", "width", "bottom")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def bar(self, *args, **kwargs):
        """
        %(plot.bar)s
        """
        kwargs = _parse_vert(default_orientation="vertical", **kwargs)
        return self._apply_bar(*args, **kwargs)

    # WARNING: Swap 'height' and 'width' here so that they are always relative
    # to the 'tall' axis. This lets people always pass 'width' as keyword
    @inputs._preprocess_or_redirect("y", "height", "width", "left")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def barh(self, *args, **kwargs):
        """
        %(plot.barh)s
        """
        kwargs = _parse_vert(default_orientation="horizontal", **kwargs)
        return self._apply_bar(*args, **kwargs)

    # WARNING: 'labels' and 'colors' no longer passed through `data` (seems like
    # extremely niche usage... `data` variables should be data-like)
    @inputs._preprocess_or_redirect("x", "explode")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def pie(self, x, explode, *, labelpad=None, labeldistance=None, **kwargs):
        """
        %(plot.pie)s
        """
        kw = kwargs.copy()
        pad = _not_none(labeldistance=labeldistance, labelpad=labelpad, default=1.15)
        wedge_kw = kw.pop("wedgeprops", None) or {}
        wedge_kw.update(_pop_props(kw, "patch"))
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        _, x, kw = self._parse_1d_args(
            x, autox=False, autoy=False, autoreverse=False, **kw
        )
        kw = self._parse_cycle(x.size, **kw)
        objs = self._call_native(
            "pie", x, explode=explode, labeldistance=pad, wedgeprops=wedge_kw, **kw
        )
        objs = tuple(cbook.silent_list(type(seq[0]).__name__, seq) for seq in objs)
        self._fix_patch_edges(objs[0], **edgefix_kw, **wedge_kw)
        return objs

    @staticmethod
    def _parse_box_violin(fillcolor, fillalpha, edgecolor, **kw):
        """
        Parse common boxplot and violinplot arguments.
        """
        if isinstance(fillcolor, list):
            warnings._warn_ultraplot(
                "Passing lists to fillcolor was deprecated in v0.9. Please use "
                f"the property cycler with e.g. cycle={fillcolor!r} instead."
            )
            kw["cycle"] = _not_none(cycle=kw.get("cycle", None), fillcolor=fillcolor)
            fillcolor = None
        if isinstance(fillalpha, list):
            warnings._warn_ultraplot(
                "Passing lists to fillalpha was removed in v0.9. Please specify "
                "different opacities using the property cycle colors instead."
            )
            fillalpha = fillalpha[0]  # too complicated to try to apply this
        if isinstance(edgecolor, list):
            warnings._warn_ultraplot(
                "Passing lists of edgecolors was removed in v0.9. Please call the "
                "plotting command multiple times with different edge colors instead."
            )
            edgecolor = edgecolor[0]
        return fillcolor, fillalpha, edgecolor, kw

    def _apply_boxplot(
        self,
        x,
        y,
        *,
        mean=None,
        means=None,
        vert=True,
        fill=None,
        filled=None,
        marker=None,
        markersize=None,
        **kwargs,
    ):
        """
        Apply the box plot.
        """
        # Global and fill properties
        kw = kwargs.copy()
        kw.update(_pop_props(kw, "patch"))
        fill = _not_none(fill=fill, filled=filled)
        means = _not_none(mean=mean, means=means, showmeans=kw.get("showmeans"))
        linewidth = kw.pop("linewidth", rc["patch.linewidth"])
        edgecolor = kw.pop("edgecolor", "black")
        fillcolor = kw.pop("facecolor", None)
        fillalpha = kw.pop("alpha", None)
        fillcolor, fillalpha, edgecolor, kw = self._parse_box_violin(
            fillcolor, fillalpha, edgecolor, **kw
        )
        if fill is None:
            fill = fillcolor is not None or fillalpha is not None
            fill = fill or kw.get("cycle") is not None

        # Parse non-color properties
        # NOTE: Output dict keys are plural but we use singular for keyword args
        props = {}
        for key in (
            "boxes",
            "whiskers",
            "caps",
            "fliers",
            "medians",
            "means",
            "hatches",
        ):
            prefix = key.rstrip("es")  # singular form
            props[key] = iprops = _pop_props(kw, "line", prefix=prefix)
            iprops.setdefault("color", edgecolor)
            iprops.setdefault("linewidth", linewidth)
            iprops.setdefault("markeredgecolor", edgecolor)

        # Parse color properties
        x, y, kw = self._parse_1d_args(
            x, y, autoy=False, autoguide=False, vert=vert, **kw
        )
        kw = self._parse_cycle(x.size, **kw)  # possibly apply cycle
        if fill and fillcolor is None:
            parser = self._get_patches_for_fill
            fillcolor = [parser.get_next_color() for _ in range(x.size)]
        else:
            fillcolor = [fillcolor] * x.size

        # Plot boxes
        kw.setdefault("positions", x)
        if means:
            kw["showmeans"] = kw["meanline"] = True
        y = inputs._dist_clean(y)
        # Add hatch to props as boxplot does not have a hatch but Rectangle does
        hatch = kw.pop("hatch", None)
        if hatch is None:
            hatch = [None for _ in range(x.size)]

        # TODO(compat) remove this when 3.9 is deprecated
        # Convert vert boolean to orientation string for newer versions
        orientation = "vertical" if vert else "horizontal"

        if version.parse(str(_version_mpl)) >= version.parse("3.10.0"):
            # For matplotlib 3.10+:
            # Use the orientation parameters
            artists = self._call_native("boxplot", y, orientation=orientation, **kw)
        else:
            # For older matplotlib versions:
            # Use vert parameter
            artists = self._call_native("boxplot", y, vert=vert, **kw)

        artists = artists or {}  # necessary?
        artists = {
            key: cbook.silent_list(type(objs[0]).__name__, objs) if objs else objs
            for key, objs in artists.items()
        }

        # Modify artist settings

        for key, aprops in props.items():
            if key not in artists:  # possible if not rendered
                continue
            objs = artists[key]
            for i, obj in enumerate(objs):
                # Update lines used for boxplot components
                # TODO: Test this thoroughly!
                iprops = {
                    key: (
                        value[i // 2 if key in ("caps", "whiskers") else i]
                        if isinstance(value, (list, np.ndarray))
                        else value
                    )
                    for key, value in aprops.items()
                }
                obj.update(iprops)
                # "Filled" boxplot by adding patch beneath line path
                if key == "boxes" and (
                    fillcolor[i] is not None
                    or fillalpha is not None
                    or hatch[i] is not None
                ):
                    patch = mpatches.PathPatch(
                        obj.get_path(),
                        linewidth=0.0,
                        facecolor=fillcolor[i],
                        alpha=fillalpha,
                        hatch=hatch[i],
                    )
                    self.add_artist(patch)
                # Outlier markers
                if key == "fliers":
                    if marker is not None:
                        obj.set_marker(marker)
                    if markersize is not None:
                        obj.set_markersize(markersize)

        return artists

    @docstring._snippet_manager
    def box(self, *args, **kwargs):
        """
        %(plot.boxplot)s
        """
        return self.boxplot(*args, **kwargs)

    @docstring._snippet_manager
    def boxh(self, *args, **kwargs):
        """
        %(plot.boxploth)s
        """
        return self.boxploth(*args, **kwargs)

    @inputs._preprocess_or_redirect("positions", "y")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def boxplot(self, *args, **kwargs):
        """
        %(plot.boxplot)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_boxplot(*args, **kwargs)

    @inputs._preprocess_or_redirect("positions", "x")
    @docstring._snippet_manager
    def boxploth(self, *args, **kwargs):
        """
        %(plot.boxploth)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_boxplot(*args, **kwargs)

    def _apply_violinplot(
        self,
        x,
        y,
        vert=True,
        mean=None,
        means=None,
        median=None,
        medians=None,
        showmeans=None,
        showmedians=None,
        showextrema=None,
        **kwargs,
    ):
        """
        Apply the violinplot.
        """
        # Parse keyword args
        kw = kwargs.copy()
        kw.update(_pop_props(kw, "patch"))
        kw.setdefault("capsize", 0)  # caps are redundant for violin plots
        means = _not_none(mean=mean, means=means, showmeans=showmeans)
        medians = _not_none(median=median, medians=medians, showmedians=showmedians)
        if showextrema:
            kw["default_barpctiles"] = True
            if not means and not medians:
                medians = _not_none(medians, True)
        linewidth = kw.pop("linewidth", None)
        edgecolor = kw.pop("edgecolor", "black")
        fillcolor = kw.pop("facecolor", None)
        fillalpha = kw.pop("alpha", None)
        fillcolor, fillalpha, edgecolor, kw = self._parse_box_violin(
            fillcolor, fillalpha, edgecolor, **kw
        )

        # Parse color properties
        x, y, kw = self._parse_1d_args(
            x, y, autoy=False, autoguide=False, vert=vert, **kw
        )
        kw = self._parse_cycle(x.size, **kw)
        if fillcolor is None:
            parser = self._get_patches_for_fill
            fillcolor = [parser.get_next_color() for _ in range(x.size)]
        else:
            fillcolor = [fillcolor] * x.size

        # Plot violins
        y, kw = inputs._dist_reduce(y, means=means, medians=medians, **kw)
        *eb, kw = self._add_error_bars(
            x, y, vert=vert, default_boxstds=True, default_marker=True, **kw
        )  # noqa: E501
        kw.setdefault("positions", x)  # coordinates passed as keyword
        y = _not_none(kw.pop("distribution"), y)  # i.e. was reduced
        y = inputs._dist_clean(y)

        hatches = None
        if "hatch" in kw:
            hatches = kw.pop("hatch", None)
        if "hatches" in kw:
            hatches = kw.pop("hatches", None)

        if hatches is None:
            hatches = len(y) * [None]
        elif len(hatches) != len(y):
            raise ValueError(f"Retrieved {len(hatches)} hatches but need {len(y)}")

        legend_labels = kw.pop("labels", None)
        if version.parse(str(_version_mpl)) >= version.parse("3.10.0"):
            # For matplotlib 3.10+:
            # Use orientation parameter
            orientation = "vertical" if vert else "horizontal"
            artists = self._call_native(
                "violinplot",
                y,
                orientation=orientation,
                showmeans=False,
                showmedians=False,
                showextrema=False,
                **kw,
            )
        else:
            # For older matplotlib versions:
            # Use vert parameter
            artists = self._call_native(
                "violinplot",
                y,
                vert=vert,  # Use the original vert boolean
                showmeans=False,
                showmedians=False,
                showextrema=False,
                **kw,
            )

        # Modify body settings
        artists = artists or {}  # necessary?
        bodies = artists.pop("bodies", ())  # should be no other entries
        if bodies:
            bodies = cbook.silent_list(type(bodies[0]).__name__, bodies)

        # Pad body names if less available
        if legend_labels is None:
            legend_labels = np.full(len(bodies), None)
        elif len(legend_labels) < len(bodies):
            warnings._warn_ultraplot(
                f"Warning: More bodies ({len(bodies)}) than labels ({len(legend_labels)})"
            )
            for i in range(len(legend_labels), len(bodies)):
                legend_labels = np.append(legend_labels, None)
        for i, body in enumerate(bodies):
            body.set_alpha(1.0)  # change default to 1.0
            if fillcolor[i] is not None:
                body.set_facecolor(fillcolor[i])
            if fillalpha is not None:
                body.set_alpha(fillalpha[i])
            if edgecolor is not None:
                body.set_edgecolor(edgecolor)
            if linewidth is not None:
                body.set_linewidths(linewidth)
            if hatches[i] is not None:
                body.set_hatch(hatches[i])
            if legend_labels[i] is not None:
                body.set_label(legend_labels[i])
        return (bodies, *eb) if eb else bodies

    @docstring._snippet_manager
    def violin(self, *args, **kwargs):
        """
        %(plot.violinplot)s
        """
        # WARNING: This disables use of 'violin' by users but
        # probably very few people use this anyway.
        if getattr(self, "_internal_call", None):
            return super().violin(*args, **kwargs)
        else:
            return self.violinplot(*args, **kwargs)

    @docstring._snippet_manager
    def violinh(self, *args, **kwargs):
        """
        %(plot.violinploth)s
        """
        return self.violinploth(*args, **kwargs)

    @inputs._preprocess_or_redirect("positions", "y")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def violinplot(self, *args, **kwargs):
        """
        %(plot.violinplot)s
        """
        kwargs = _parse_vert(default_vert=True, **kwargs)
        return self._apply_violinplot(*args, **kwargs)

    @inputs._preprocess_or_redirect("positions", "x")
    @docstring._snippet_manager
    def violinploth(self, *args, **kwargs):
        """
        %(plot.violinploth)s
        """
        kwargs = _parse_vert(default_vert=False, **kwargs)
        return self._apply_violinplot(*args, **kwargs)

    def _apply_hist(
        self,
        xs,
        bins,
        *,
        width=None,
        rwidth=None,
        stack=None,
        stacked=None,
        fill=None,
        filled=None,
        histtype=None,
        orientation="vertical",
        **kwargs,
    ):
        """
        Apply the histogram.
        """
        # NOTE: While Axes.bar() adds labels to the container Axes.hist() only
        # adds them to the first elements in the container for each column
        # of the input data. Make sure that legend() will read both containers
        # and individual items inside those containers.
        _, xs, kw = self._parse_1d_args(
            xs, autoreverse=False, orientation=orientation, **kwargs
        )
        fill = _not_none(fill=fill, filled=filled)
        stack = _not_none(stack=stack, stacked=stacked)
        if fill is not None:
            histtype = _not_none(histtype, "stepfilled" if fill else "step")
        if stack is not None:
            histtype = _not_none(histtype, "barstacked" if stack else "bar")
        kw["bins"] = bins
        kw["label"] = kw.pop("labels", None)  # multiple labels are natively supported
        kw["rwidth"] = _not_none(width=width, rwidth=rwidth)  # latter is native
        kw["histtype"] = histtype = _not_none(histtype, "bar")
        kw.update(_pop_props(kw, "patch"))
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        guide_kw = _pop_params(kw, self._update_guide)
        n = xs.shape[1] if xs.ndim > 1 else 1
        kw = self._parse_cycle(n, **kw)
        obj = self._call_native("hist", xs, orientation=orientation, **kw)
        if histtype.startswith("bar"):
            self._fix_patch_edges(obj[2], **edgefix_kw, **kw)
        # Revert to mpl < 3.3 behavior where silent_list was always returned for
        # non-bar-type histograms. Because consistency.
        res = obj[2]
        if type(res) is list:  # 'step' histtype plots
            res = cbook.silent_list("Polygon", res)
            obj = (*obj[:2], res)
        else:
            for i, sub in enumerate(res):
                if type(sub) is list:
                    res[i] = cbook.silent_list("Polygon", sub)
        self._update_guide(res, **guide_kw)
        return obj

    @inputs._preprocess_or_redirect("x", "bins", keywords="weights")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def hist(self, *args, **kwargs):
        """
        %(plot.hist)s
        """
        kwargs = _parse_vert(default_orientation="vertical", **kwargs)
        return self._apply_hist(*args, **kwargs)

    @inputs._preprocess_or_redirect("y", "bins", keywords="weights")
    @docstring._snippet_manager
    def histh(self, *args, **kwargs):
        """
        %(plot.histh)s
        """
        kwargs = _parse_vert(default_orientation="horizontal", **kwargs)
        return self._apply_hist(*args, **kwargs)

    @inputs._preprocess_or_redirect("x", "y", "bins", keywords="weights")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def hist2d(self, x, y, bins, **kwargs):
        """
        %(plot.hist2d)s
        """
        # Rely on the pcolormesh() override for this.
        if bins is not None:
            kwargs["bins"] = bins
        return super().hist2d(x, y, autoreverse=False, default_discrete=False, **kwargs)

    # WARNING: breaking change from native 'C'
    @inputs._preprocess_or_redirect("x", "y", "weights")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def hexbin(self, x, y, weights, **kwargs):
        """
        %(plot.hexbin)s
        """
        # WARNING: Cannot use automatic level generation here until counts are
        # estimated. Inside _parse_level_vals if no manual levels were provided then
        # _parse_level_num is skipped and args like levels=10 or locator=5 are ignored
        kw = kwargs.copy()
        x, y, kw = self._parse_1d_args(x, y, autoreverse=False, autovalues=True, **kw)
        kw.update(_pop_props(kw, "collection"))  # takes LineCollection props
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x,
            y,
            y,
            skip_autolev=True,
            default_discrete=False,
            center_levels=center_levels,
            **kw,
        )
        norm = kw.get("norm", None)
        if norm is not None and not isinstance(norm, pcolors.DiscreteNorm):
            norm.vmin = norm.vmax = None  # remove nonsense values
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        m = self._call_native("hexbin", x, y, weights, **kw)
        self._add_auto_labels(m, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def contour(self, x, y, z, **kwargs):
        """
        %(plot.contour)s
        """
        x, y, z, kw = self._parse_2d_args(x, y, z, **kwargs)
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x,
            y,
            z,
            center_levels=center_levels,
            min_levels=1,
            plot_lines=True,
            plot_contours=True,
            **kw,
        )
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        label = kw.pop("label", None)
        m = self._call_native("contour", x, y, z, **kw)
        m._legend_label = label
        self._add_auto_labels(m, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def contourf(self, x, y, z, **kwargs):
        """
        %(plot.contourf)s
        """
        x, y, z, kw = self._parse_2d_args(x, y, z, **kwargs)
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x, y, z, center_levels=center_levels, plot_contours=True, **kw
        )
        contour_kw = _pop_kwargs(kw, "edgecolors", "linewidths", "linestyles")
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        label = kw.pop("label", None)
        m = cm = self._call_native("contourf", x, y, z, **kw)
        m._legend_label = label
        self._fix_patch_edges(m, **edgefix_kw, **contour_kw)  # no-op if not contour_kw
        if contour_kw or labels_kw:
            cm = self._fix_contour_edges("contour", x, y, z, **kw, **contour_kw)
        self._add_auto_labels(m, cm, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def pcolor(self, x, y, z, **kwargs):
        """
        %(plot.pcolor)s
        """
        x, y, z, kw = self._parse_2d_args(x, y, z, edges=True, **kwargs)
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x, y, z, to_centers=True, center_levels=center_levels, **kw
        )
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        with self._keep_grid_bools():
            m = self._call_native("pcolor", x, y, z, **kw)
        self._fix_patch_edges(m, **edgefix_kw, **kw)
        self._add_auto_labels(m, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def pcolormesh(self, x, y, z, **kwargs):
        """
        %(plot.pcolormesh)s
        """
        to_centers = edges = True
        # For 'nearest' and 'gouraud' shading, Matplotlib's pcolormesh uses the original grid points
        # rather than interpolated values. Therefore, we set to_centers and edges to False.
        if kwargs.get("shading", "").lower() in ("nearest", "gouraud"):
            to_centers = edges = False
        x, y, z, kw = self._parse_2d_args(x, y, z, edges=edges, **kwargs)
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x, y, z, to_centers=to_centers, center_levels=center_levels, **kw
        )
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        with self._keep_grid_bools():
            m = self._call_native("pcolormesh", x, y, z, **kw)
        self._fix_patch_edges(m, **edgefix_kw, **kw)
        self._add_auto_labels(m, **labels_kw)
        # Add center levels to keywords
        guide_kw.setdefault("colorbar_kw", {})["center_levels"] = center_levels
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def pcolorfast(self, x, y, z, **kwargs):
        """
        %(plot.pcolorfast)s
        """
        x, y, z, kw = self._parse_2d_args(x, y, z, edges=True, **kwargs)
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            x, y, z, center_levels=center_levels, to_centers=True, **kw
        )
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)
        with self._keep_grid_bools():
            m = self._call_native("pcolorfast", x, y, z, **kw)
        if not isinstance(m, mimage.AxesImage):  # NOTE: PcolorImage is derivative
            self._fix_patch_edges(m, **edgefix_kw, **kw)
            self._add_auto_labels(m, **labels_kw)
        elif edgefix_kw or labels_kw:
            kw = {**edgefix_kw, **labels_kw}
            warnings._warn_ultraplot(
                f"Ignoring unused keyword argument(s): {kw}. These only work with "
                "QuadMesh, not AxesImage. Consider using pcolor() or pcolormesh()."
            )
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    @docstring._snippet_manager
    def heatmap(self, *args, aspect=None, **kwargs):
        """
        %(plot.heatmap)s
        """
        obj = self.pcolormesh(*args, default_discrete=False, **kwargs)
        aspect = _not_none(aspect, rc["image.aspect"])
        if self._name != "cartesian":
            warnings._warn_ultraplot(
                "The heatmap() command is meant for CartesianAxes "
                "only. Please use pcolor() or pcolormesh() instead."
            )
            return obj
        coords = getattr(obj, "_coordinates", None)
        xlocator = ylocator = None
        if coords is not None:
            coords = 0.5 * (coords[1:, ...] + coords[:-1, ...])
            coords = 0.5 * (coords[:, 1:, :] + coords[:, :-1, :])
            xlocator, ylocator = coords[0, :, 0], coords[:, 0, 1]
        kw = {"aspect": aspect, "xgrid": False, "ygrid": False}
        if xlocator is not None and self.xaxis.isDefault_majloc:
            kw["xlocator"] = xlocator
        if ylocator is not None and self.yaxis.isDefault_majloc:
            kw["ylocator"] = ylocator
        if self.xaxis.isDefault_minloc:
            kw["xtickminor"] = False
        if self.yaxis.isDefault_minloc:
            kw["ytickminor"] = False
        self.format(**kw)
        return obj

    @inputs._preprocess_or_redirect("x", "y", "u", "v", ("c", "color", "colors"))
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def barbs(self, x, y, u, v, c, **kwargs):
        """
        %(plot.barbs)s
        """
        x, y, u, v, kw = self._parse_2d_args(
            x, y, u, v, allow1d=True, autoguide=False, **kwargs
        )  # noqa: E501
        kw.update(_pop_props(kw, "line"))  # applied to barbs
        c, kw = self._parse_color(x, y, c, **kw)
        if mcolors.is_color_like(c):
            kw["barbcolor"], c = c, None
        a = [x, y, u, v]
        if c is not None:
            a.append(c)
        kw.pop("colorbar_kw", None)  # added by _parse_cmap
        m = self._call_native("barbs", *a, **kw)
        return m

    @inputs._preprocess_or_redirect("x", "y", "u", "v", ("c", "color", "colors"))
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def quiver(self, x, y, u, v, c, **kwargs):
        """
        %(plot.quiver)s
        """
        x, y, u, v, kw = self._parse_2d_args(
            x, y, u, v, allow1d=True, autoguide=False, **kwargs
        )  # noqa: E501
        kw.update(_pop_props(kw, "line"))  # applied to arrow outline
        c, kw = self._parse_color(x, y, c, **kw)
        color = None
        # Handle case where c is a singular color
        if mcolors.is_color_like(c):
            color, c = c, None

        if color is not None:
            kw["color"] = color

        a = [x, y, u, v]
        if c is not None:
            # If U is 1D we are dealing with arrows
            if len(u.shape) == 1:
                kw["color"] = c
            # Otherwise we assume we are populating a field
            else:
                a.append(c)
        kw.pop("colorbar_kw", None)  # added by _parse_cmap
        m = self._call_native("quiver", *a, **kw)
        return m

    @docstring._snippet_manager
    def stream(self, *args, **kwargs):
        """
        %(plot.stream)s
        """
        return self.streamplot(*args, **kwargs)

    # WARNING: breaking change from native streamplot() fifth positional arg 'density'
    @inputs._preprocess_or_redirect(
        "x", "y", "u", "v", ("c", "color", "colors"), keywords="start_points"
    )
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def streamplot(self, x, y, u, v, c, **kwargs):
        """
        %(plot.stream)s
        """
        x, y, u, v, kw = self._parse_2d_args(x, y, u, v, **kwargs)
        kw.update(_pop_props(kw, "line"))  # applied to lines
        c, kw = self._parse_color(x, y, c, **kw)
        if c is None:  # throws an error if color not provided
            c = pcolors.to_hex(self._get_lines.get_next_color())
        kw["color"] = c  # always pass this
        guide_kw = _pop_params(kw, self._update_guide)
        label = kw.pop("label", None)
        m = self._call_native("streamplot", x, y, u, v, **kw)
        m.lines.set_label(label)  # the collection label
        self._update_guide(m.lines, queue_colorbar=False, **guide_kw)  # use lines
        return m

    @inputs._parse_triangulation_with_preprocess("x", "y", "z", keywords=["triangles"])
    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def tricontour(self, *args, **kwargs):
        """
        %(plot.tricontour)s
        """
        kw = kwargs.copy()
        triangulation, z, args, kwargs = inputs._parse_triangulation_inputs(
            *args, **kwargs
        )

        # Update kwargs and handle cmap
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            triangulation.x,
            triangulation.y,
            z,
            min_levels=1,
            plot_lines=True,
            plot_contours=True,
            center_levels=center_levels,
            **kw,
        )

        # Handle labels and guide parameters
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)

        # Extract and assign label
        label = kw.pop("label", None)
        m = self._call_native("tricontour", triangulation, z, **kw)
        m._legend_label = label

        # Add labels and update guide
        self._add_auto_labels(m, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)

        return m

    @inputs._parse_triangulation_with_preprocess("x", "y", "z", keywords=["triangles"])
    @inputs._preprocess_or_redirect("x", "y", "z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def tricontourf(self, *args, **kwargs):
        """
        %(plot.tricontourf)s
        """
        kw = kwargs.copy()
        triangulation, z, args, kw = inputs._parse_triangulation_inputs(*args, **kwargs)

        # Update kwargs and handle contour parameters
        kw.update(_pop_props(kw, "collection"))
        contour_kw = _pop_kwargs(kw, "edgecolors", "linewidths", "linestyles")
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            triangulation.x,
            triangulation.y,
            z,
            center_levels=center_levels,
            plot_contours=True,
            **kw,
        )

        # Handle patch edges, labels, and guide parameters
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)

        label = kw.pop("label", None)

        # Call native tricontourf function with triangulation
        m = cm = self._call_native("tricontourf", triangulation, z, **kw)
        m._legend_label = label

        # Fix edges and add labels
        self._fix_patch_edges(m, **edgefix_kw, **contour_kw)  # No-op if not contour_kw
        if contour_kw or labels_kw:
            cm = self._fix_contour_edges(
                "tricontour", triangulation.x, triangulation.y, z, **kw, **contour_kw
            )

        # Add auto labels and update the guide
        self._add_auto_labels(m, cm, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)

        return m

    @inputs._parse_triangulation_with_preprocess("x", "y", "z", keywords=["triangles"])
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def tripcolor(self, *args, **kwargs):
        """
        %(plot.tripcolor)s
        """
        kw = kwargs.copy()
        triangulation, z, args, kw = inputs._parse_triangulation_inputs(*args, **kwargs)

        # Update kwargs and handle cmap
        kw.update(_pop_props(kw, "collection"))
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            triangulation.x, triangulation.y, z, center_levels=center_levels, **kw
        )

        # Handle patch edges, labels, and guide parameters
        edgefix_kw = _pop_params(kw, self._fix_patch_edges)
        labels_kw = _pop_params(kw, self._add_auto_labels)
        guide_kw = _pop_params(kw, self._update_guide)

        # Plot with the native tripcolor method
        with self._keep_grid_bools():
            m = self._call_native("tripcolor", triangulation, z, **kw)

        # Fix edges and add labels
        self._fix_patch_edges(m, **edgefix_kw, **kw)
        self._add_auto_labels(m, **labels_kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)

        return m

    # WARNING: breaking change from native 'X'
    @inputs._preprocess_or_redirect("z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def imshow(self, z, **kwargs):
        """
        %(plot.imshow)s
        """
        kw = kwargs.copy()
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            z, center_levels=center_levels, default_discrete=False, **kw
        )
        guide_kw = _pop_params(kw, self._update_guide)
        m = self._call_native("imshow", z, **kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    # WARNING: breaking change from native 'Z'
    @inputs._preprocess_or_redirect("z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def matshow(self, z, **kwargs):
        """
        %(plot.matshow)s
        """
        # Rely on imshow() override for this.
        return super().matshow(z, **kwargs)

    # WARNING: breaking change from native 'Z'
    @inputs._preprocess_or_redirect("z")
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def spy(self, z, **kwargs):
        """
        %(plot.spy)s
        """
        kw = kwargs.copy()
        kw.update(_pop_props(kw, "line"))  # takes valid Line2D properties
        default_cmap = pcolors.DiscreteColormap(["w", "k"], "_no_name")
        center_levels = kw.pop("center_levels", None)
        kw = self._parse_cmap(
            z, center_levels=center_levels, default_cmap=default_cmap, **kw
        )
        guide_kw = _pop_params(kw, self._update_guide)
        m = self._call_native("spy", z, **kw)
        self._update_guide(m, queue_colorbar=False, **guide_kw)
        return m

    def _iter_arg_pairs(self, *args):
        """
        Iterate over ``[x1,] y1, [fmt1,] [x2,] y2, [fmt2,] ...`` input.
        """
        # NOTE: This is copied from _process_plot_var_args.__call__ to avoid relying
        # on private API. We emulate this input style with successive plot() calls.
        args = list(args)
        while args:  # this permits empty input
            x, y, *args = args
            if args and isinstance(args[0], str):  # format string detected!
                fmt, *args = args
            elif isinstance(y, str):  # omits some of matplotlib's rigor but whatevs
                x, y, fmt = None, x, y
            else:
                fmt = None
            yield x, y, fmt

    def _iter_arg_cols(self, *args, label=None, labels=None, values=None, **kwargs):
        """
        Iterate over columns of positional arguments.
        """
        is_array = lambda data: hasattr(data, "ndim") and hasattr(data, "shape")

        # Determine the number of columns
        n = max(1 if not is_array(a) or a.ndim < 2 else a.shape[-1] for a in args)

        # Handle labels
        labels = _not_none(label=label, values=values, labels=labels)
        if not np.iterable(labels) or isinstance(labels, str):
            labels = n * [labels]
        if len(labels) != n:
            raise ValueError(f"Array has {n} columns but got {len(labels)} labels.")
        if labels is not None:
            labels = [
                str(_not_none(label, "")) for label in inputs._to_numpy_array(labels)
            ]
        else:
            labels = n * [None]

        # Yield successive columns
        for i in range(n):
            kw = kwargs.copy()
            kw["label"] = labels[i] or None
            a = tuple(a if not is_array(a) or a.ndim < 2 else a[..., i] for a in args)
            yield (i, n, *a, kw)

    # Related parsing functions for warnings
    _level_parsers = (_parse_level_vals, _parse_level_num, _parse_level_lim)

    # Rename the shorthands
    boxes = warnings._rename_objs("0.8.0", boxes=box)
    violins = warnings._rename_objs("0.8.0", violins=violin)
