#!/usr/bin/env python3
"""
Axes filled with cartographic projections.
"""
import copy
import inspect
from functools import partial

try:
    # From python 3.12
    from typing import override
except ImportError:
    # From Python 3.5
    from typing_extensions import override

from collections.abc import MutableMapping

import matplotlib.axis as maxis
import matplotlib.path as mpath
import matplotlib.text as mtext
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import numpy as np

from .. import constructor
from .. import proj as pproj
from ..config import rc
from ..internals import ic  # noqa: F401
from ..internals import (
    _not_none,
    _pop_rc,
    _version_cartopy,
    docstring,
    warnings,
)
from .. import ticker as pticker
from ..utils import units
from . import plot
from . import shared

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.mpl.gridliner as cgridliner
    from cartopy.crs import Projection
    from cartopy.mpl.geoaxes import GeoAxes as _GeoAxes
except ModuleNotFoundError:
    ccrs = cfeature = cgridliner = None
    _GeoAxes = Projection = object

try:
    from mpl_toolkits.basemap import Basemap
except ModuleNotFoundError:
    Basemap = object

__all__ = ["GeoAxes"]


# Format docstring
_format_docstring = """
round : bool, default: :rc:`geo.round`
    *For polar cartopy axes only*.
    Whether to bound polar projections with circles rather than squares. Note that outer
    gridline labels cannot be added to circle-bounded polar projections. When basemap
    is the backend this argument must be passed to `~ultraplot.constructor.Proj` instead.
extent : {'globe', 'auto'}, default: :rc:`geo.extent`
    *For cartopy axes only*.
    Whether to auto adjust the map bounds based on plotted content. If ``'globe'`` then
    non-polar projections are fixed with `~cartopy.mpl.geoaxes.GeoAxes.set_global`,
    non-Gnomonic polar projections are bounded at the equator, and Gnomonic polar
    projections are bounded at 30 degrees latitude. If ``'auto'`` nothing is done.
lonlim, latlim : 2-tuple of float, optional
    *For cartopy axes only.*
    The approximate longitude and latitude boundaries of the map, applied
    with `~cartopy.mpl.geoaxes.GeoAxes.set_extent`. When basemap is the backend
    this argument must be passed to `~ultraplot.constructor.Proj` instead.
boundinglat : float, optional
    *For cartopy axes only.*
    The edge latitude for the circle bounding North Pole and South Pole-centered
    projections. When basemap is the backend this argument must be passed to
    `~ultraplot.constructor.Proj` instead.
longrid, latgrid, grid : bool, default: :rc:`grid`
    Whether to draw longitude and latitude gridlines.
    Use the keyword `grid` to toggle both at once.
longridminor, latgridminor, gridminor : bool, default: :rc:`gridminor`
    Whether to draw "minor" longitude and latitude lines.
    Use the keyword `gridminor` to toggle both at once.
lonticklen, latticklen, ticklen : unit-spec, default: :rc:`tick.len`
    Major tick lengths for the longitudinal (x) and latitude (y) axis.
    %(units.pt)s
    Use the keyword `ticklen` to set both at once.
latmax : float, default: 80
    The maximum absolute latitude for gridlines. Longitude gridlines are cut off
    poleward of this value (note this feature does not work in cartopy 0.18).
nsteps : int, default: :rc:`grid.nsteps`
    *For cartopy axes only.*
    The number of interpolation steps used to draw gridlines.
lonlines, latlines : optional
    Aliases for `lonlocator`, `latlocator`.
lonlocator, latlocator : locator-spec, optional
    Used to determine the longitude and latitude gridline locations.
    Passed to the `~ultraplot.constructor.Locator` constructor. Can be
    string, float, list of float, or `matplotlib.ticker.Locator` instance.

    For basemap or cartopy < 0.18, the defaults are ``'deglon'`` and
    ``'deglat'``, which correspond to the `~ultraplot.ticker.LongitudeLocator`
    and `~ultraplot.ticker.LatitudeLocator` locators (adapted from cartopy).
    For cartopy >= 0.18, the defaults are ``'dmslon'`` and ``'dmslat'``,
    which uses the same locators with ``dms=True``. This selects gridlines
    at nice degree-minute-second intervals when the map extent is very small.
lonlines_kw, latlines_kw : optional
    Aliases for `lonlocator_kw`, `latlocator_kw`.
lonlocator_kw, latlocator_kw : dict-like, optional
    Keyword arguments passed to the `matplotlib.ticker.Locator` class.
lonminorlocator, latminorlocator, lonminorlines, latminorlines : optional
    As with `lonlocator` and `latlocator` but for the "minor" gridlines.
lonminorlines_kw, latminorlines_kw : optional
    Aliases for `lonminorlocator_kw`, `latminorlocator_kw`.
lonminorlocator_kw, latminorlocator_kw : optional
    As with `lonlocator_kw`, and `latlocator_kw` but for the "minor" gridlines.
lonlabels, latlabels, labels : str, bool, or sequence, :rc:`grid.labels`
    Whether to add non-inline longitude and latitude gridline labels, and on
    which sides of the map. Use the keyword `labels` to set both at once. The
    argument must conform to one of the following options:

    * A boolean. ``True`` indicates the bottom side for longitudes and
      the left side for latitudes, and ``False`` disables all labels.
    * A string or sequence of strings indicating the side names, e.g.
      ``'top'`` for longitudes or ``('left', 'right')`` for latitudes.
    * A string indicating the side names with single characters, e.g.
      ``'bt'`` for longitudes or ``'lr'`` for latitudes.
    * A string matching ``'neither'`` (no labels), ``'both'`` (equivalent
      to ``'bt'`` for longitudes and ``'lr'`` for latitudes), or ``'all'``
      (equivalent to ``'lrbt'``, i.e. all sides).
    * A boolean 2-tuple indicating whether to draw labels
      on the ``(bottom, top)`` sides for longitudes,
      and the ``(left, right)`` sides for latitudes.
    * A boolean 4-tuple indicating whether to draw labels on the
      ``(left, right, bottom, top)`` sides, as with the basemap
      :func:`~mpl_toolkits.basemap.Basemap.drawmeridians` and
      :func:`~mpl_toolkits.basemap.Basemap.drawparallels` `labels` keyword.

loninline, latinline, inlinelabels : bool, default: :rc:`grid.inlinelabels`
    *For cartopy axes only.*
    Whether to add inline longitude and latitude gridline labels. Use
    the keyword `inlinelabels` to set both at once.
rotatelabels : bool, default: :rc:`grid.rotatelabels`
    *For cartopy axes only.*
    Whether to rotate non-inline gridline labels so that they automatically
    follow the map boundary curvature.
labelpad : unit-spec, default: :rc:`grid.labelpad`
    *For cartopy axes only.*
    The padding between non-inline gridline labels and the map boundary.
    %(units.pt)s
dms : bool, default: :rc:`grid.dmslabels`
    *For cartopy axes only.*
    Whether the default locators and formatters should use "minutes" and "seconds"
    for gridline labels on small scales rather than decimal degrees. Setting this to
    ``False`` is equivalent to ``ax.format(lonlocator='deglon', latlocator='deglat')``
    and ``ax.format(lonformatter='deglon', latformatter='deglat')``.
lonformatter, latformatter : formatter-spec, optional
    Formatter used to style longitude and latitude gridline labels.
    Passed to the `~ultraplot.constructor.Formatter` constructor. Can be
    string, list of string, or `matplotlib.ticker.Formatter` instance.

    For basemap or cartopy < 0.18, the defaults are ``'deglon'`` and
    ``'deglat'``, which correspond to `~ultraplot.ticker.SimpleFormatter`
    presets with degree symbols and cardinal direction suffixes.
    For cartopy >= 0.18, the defaults are ``'dmslon'`` and ``'dmslat'``,
    which uses cartopy's `~cartopy.mpl.ticker.LongitudeFormatter` and
    `~cartopy.mpl.ticker.LatitudeFormatter` formatters with ``dms=True``.
    This formats gridlines that do not fall on whole degrees as "minutes" and
    "seconds" rather than decimal degrees. Use ``dms=False`` to disable this.
lonformatter_kw, latformatter_kw : dict-like, optional
    Keyword arguments passed to the `matplotlib.ticker.Formatter` class.
land, ocean, coast, rivers, lakes, borders, innerborders : bool, optional
    Toggles various geographic features. These are actually the
    :rcraw:`land`, :rcraw:`ocean`, :rcraw:`coast`, :rcraw:`rivers`,
    :rcraw:`lakes`, :rcraw:`borders`, and :rcraw:`innerborders`
    settings passed to `~ultraplot.config.Configurator.context`.
    The style can be modified using additional `rc` settings.

    For example, to change :rcraw:`land.color`, use
    ``ax.format(landcolor='green')``, and to change
    :rcraw:`land.zorder`, use ``ax.format(landzorder=4)``.
reso : {'lo', 'med', 'hi', 'x-hi', 'xx-hi'}, optional
    *For cartopy axes only.*
    The resolution of geographic features. When basemap is the backend this
    must be passed to `~ultraplot.constructor.Proj` instead.
color : color-spec, default: :rc:`meta.color`
    The color for the axes edge. Propagates to `labelcolor` unless specified
    otherwise (similar to :func:`ultraplot.axes.CartesianAxes.format`).
gridcolor : color-spec, default: :rc:`grid.color`
    The color for the gridline labels.
labelcolor : color-spec, default: `color` or :rc:`grid.labelcolor`
    The color for the gridline labels (`gridlabelcolor` is also allowed).
labelsize : unit-spec or str, default: :rc:`grid.labelsize`
    The font size for the gridline labels (`gridlabelsize` is also allowed).
    %(units.pt)s
labelweight : str, default: :rc:`grid.labelweight`
    The font weight for the gridline labels (`gridlabelweight` is also allowed).
"""
docstring._snippet_manager["geo.format"] = _format_docstring


class _GeoLabel(object):
    """
    Optionally omit overlapping check if an rc setting is disabled.
    """

    def check_overlapping(self, *args, **kwargs):
        if rc["grid.checkoverlap"]:
            return super().check_overlapping(*args, **kwargs)
        else:
            return False


# Add monkey patch to gridliner module
if cgridliner is not None and hasattr(cgridliner, "Label"):  # only recent versions
    _cls = type("Label", (_GeoLabel, cgridliner.Label), {})
    cgridliner.Label = _cls


class _GeoAxis(object):
    """
    Dummy axis used by longitude and latitude locators and for storing view limits on
    longitude and latitude coordinates. Modeled after how `matplotlib.ticker._DummyAxis`
    and `matplotlib.ticker.TickHelper` are used to control tick locations and labels.
    """

    # NOTE: Due to cartopy bug (https://github.com/SciTools/cartopy/issues/1564)
    # we store presistent longitude and latitude locators on axes, then *call*
    # them whenever set_extent is called and apply *fixed* locators.
    def __init__(self, axes):
        self.axes = axes
        self.major = maxis.Ticker()
        self.minor = maxis.Ticker()
        self.isDefault_majfmt = True
        self.isDefault_majloc = True
        self.isDefault_minloc = True
        self._interval = None
        self._use_dms = (
            ccrs is not None
            and isinstance(
                axes.projection, (ccrs._RectangularProjection, ccrs.Mercator)
            )  # noqa: E501
            and _version_cartopy >= "0.18"
        )

    def _get_extent(self):
        # Try to get extent but bail out for projections where this is
        # impossible. So far just transverse Mercator
        try:
            return self.axes.get_extent()
        except Exception:
            lon0 = self.axes._get_lon0()
            return (-180 + lon0, 180 + lon0, -90, 90)

    @staticmethod
    def _pad_ticks(ticks, vmin, vmax):
        # Wrap up to the longitude/latitude range to avoid
        # giant lists of 10,000 gridline locations.
        if len(ticks) == 0:
            return ticks
        range_ = np.max(ticks) - np.min(ticks)
        vmin = max(vmin, ticks[0] - range_)
        vmax = min(vmax, ticks[-1] + range_)

        # Pad the reported tick range up to specified range
        step = ticks[1] - ticks[0]  # MaxNLocator/AutoMinorLocator steps are equal
        ticks_lo = np.arange(ticks[0], vmin, -step)[1:][::-1]
        ticks_hi = np.arange(ticks[-1], vmax, step)[1:]
        ticks = np.concatenate((ticks_lo, ticks, ticks_hi))
        return ticks

    def get_scale(self):
        return "linear"

    def get_tick_space(self):
        return 9  # longstanding default of nbins=9

    def get_major_formatter(self):
        return self.major.formatter

    def get_major_locator(self):
        return self.major.locator

    def get_minor_locator(self):
        return self.minor.locator

    def get_majorticklocs(self):
        return self._get_ticklocs(self.major.locator)

    def get_minorticklocs(self):
        return self._get_ticklocs(self.minor.locator)

    def set_major_formatter(self, formatter, default=False):
        # NOTE: Cartopy formatters check Formatter.axis.axes.projection
        # in order to implement special projection-dependent behavior.
        self.major.formatter = formatter
        formatter.set_axis(self)
        self.isDefault_majfmt = default

    def set_major_locator(self, locator, default=False):
        self.major.locator = locator
        if self.major.formatter:
            self.major.formatter._set_locator(locator)
        locator.set_axis(self)
        self.isDefault_majloc = default

    def set_minor_locator(self, locator, default=False):
        self.minor.locator = locator
        locator.set_axis(self)
        self.isDefault_majfmt = default

    def set_view_interval(self, vmin, vmax):
        self._interval = (vmin, vmax)

    def _copy_locator_properties(self, other: "_GeoAxis"):
        """
        This function copies the locator properties. It is
        used when the @self is sharing with @other.
        """
        props = [
            "isDefault_majloc",
            "isDefault_minloc",
            "isDefault_majfmt",
        ]
        funcs = [
            "major_locator",
            "minor_locator",
            "major_formatter",
        ]
        for prop, func in zip(props, funcs):
            # Copy if props differ from this to other
            this_prop = getattr(self, prop)
            other_prop = getattr(other, prop)
            if this_prop ^ other_prop:
                # Allow this to error if in the unlikely
                # case that the backend changes
                getter = getattr(self, f"get_{func}")
                setter = getattr(other, f"set_{func}")
                setter(getter())
                setattr(other, prop, this_prop)


class _LonAxis(_GeoAxis):
    """
    Axis with default longitude locator.
    """

    axis_name = "lon"

    # NOTE: Basemap accepts tick formatters with drawmeridians(fmt=Formatter())
    # Try to use cartopy formatter if cartopy installed. Otherwise use
    # default builtin basemap formatting.
    def __init__(self, axes):
        super().__init__(axes)
        if self._use_dms:
            locator = formatter = "dmslon"
        else:
            locator = formatter = "deglon"
        self.set_major_formatter(
            constructor.Formatter(formatter),
            default=True,
        )
        self.set_major_locator(constructor.Locator(locator), default=True)
        self.set_minor_locator(mticker.AutoMinorLocator(), default=True)

    def _get_ticklocs(self, locator):
        # Prevent ticks from looping around
        # NOTE: Cartopy 0.17 formats numbers offset by eps with the cardinal indicator
        # (e.g. 0 degrees for map centered on 180 degrees). So skip in that case.
        # NOTE: Common strange issue is e.g. MultipleLocator(60) starts out at
        # -60 degrees for a map from 0 to 360 degrees. If always trimmed circular
        # locations from right then would cut off rightmost gridline. Workaround is
        # to trim on the side closest to central longitude (in this case the left).
        eps = 1e-10
        # We set lon0 in the Formatter here
        # as initially the formatter is parsed
        # as a SimpleFormatter. Here, the formatter
        # should be a LongitudinalFormatter.
        lon0 = self.axes._get_lon0()
        formatter = self.get_major_formatter()
        formatter.lon0 = lon0  # update if necessary
        ticks = np.sort(locator())
        while ticks.size:
            if np.isclose(ticks[0] + 360, ticks[-1]):
                if _version_cartopy >= "0.18" or not np.isclose(ticks[0] % 360, 0):
                    ticks[-1] -= eps  # ensure label appears on *right* not left
                break
            elif ticks[0] + 360 < ticks[-1]:
                idx = (1, None) if lon0 - ticks[0] > ticks[-1] - lon0 else (None, -1)
                ticks = ticks[slice(*idx)]  # cut off ticks looped over globe
            else:
                break

        # Append extra ticks in case longitude/latitude limits do not encompass
        # the entire view range of map, e.g. for Lambert Conformal sectors.
        # NOTE: Try to avoid making 10,000 element lists. Just wrap extra ticks
        # up to the width of *reported* longitude range.
        if isinstance(locator, (mticker.MaxNLocator, mticker.AutoMinorLocator)):
            ticks = self._pad_ticks(ticks, lon0 - 180 + eps, lon0 + 180 - eps)

        return ticks

    def get_view_interval(self):
        # NOTE: ultraplot tries to set its *own* view intervals to avoid dateline
        # weirdness, but if rc['geo.extent'] is 'auto' the interval will be unset.
        # In this case we use _get_extent() as a backup.
        interval = self._interval
        if interval is None:
            extent = self._get_extent()
            interval = extent[:2]  # longitude extents
        return interval


class _LatAxis(_GeoAxis):
    """
    Axis with default latitude locator.
    """

    axis_name = "lat"

    def __init__(self, axes, latmax=90):
        # NOTE: Need to pass projection because lataxis/lonaxis are
        # initialized before geoaxes is initialized, because format() needs
        # the axes and format() is called by ultraplot.axes.Axes.__init__()
        self._latmax = latmax
        super().__init__(axes)
        if self._use_dms:
            locator = formatter = "dmslat"
        else:
            locator = formatter = "deglat"
        self.set_major_formatter(constructor.Formatter(formatter), default=True)
        self.set_major_locator(constructor.Locator(locator), default=True)
        self.set_minor_locator(mticker.AutoMinorLocator(), default=True)

    def _get_ticklocs(self, locator):
        # Adjust latitude ticks to fix bug in some projections. Harmless for basemap.
        # NOTE: Maybe this was fixed by cartopy 0.18?
        eps = 1e-10
        ticks = np.sort(locator())
        if ticks.size:
            if ticks[0] == -90:
                ticks[0] += eps
            if ticks[-1] == 90:
                ticks[-1] -= eps

        # Append extra ticks in case longitude/latitude limits do not encompass
        # the entire view range of map, e.g. for Lambert Conformal sectors.
        if isinstance(locator, (mticker.MaxNLocator, mticker.AutoMinorLocator)):
            ticks = self._pad_ticks(ticks, -90 + eps, 90 - eps)

        # Filter ticks to latmax range
        latmax = self.get_latmax()
        ticks = ticks[(ticks >= -latmax) & (ticks <= latmax)]

        return ticks

    def get_latmax(self):
        return self._latmax

    def get_view_interval(self):
        interval = self._interval
        if interval is None:
            extent = self._get_extent()
            interval = extent[2:]  # latitudes
        return interval

    def set_latmax(self, latmax):
        self._latmax = latmax


class GeoAxes(shared._SharedAxes, plot.PlotAxes):
    """
    Axes subclass for plotting in geographic projections. Uses either cartopy
    or basemap as a "backend".

    Note
    ----
    This subclass uses longitude and latitude as the default coordinate system for all
    plotting commands by internally passing ``transform=cartopy.crs.PlateCarree()`` to
    cartopy commands and ``latlon=True`` to basemap commands. Also, when using basemap
    as the "backend", plotting is still done "cartopy-style" by calling methods from
    the axes instance rather than the `~mpl_toolkits.basemap.Basemap` instance.

    Important
    ---------
    This axes subclass can be used by passing ``proj='proj_name'``
    to axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and `~ultraplot.figure.Figure.subplots`,
    where ``proj_name`` is a registered :ref:`PROJ projection name <proj_table>`.
    You can also pass a `~cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap`
    instance instead of a projection name. Alternatively, you can pass any of the
    matplotlib-recognized axes subclass names ``proj='cartopy'``, ``proj='geo'``, or
    ``proj='geographic'`` with a `~cartopy.crs.Projection` `map_projection` keyword
    argument, or pass ``proj='basemap'`` with a `~mpl_toolkits.basemap.Basemap`
    `map_projection` keyword argument.
    """

    @docstring._snippet_manager
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args
            Passed to `matplotlib.axes.Axes`.
        map_projection : `~cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap`
            The cartopy or basemap projection instance. This is
            passed automatically when calling axes-creation
            commands like `~ultraplot.figure.Figure.add_subplot`.
        %(geo.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(rc.init)s

        See also
        --------
        GeoAxes.format
        ultraplot.constructor.Proj
        ultraplot.axes.Axes
        ultraplot.axes.PlotAxes
        ultraplot.figure.Figure.subplot
        ultraplot.figure.Figure.add_subplot
        """
        super().__init__(*args, **kwargs)

    @override
    def _sharey_limits(self, sharey: "GeoAxes"):
        return self._share_limits_with(sharey, which="y")

    @override
    def _sharex_limits(self, sharex: "GeoAxes"):
        return self._share_limits_with(sharex, which="x")

    def _share_limits_with(self, other: "GeoAxes", which: str):
        """
        Safely share limits and tickers without resetting things.
        """
        # NOTE: See _sharex_limits for notes
        if which == "x":
            this_ax = self._lonaxis
            other_ax = other._lonaxis
        else:
            this_ax = self._lataxis
            other_ax = other._lataxis
        for ax1, ax2 in ((other_ax, this_ax), (this_ax, other_ax)):
            ax1.set_view_interval(*ax2.get_view_interval())

        # Set the shared axis
        getattr(self, f"share{which}")(other)
        this_ax._copy_locator_properties(other_ax)

    def _is_rectilinear(self):
        return _is_rectilinear_projection(self)

    def __share_axis_setup(
        self,
        other: "GeoAxes",
        *,
        which: str,
        labels: bool,
        limits: bool,
    ):
        level = getattr(self.figure, f"_share{which}")
        if getattr(self, f"_panel_share{which}_group") and self.is_panel_group_member(
            other
        ):
            level = 3
        if level not in range(5):  # must be internal error
            raise ValueError(f"Invalid sharing level sharex={level!r}.")
        if other in (None, self) or not isinstance(other, GeoAxes):
            return
        # Share future axis label changes. Implemented in _apply_axis_sharing().
        # Matplotlib only uses these attributes in __init__() and cla() to share
        # tickers -- all other builtin sharing features derives from shared x axes
        if level > 0 and labels:
            setattr(self, f"_share{which}", other)
        # Share future axis tickers, limits, and scales
        # NOTE: Only difference between levels 2 and 3 is level 3 hides ticklabels
        # labels. But this is done after the fact -- tickers are still shared.
        if level > 1 and limits:
            self._share_limits_with(other, which=which)

    @override
    def _sharey_setup(self, sharey, *, labels=True, limits=True):
        """
        Configure shared axes accounting for panels. The input is the
        'parent' axes, from which this one will draw its properties.
        """
        super()._sharey_setup(sharey, labels=labels, limits=limits)
        return self.__share_axis_setup(sharey, which="y", labels=labels, limits=limits)

    @override
    def _sharex_setup(self, sharex, *, labels=True, limits=True):
        # Share panels across *different* subplots
        super()._sharex_setup(sharex, labels=labels, limits=limits)
        return self.__share_axis_setup(sharex, which="x", labels=labels, limits=limits)

    def _toggle_ticks(self, label: "str | None", which: str):
        """
        Ticks are controlled by matplotlib independent of the backend. We can toggle ticks on and of depending on the desired position.
        """
        if not isinstance(label, str):
            return

        # Only allow "lrbt" and "all" or "both"
        label = label.replace("top", "t")
        label = label.replace("bottom", "b")
        label = label.replace("left", "l")
        label = label.replace("right", "r")
        match label:
            case _ if len(label) == 2 and "t" in label and "b" in label:
                self.xaxis.set_ticks_position("both")
            case _ if len(label) == 2 and "l" in label and "r" in label:
                self.yaxis.set_ticks_position("both")
            case "t":
                self.xaxis.set_ticks_position("top")
            case "b":
                self.xaxis.set_ticks_position("bottom")
            case "l":
                self.yaxis.set_ticks_position("left")
            case "r":
                self.yaxis.set_ticks_position("right")
            case "all":
                self.xaxis.set_ticks_position("both")
                self.yaxis.set_ticks_position("both")
            case "both":
                if which == "x":
                    self.xaxis.set_ticks_position("both")
                else:
                    self.yaxis.set_ticks_position("both")
            case _:
                warnings._warn_ultraplot(
                    f"Not toggling {label=}. Input was not understood. Valid values are ['left', 'right', 'top', 'bottom', 'all', 'both']"
                )

    def _apply_axis_sharing(self):
        """
        Enforce the "shared" axis labels and axis tick labels. If this is not
        called at drawtime, "shared" labels can be inadvertantly turned off.

        Notes:
            - Critical to apply labels to *shared* axes attributes rather than testing
                extents or we end up sharing labels with twin axes.
            - Similar to how align_super_labels() calls apply_title_above(), this is called
                inside align_axis_labels() so we align the correct text.
            - The "panel sharing group" refers to axes and panels *above* the bottommost
                or to the *right* of the leftmost panel. But the sharing level used for
                the leftmost and bottommost is the *figure* sharing level.
        """
        # Handle X axis sharing
        if self._sharex:
            self._handle_axis_sharing(
                source_axis=self._sharex._lonaxis,
                target_axis=self._lonaxis,
            )

        # Handle Y axis sharing
        if self._sharey:
            self._handle_axis_sharing(
                source_axis=self._sharey._lataxis,
                target_axis=self._lataxis,
            )

    def _get_gridliner_labels(
        self,
        bottom=None,
        top=None,
        left=None,
        right=None,
    ):
        assert NotImplementedError("Should be implemented by Cartopy or Basemap Axes")

    def _toggle_gridliner_labels(
        self,
        top=None,
        bottom=None,
        left=None,
        right=None,
        geo=None,
    ):
        # For BasemapAxes the gridlines are dicts with key as the coordinate and  keys the line and label
        # We override the dict here assuming the labels are mut excl due to the N S E W extra chars
        if self.gridlines_major is None:
            return
        if any(i is None for i in self.gridlines_major):
            return
        gridlabels = self._get_gridliner_labels(
            bottom=bottom, top=top, left=left, right=right
        )
        for direction, toggle in zip(
            "bottom top left right".split(),
            [bottom, top, left, right],
        ):
            if toggle is not None:
                for label in gridlabels.get(direction, []):
                    label.set_visible(toggle)
        self.stale = True

    def _handle_axis_sharing(
        self,
        source_axis: "GeoAxes",
        target_axis: "GeoAxes",
    ):
        """
        Helper method to handle axis sharing for both X and Y axes.

        Args:
            source_axis: The source axis to share from
            target_axis: The target axis to apply sharing to
        """
        # Copy view interval and minor locator from source to target

        if self.figure._get_sharing_level() >= 2:
            target_axis.set_view_interval(*source_axis.get_view_interval())
            target_axis.set_minor_locator(source_axis.get_minor_locator())

        if not self.stale:
            return

        # Turn all labels off
        # Note: this action performs it for all the axes in
        # the figure. We use the stale here to only perform
        # it once as it is an expensive action.
        border_axes = self.figure._get_border_axes()
        # Recode:
        recoded = {}
        for direction, axes in border_axes.items():
            for axi in axes:
                recoded[axi] = recoded.get(axi, []) + [direction]

        # We turn off the tick labels when the scale and
        # ticks are shared (level >= 3)
        are_ticks_on = True
        if self.figure._get_sharing_level() >= 3:
            are_ticks_on = False

        default = dict(
            left=are_ticks_on,
            right=are_ticks_on,
            top=are_ticks_on,
            bottom=are_ticks_on,
        )
        for axi in self.figure.axes:
            # If users call colorbar on the figure
            # an axis is added which needs to skip the
            # sharing that is specific for the GeoAxes.
            if not isinstance(axi, GeoAxes):
                continue

            sides = recoded.get(axi, [])
            tmp = default.copy()
            for side in sides:
                tmp[side] = True
            axi._toggle_gridliner_labels(**tmp)
        self.stale = False

    @override
    def draw(self, renderer=None, *args, **kwargs):
        # Perform extra post-processing steps
        # NOTE: In *principle* axis sharing application step goes here. But should
        # already be complete because auto_layout() (called by figure pre-processor)
        # has to run it before aligning labels. So this is harmless no-op.
        self._apply_axis_sharing()
        super().draw(renderer, *args, **kwargs)

    def _get_lonticklocs(self, which="major"):
        """
        Retrieve longitude tick locations.
        """
        # Get tick locations from dummy axes
        # NOTE: This is workaround for: https://github.com/SciTools/cartopy/issues/1564
        # Since _axes_domain is wrong we determine tick locations ourselves with
        # more accurate extent tracked by _LatAxis and _LonAxis.
        axis = self._lonaxis
        if which == "major":
            lines = axis.get_majorticklocs()
        else:
            lines = axis.get_minorticklocs()
        return lines

    def _get_latticklocs(self, which="major"):
        """
        Retrieve latitude tick locations.
        """
        axis = self._lataxis
        if which == "major":
            lines = axis.get_majorticklocs()
        else:
            lines = axis.get_minorticklocs()
        return lines

    def _set_view_intervals(self, extent):
        """
        Update view intervals for lon and lat axis.
        """
        self._lonaxis.set_view_interval(*extent[:2])
        self._lataxis.set_view_interval(*extent[2:])

    @staticmethod
    def _to_label_array(arg, lon=True):
        """
        Convert labels argument to length-5 boolean array.
        """
        array = arg
        which = "lon" if lon else "lat"
        array = np.atleast_1d(array).tolist()
        if len(array) == 1 and array[0] is None:
            array = [None] * 5
        elif all(isinstance(_, str) for _ in array):
            strings = array  # iterate over list of strings
            array = [False] * 5
            opts = ("left", "right", "bottom", "top", "geo")
            for string in strings:
                string = string.replace("left", "l")
                string = string.replace("right", "r")
                string = string.replace("bottom", "b")
                string = string.replace("top", "t")
                if string == "all":
                    string = "lrbt"
                elif string == "both":
                    string = "bt" if lon else "lr"
                elif string == "neither":
                    string = ""
                elif string in opts:
                    string = string[0]
                if set(string) - set("lrbtg"):
                    raise ValueError(
                        f"Invalid {which}label string {string!r}. Must be one of "
                        + ", ".join(map(repr, (*opts, "neither", "both", "all")))
                        + " or a string of single-letter characters like 'lr'."
                    )
                for char in string:
                    array["lrbtg".index(char)] = True
                if rc["grid.geolabels"] and any(array):
                    array[4] = True  # possibly toggle geo spine labels
        elif not any(isinstance(_, str) for _ in array):
            if len(array) == 1:
                array.append(False)  # default is to label bottom or left
            if len(array) == 2:
                array = [False, False, *array] if lon else [*array, False, False]
            if len(array) == 4:
                b = any(array) if rc["grid.geolabels"] else False
                array.append(b)  # possibly toggle geo spine labels
            if len(array) != 5:
                raise ValueError(f"Invald boolean label array length {len(array)}.")
            array = list(map(bool, array))
        else:
            raise ValueError(f"Invalid {which}label spec: {arg}.")
        return array

    @docstring._snippet_manager
    def format(
        self,
        *,
        extent=None,
        round=None,
        lonlim=None,
        latlim=None,
        boundinglat=None,
        longrid=None,
        latgrid=None,
        longridminor=None,
        latgridminor=None,
        ticklen=None,
        lonticklen=None,
        latticklen=None,
        latmax=None,
        nsteps=None,
        lonlocator=None,
        lonlines=None,
        latlocator=None,
        latlines=None,
        lonminorlocator=None,
        lonminorlines=None,
        latminorlocator=None,
        latminorlines=None,
        lonlocator_kw=None,
        lonlines_kw=None,
        latlocator_kw=None,
        latlines_kw=None,
        lonminorlocator_kw=None,
        lonminorlines_kw=None,
        latminorlocator_kw=None,
        latminorlines_kw=None,
        lonformatter=None,
        latformatter=None,
        lonformatter_kw=None,
        latformatter_kw=None,
        labels=None,
        latlabels=None,
        lonlabels=None,
        rotatelabels=None,
        loninline=None,
        latinline=None,
        inlinelabels=None,
        dms=None,
        labelpad=None,
        labelcolor=None,
        labelsize=None,
        labelweight=None,
        **kwargs,
    ):
        """
        Modify map limits, longitude and latitude
        gridlines, geographic features, and more.

        Parameters
        ----------
        %(geo.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(figure.format)s
        %(rc.format)s

        See also
        --------
        ultraplot.axes.Axes.format
        ultraplot.config.Configurator.context
        """
        # Initialize map boundary
        # WARNING: Normal workflow is Axes.format() does 'universal' tasks including
        # updating the map boundary (in the future may also handle gridlines). However
        # drawing gridlines before basemap map boundary will call set_axes_limits()
        # which initializes a boundary hidden from external access. So we must call
        # it here. Must do this between mpl.Axes.__init__() and base.Axes.format().
        #
        if self._name == "basemap" and self._map_boundary is None:
            if self.projection.projection in self._proj_non_rectangular:
                patch = self.projection.drawmapboundary(ax=self)
                self._map_boundary = patch
            else:
                self.projection.set_axes_limits(self)  # initialize aspect ratio
                self._map_boundary = object()  # sentinel

        # Initiate context block
        rc_kw, rc_mode = _pop_rc(kwargs)
        ticklen = _not_none(
            ticklen, rc_kw.get("tick.len", None)
        )  # Don't pop this as it will only plot on a singular axis
        lonlabels = _not_none(lonlabels, labels)
        latlabels = _not_none(latlabels, labels)
        if "0.18" <= _version_cartopy < "0.20":
            lonlabels = _not_none(lonlabels, loninline, inlinelabels)
            latlabels = _not_none(latlabels, latinline, inlinelabels)
        labelcolor = _not_none(labelcolor, kwargs.get("color", None))
        if labelcolor is not None:
            rc_kw["grid.labelcolor"] = labelcolor
        if labelsize is not None:
            rc_kw["grid.labelsize"] = labelsize
        if labelweight is not None:
            rc_kw["grid.labelweight"] = labelweight
        with rc.context(rc_kw, mode=rc_mode):
            # Apply extent mode first
            # NOTE: We deprecate autoextent on _CartopyAxes with _rename_kwargs which
            # does not translate boolean flag. So here apply translation.
            if extent is not None and not isinstance(extent, str):
                extent = ("globe", "auto")[int(bool(extent))]
            self._update_boundary(round)
            self._update_extent_mode(extent, boundinglat)

            # Retrieve label toggles
            # NOTE: Cartopy 0.18 and 0.19 inline labels require any of
            # top, bottom, left, or right to be toggled then ignores them.
            # Later versions of cartopy permit both or neither labels.
            labels = _not_none(labels, rc.find("grid.labels", context=True))
            lonlabels = _not_none(lonlabels, labels)
            latlabels = _not_none(latlabels, labels)
            # Set the ticks
            self._toggle_ticks(lonlabels, "x")
            self._toggle_ticks(latlabels, "y")
            lonarray = self._to_label_array(lonlabels, lon=True)
            latarray = self._to_label_array(latlabels, lon=False)

            # Update max latitude
            latmax = _not_none(latmax, rc.find("grid.latmax", context=True))
            if latmax is not None:
                self._lataxis.set_latmax(latmax)

            # Update major locators
            lonlocator = _not_none(lonlocator=lonlocator, lonlines=lonlines)
            latlocator = _not_none(latlocator=latlocator, latlines=latlines)
            if lonlocator is not None:
                lonlocator_kw = _not_none(
                    lonlocator_kw=lonlocator_kw,
                    lonlines_kw=lonlines_kw,
                    default={},
                )
                locator = constructor.Locator(lonlocator, **lonlocator_kw)
                self._lonaxis.set_major_locator(locator)
            if latlocator is not None:
                latlocator_kw = _not_none(
                    latlocator_kw=latlocator_kw,
                    latlines_kw=latlines_kw,
                    default={},
                )
                locator = constructor.Locator(latlocator, **latlocator_kw)
                self._lataxis.set_major_locator(locator)

            # Update minor locators
            lonminorlocator = _not_none(
                lonminorlocator=lonminorlocator, lonminorlines=lonminorlines
            )
            latminorlocator = _not_none(
                latminorlocator=latminorlocator, latminorlines=latminorlines
            )
            if lonminorlocator is not None:
                lonminorlocator_kw = _not_none(
                    lonminorlocator_kw=lonminorlocator_kw,
                    lonminorlines_kw=lonminorlines_kw,
                    default={},
                )
                locator = constructor.Locator(lonminorlocator, **lonminorlocator_kw)
                self._lonaxis.set_minor_locator(locator)
            if latminorlocator is not None:
                latminorlocator_kw = _not_none(
                    latminorlocator_kw=latminorlocator_kw,
                    latminorlines_kw=latminorlines_kw,
                    default={},
                )
                locator = constructor.Locator(latminorlocator, **latminorlocator_kw)
                self._lataxis.set_minor_locator(locator)

            # Update formatters
            loninline = _not_none(
                loninline, inlinelabels, rc.find("grid.inlinelabels", context=True)
            )  # noqa: E501
            latinline = _not_none(
                latinline, inlinelabels, rc.find("grid.inlinelabels", context=True)
            )  # noqa: E501
            rotatelabels = _not_none(
                rotatelabels, rc.find("grid.rotatelabels", context=True)
            )  # noqa: E501
            labelpad = _not_none(labelpad, rc.find("grid.labelpad", context=True))
            dms = _not_none(dms, rc.find("grid.dmslabels", context=True))
            nsteps = _not_none(nsteps, rc.find("grid.nsteps", context=True))
            lon0 = self._get_lon0()

            if lonformatter is not None:
                lonformatter_kw = lonformatter_kw or {}
                formatter = constructor.Formatter(lonformatter, **lonformatter_kw)
                self._lonaxis.set_major_formatter(formatter)
            if latformatter is not None:
                latformatter_kw = latformatter_kw or {}
                formatter = constructor.Formatter(latformatter, **latformatter_kw)
                self._lataxis.set_major_formatter(formatter)
            if dms is not None:  # harmless if these are not GeoLocators
                self._lonaxis.get_major_formatter()._dms = dms
                self._lataxis.get_major_formatter()._dms = dms
                self._lonaxis.get_major_locator()._dms = dms
                self._lataxis.get_major_locator()._dms = dms

            # Apply worker extent, feature, and gridline functions
            lonlim = _not_none(lonlim, default=(None, None))
            latlim = _not_none(latlim, default=(None, None))
            self._update_extent(lonlim=lonlim, latlim=latlim, boundinglat=boundinglat)
            self._update_features()
            self._update_major_gridlines(
                longrid=longrid,
                latgrid=latgrid,  # gridline toggles
                lonarray=lonarray,
                latarray=latarray,  # label toggles
                loninline=loninline,
                latinline=latinline,
                rotatelabels=rotatelabels,
                labelpad=labelpad,
                nsteps=nsteps,
            )
            self._update_minor_gridlines(
                longrid=longridminor,
                latgrid=latgridminor,
                nsteps=nsteps,
            )
        # Set tick lengths for flat projections
        lonticklen = _not_none(lonticklen, ticklen)
        latticklen = _not_none(latticklen, ticklen)
        if lonticklen or latticklen:
            # Only add warning when ticks are given
            if _is_rectilinear_projection(self):
                self._add_geoticks("x", lonticklen, ticklen)
                self._add_geoticks("y", latticklen, ticklen)
                self._update_extent(
                    lonlim=lonlim, latlim=latlim, boundinglat=boundinglat
                )
            else:
                warnings._warn_ultraplot(
                    f"Projection is not rectilinear. Ignoring {lonticklen=} and {latticklen=} settings."
                )

        # Parent format method
        super().format(rc_kw=rc_kw, rc_mode=rc_mode, **kwargs)

    def _add_geoticks(self, x_or_y, itick, ticklen):
        """
        Add tick marks to the geographic axes.

        Parameters
        ----------
        x_or_y : {'x', 'y'}
            The axis to add ticks to ('x' for longitude, 'y' for latitude).
        itick, ticklen : unit-spec, default: :rc:`tick.len`
            Major tick lengths for the x and y axis.
            %(units.pt)s
            Use the argument `ticklen` to set both at once.

        Notes
        -----
        This method handles proper tick mark drawing for geographic projections
        while respecting the current gridline settings.
        """

        size = _not_none(itick, ticklen)
        # Skip if no tick size specified
        if size is None:
            return
        size = units(size) * rc["tick.len"]

        ax = getattr(self, f"{x_or_y}axis")

        # Get the tick positions based on the locator
        gl = self.gridlines_major
        # Note: set_xticks points to a different method than self.[x/y]axis.set_ticks
        # from the mpl backend. For basemap we are adding the ticks to the mpl backend
        # and for cartopy we are simple using their functions by showing the axis.
        if isinstance(gl, tuple):
            locator = gl[0] if x_or_y == "x" else gl[1]
            tick_positions = np.asarray(list(locator.keys()))
            # Turn off the ticks otherwise they are double for
            # basemap (different from cartopy)
            ax.set_major_formatter(mticker.NullFormatter())

        else:
            if x_or_y == "x":
                lim = self._lonaxis.get_view_interval()
                locator = gl.xlocator
                tick_positions = self._lonaxis._get_ticklocs(locator)
            else:
                lim = self._lataxis.get_view_interval()
                locator = gl.ylocator
                tick_positions = self._lataxis._get_ticklocs(locator)

        # Always show the ticks
        ax.set_ticks(tick_positions)
        ax.set_visible(True)

        # Note: set grid_alpha to 0 as it is controlled through the gridlines_major
        # object (which is not the same ticker)
        params = ax.get_tick_params()
        sizes = [size, 0.6 * size if isinstance(size, (int, float)) else size]
        for size, which in zip(sizes, ["major", "minor"]):
            params.update({"length": size})
            params.pop("grid_alpha", None)
            self.tick_params(
                axis=x_or_y,
                which=which,
                grid_alpha=0,
                **params,
            )
        # Apply tick parameters
        # Move the labels outwards if specified
        if hasattr(gl, f"{x_or_y}padding"):
            setattr(gl, f"{x_or_y}padding", 2 * size)
        elif isinstance(gl, tuple):
            # For basemap backends, emulate the label placement
            # like how cartopy does this
            self._add_gridline_labels(ax, gl, padding=size)

        self.stale = True

    def _add_gridline_labels(self, ax, gl, padding=8):
        """
        This function is intended for the Basemap backend
        and mirrors the label placement behavior of Cartopy.
        See: https://scitools.org.uk/cartopy/docs/v0.16/_modules/cartopy/mpl/gridliner.html#Gridliner
        """
        sides = dict()
        for which, formatter in zip("xy", gl):
            for loc, (lines, labels) in formatter.items():
                for i, label in enumerate(labels):
                    upper_end = True
                    position = label.get_position()

                    if which == "x":
                        if position[1] < 0:
                            upper_end = False
                    elif which == "y":
                        if position[0] < 0:
                            upper_end = False
                    line = lines[0] if upper_end else lines[-1]

                    shift_scale = 1 if upper_end else -1
                    path = line.get_path()
                    vertices = path.vertices
                    label.set_transform(line.get_transform())

                    if len(ax.get_major_ticks()) == 0:
                        continue

                    # Get correct line
                    tick = ax.get_major_ticks()[0]
                    which_line = 1 if shift_scale == 1 else 2
                    tickline = getattr(tick, f"tick{which_line}line")
                    position = np.array(label.get_position())
                    # Magic numbers are judged by eye (not great)
                    size = (
                        0.5
                        * (tick._size + label.get_fontsize() + padding)
                        * self.figure.dpi
                        / 72
                    )

                    offset = vertices[0]
                    if upper_end:
                        offset = vertices[-1]

                    if which == "x":
                        # Move y position
                        position[1] = offset[1] + shift_scale * size * 0.65
                        ha = "center"
                        va = "top" if shift_scale == 1 else "bottom"
                        if shift_scale == 1:
                            sides.setdefault("top", []).append(label)
                        else:
                            sides.setdefault("bottom", []).append(label)

                    else:
                        # Move x position
                        position[0] = offset[0] + shift_scale * size * 0.25
                        ha = "left" if shift_scale == 1 else "right"
                        va = "center"
                        if shift_scale == 1:
                            sides.setdefault("right", []).append(label)
                        else:
                            sides.setdefault("left", []).append(label)

                    label.set_position(position)
                    label.set_horizontalalignment(ha)
                    label.set_verticalalignment(va)

        # Some labels are double in the list not sure why
        # Remove them for now
        for key, labels in sides.items():
            seen = set()
            for label in labels:
                pos = label.get_position()
                txt = label.get_text()
                if (pos, txt) not in seen:
                    seen.add((pos, txt))
                else:
                    label.set_visible(False)

    @property
    def gridlines_major(self):
        """
        The cartopy `~cartopy.mpl.gridliner.Gridliner`
        used for major gridlines or a 2-tuple containing the
        (longitude, latitude) major gridlines returned by
        basemap's :func:`~mpl_toolkits.basemap.Basemap.drawmeridians`
        and :func:`~mpl_toolkits.basemap.Basemap.drawparallels`.
        This can be used for customization and debugging.
        """
        if self._name == "basemap":
            return (self._lonlines_major, self._latlines_major)
        else:
            return self._gridlines_major

    @property
    def gridlines_minor(self):
        """
        The cartopy `~cartopy.mpl.gridliner.Gridliner`
        used for minor gridlines or a 2-tuple containing the
        (longitude, latitude) minor gridlines returned by
        basemap's :func:`~mpl_toolkits.basemap.Basemap.drawmeridians`
        and :func:`~mpl_toolkits.basemap.Basemap.drawparallels`.
        This can be used for customization and debugging.
        """
        if self._name == "basemap":
            return (self._lonlines_minor, self._latlines_minor)
        else:
            return self._gridlines_minor

    @property
    def projection(self):
        """
        The cartopy `~cartopy.crs.Projection` or basemap `~mpl_toolkits.basemap.Basemap`
        instance associated with this axes.
        """
        return self._map_projection

    @projection.setter
    def projection(self, map_projection):
        cls = self._proj_class
        if not isinstance(map_projection, cls):
            raise ValueError(f"Projection must be a {cls} instance.")
        self._map_projection = map_projection


class _CartopyAxes(GeoAxes, _GeoAxes):
    """
    Axes subclass for plotting cartopy projections.
    """

    _name = "cartopy"
    _name_aliases = ("geo", "geographic")  # default 'geographic' axes
    _proj_class = Projection
    _proj_north = (
        pproj.NorthPolarStereo,
        pproj.NorthPolarGnomonic,
        pproj.NorthPolarAzimuthalEquidistant,
        pproj.NorthPolarLambertAzimuthalEqualArea,
    )
    _proj_south = (
        pproj.SouthPolarStereo,
        pproj.SouthPolarGnomonic,
        pproj.SouthPolarAzimuthalEquidistant,
        pproj.SouthPolarLambertAzimuthalEqualArea,
    )
    _proj_polar = _proj_north + _proj_south

    # NOTE: The rename argument wrapper belongs here instead of format() because
    # these arguments were previously only accepted during initialization.
    @warnings._rename_kwargs("0.10", circular="round", autoextent="extent")
    def __init__(self, *args, map_projection=None, **kwargs):
        """
        Parameters
        ----------
        map_projection : ~cartopy.crs.Projection
            The map projection.
        *args, **kwargs
            Passed to `GeoAxes`.
        """
        # Initialize axes. Note that critical attributes like outline_patch
        # needed by _format_apply are added before it is called.
        import cartopy  # noqa: F401 verify package is available

        self.projection = map_projection  # verify
        polar = isinstance(self.projection, self._proj_polar)
        latmax = 80 if polar else 90  # default latmax
        self._is_round = False
        self._boundinglat = None  # NOTE: must start at None so _update_extent acts
        self._gridlines_major = None
        self._gridlines_minor = None
        self._lonaxis = _LonAxis(self)
        self._lataxis = _LatAxis(self, latmax=latmax)
        # 'map_projection' argument is deprecated since cartopy 0.21 and
        # replaced by 'projection'.
        if _version_cartopy >= "0.21":
            super().__init__(*args, projection=self.projection, **kwargs)
        else:
            super().__init__(*args, map_projection=self.projection, **kwargs)
        for axis in (self.xaxis, self.yaxis):
            axis.set_tick_params(which="both", size=0)  # prevent extra label offset

    @staticmethod
    def _get_circle_path(N=100):
        """
        Return a circle `~matplotlib.path.Path` used as the outline for polar
        stereographic, azimuthal equidistant, Lambert conformal, and gnomonic
        projections. This was developed from `this cartopy example \
    <https://scitools.org.uk/cartopy/docs/v0.15/examples/always_circular_stereo.html>`__.
        """
        theta = np.linspace(0, 2 * np.pi, N)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        return mpath.Path(verts * radius + center)

    def _get_global_extent(self):
        """
        Return the global extent with meridian properly shifted.
        """
        lon0 = self._get_lon0()
        return [-180 + lon0, 180 + lon0, -90, 90]

    def _get_lon0(self):
        """
        Get the central longitude. Default is ``0``.
        """
        return self.projection.proj4_params.get("lon_0", 0)

    def _init_gridlines(self):
        """
        Create monkey patched "major" and "minor" gridliners managed by ultraplot.
        """

        # Cartopy < 0.18 monkey patch. Helps filter valid coordates to lon_0 +/- 180
        def _axes_domain(self, *args, **kwargs):
            x_range, y_range = type(self)._axes_domain(self, *args, **kwargs)
            if _version_cartopy < "0.18":
                lon_0 = self.axes.projection.proj4_params.get("lon_0", 0)
                x_range = np.asarray(x_range) + lon_0
            return x_range, y_range

        # Cartopy >= 0.18 monkey patch. Fixes issue where cartopy draws an overlapping
        # dateline gridline (e.g. polar maps). See the nx -= 1 line in _draw_gridliner
        def _draw_gridliner(self, *args, **kwargs):  # noqa: E306
            result = type(self)._draw_gridliner(self, *args, **kwargs)
            if _version_cartopy >= "0.18":
                lon_lim, _ = self._axes_domain()
                if abs(np.diff(lon_lim)) == abs(np.diff(self.crs.x_limits)):
                    for collection in self.xline_artists:
                        if not getattr(collection, "_cartopy_fix", False):
                            collection.get_paths().pop(-1)
                            collection._cartopy_fix = True
            return result

        # Return the gridliner with monkey patch
        gl = self.gridlines(crs=ccrs.PlateCarree())
        gl._axes_domain = _axes_domain.__get__(gl)
        gl._draw_gridliner = _draw_gridliner.__get__(gl)
        gl.xlines = gl.ylines = False
        return gl

    @override
    def _get_gridliner_labels(
        self,
        bottom=None,
        top=None,
        left=None,
        right=None,
    ) -> dict[str, list[mtext.Text]]:
        sides = {}
        for dir, side in zip(
            "bottom top left right".split(), [bottom, top, left, right]
        ):
            if side != True:
                continue
            sides[dir] = getattr(self.gridlines_major, f"{dir}_label_artists")
        return sides

    @staticmethod
    def _get_side_labels() -> tuple:
        if _version_cartopy >= "0.18":
            left_labels = "left_labels"
            right_labels = "right_labels"
            bottom_labels = "bottom_labels"
            top_labels = "top_labels"
        else:  # cartopy < 0.18
            left_labels = "ylabels_left"
            right_labels = "ylabels_right"
            bottom_labels = "xlabels_bottom"
            top_labels = "xlabels_top"
        return (left_labels, right_labels, bottom_labels, top_labels)

    def _toggle_gridliner_labels(
        self,
        left=None,
        right=None,
        bottom=None,
        top=None,
        geo=None,
    ):
        """
        Toggle gridliner labels across different cartopy versions.
        """
        left_labels, right_labels, bottom_labels, top_labels = (
            _CartopyAxes._get_side_labels()
        )
        gl = self.gridlines_major
        if left is not None:
            setattr(gl, left_labels, left)
        if right is not None:
            setattr(gl, right_labels, right)
        if bottom is not None:
            setattr(gl, bottom_labels, bottom)
        if top is not None:
            setattr(gl, top_labels, top)
        if geo is not None:  # only cartopy 0.20 supported but harmless
            setattr(gl, "geo_labels", geo)

    def _update_background(self, **kwargs):
        """
        Update the map background patches. This is called in `Axes.format`.
        """
        # TODO: Understand issue where setting global linewidth puts map boundary on
        # top of land patches, but setting linewidth with format() (even with separate
        # format() calls) puts map boundary underneath. Zorder seems to be totally
        # ignored and using spines vs. patch makes no difference.
        # NOTE: outline_patch is redundant, use background_patch instead
        kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
        kw_face["linewidth"] = 0
        kw_edge["facecolor"] = "none"
        if _version_cartopy >= "0.18":
            self.patch.update(kw_face)
            self.spines["geo"].update(kw_edge)
        else:
            self.background_patch.update(kw_face)
            self.outline_patch.update(kw_edge)

    def _update_boundary(self, round=None):
        """
        Update the map boundary path.
        """
        round = _not_none(round, rc.find("geo.round", context=True))
        if round is None or not isinstance(self.projection, self._proj_polar):
            pass
        elif round:
            self._is_round = True
            self.set_boundary(self._get_circle_path(), transform=self.transAxes)
        elif not round and self._is_round:
            if hasattr(self, "_boundary"):
                self._boundary()
            else:
                warnings._warn_ultraplot("Failed to reset round map boundary.")

    def _update_extent_mode(self, extent=None, boundinglat=None):
        """
        Update the extent mode.
        """
        # NOTE: Use set_global rather than set_extent() or _update_extent() for
        # simplicity. Uses projection.[xy]_limits which may not be strictly global.
        # NOTE: For some reason initial call to _set_view_intervals may change the
        # default boundary with extent='auto'. Try this in a robinson projection:
        # ax.contour(np.linspace(-90, 180, N), np.linspace(0, 90, N), np.zeros(N, N))
        extent = _not_none(extent, rc.find("geo.extent", context=True))
        if extent is None:
            return
        if extent not in ("globe", "auto"):
            raise ValueError(
                f"Invalid extent mode {extent!r}. Must be 'auto' or 'globe'."
            )
        polar = isinstance(self.projection, self._proj_polar)
        if not polar:
            self.set_global()
        else:
            if isinstance(self.projection, pproj.NorthPolarGnomonic):
                default_boundinglat = 30
            elif isinstance(self.projection, pproj.SouthPolarGnomonic):
                default_boundinglat = -30
            else:
                default_boundinglat = 0
            boundinglat = _not_none(boundinglat, default_boundinglat)
            self._update_extent(boundinglat=boundinglat)
        if extent == "auto":
            # NOTE: This will work even if applied after plotting stuff
            # and fixing the limits. Very easy to toggle on and off.
            self.set_autoscalex_on(True)
            self.set_autoscaley_on(True)

    def _update_extent(self, lonlim=None, latlim=None, boundinglat=None):
        """
        Set the projection extent.
        """
        # Projection extent
        # NOTE: Lon axis and lat axis extents are updated by set_extent.
        # WARNING: The set_extent method tries to set a *rectangle* between the *4*
        # (x, y) coordinate pairs (each corner), so something like (-180, 180, -90, 90)
        # will result in *line*, causing error! We correct this here.
        eps = 1e-10  # bug with full -180, 180 range when lon_0 != 0
        lon0 = self._get_lon0()
        proj = type(self.projection).__name__
        north = isinstance(self.projection, self._proj_north)
        south = isinstance(self.projection, self._proj_south)
        lonlim = _not_none(lonlim, (None, None))
        latlim = _not_none(latlim, (None, None))
        if north or south:
            if any(_ is not None for _ in (*lonlim, *latlim)):
                warnings._warn_ultraplot(
                    f'{proj!r} extent is controlled by "boundinglat", '
                    f"ignoring lonlim={lonlim!r} and latlim={latlim!r}."
                )
            if boundinglat is not None and boundinglat != self._boundinglat:
                lat0 = 90 if north else -90
                lon0 = self._get_lon0()
                extent = [lon0 - 180 + eps, lon0 + 180 - eps, boundinglat, lat0]
                self.set_extent(extent, crs=ccrs.PlateCarree())
                self._boundinglat = boundinglat

        # Rectangular extent
        else:
            if boundinglat is not None:
                warnings._warn_ultraplot(
                    f'{proj!r} extent is controlled by "lonlim" and "latlim", '
                    f"ignoring boundinglat={boundinglat!r}."
                )
            if any(_ is not None for _ in (*lonlim, *latlim)):
                lonlim = list(lonlim)
                if lonlim[0] is None:
                    lonlim[0] = lon0 - 180
                if lonlim[1] is None:
                    lonlim[1] = lon0 + 180
                lonlim[0] += eps
                latlim = list(latlim)
                if latlim[0] is None:
                    latlim[0] = -90
                if latlim[1] is None:
                    latlim[1] = 90
                extent = lonlim + latlim
                self.set_extent(extent, crs=ccrs.PlateCarree())

    def _update_features(self):
        """
        Update geographic features.
        """
        # NOTE: The e.g. cfeature.COASTLINE features are just for convenience,
        # lo res versions. Use NaturalEarthFeature instead.
        # WARNING: Seems cartopy features cannot be updated! Updating _kwargs
        # attribute does *nothing*.
        reso = rc["reso"]  # resolution cannot be changed after feature created
        try:
            reso = constructor.RESOS_CARTOPY[reso]
        except KeyError:
            raise ValueError(
                f"Invalid resolution {reso!r}. Options are: "
                + ", ".join(map(repr, constructor.RESOS_CARTOPY))
                + "."
            )
        for name, args in constructor.FEATURES_CARTOPY.items():
            # Draw feature or toggle feature off
            b = rc.find(name, context=True)
            attr = f"_{name}_feature"
            feat = getattr(self, attr, None)
            drawn = feat is not None  # if exists, apply *updated* settings
            if b is not None:
                if not b:
                    if drawn:  # toggle existing feature off
                        feat.set_visible(False)
                else:
                    if not drawn:
                        feat = cfeature.NaturalEarthFeature(*args, reso)
                        feat = self.add_feature(feat)  # convert to FeatureArtist
                        setattr(self, attr, feat)

            # Update artist attributes (FeatureArtist._kwargs used back to v0.5).
            # For 'lines', need to specify edgecolor and facecolor
            # See: https://github.com/SciTools/cartopy/issues/803
            if feat is not None:
                kw = rc.category(name, context=drawn)
                if name in ("coast", "rivers", "borders", "innerborders"):
                    if "color" in kw:
                        kw.update({"edgecolor": kw.pop("color"), "facecolor": "none"})
                else:
                    kw.update({"linewidth": 0})
                if "zorder" in kw:
                    # NOTE: Necessary to update zorder directly because _kwargs
                    # attributes are not applied until draw()... at which point
                    # matplotlib is drawing in the order based on the *old* zorder.
                    feat.set_zorder(kw["zorder"])
                if hasattr(feat, "_kwargs"):
                    feat._kwargs.update(kw)
                    if _version_cartopy >= "0.23":
                        feat.set(**feat._kwargs)

    def _update_gridlines(
        self,
        gl,
        which="major",
        longrid=None,
        latgrid=None,
        nsteps=None,
    ):
        """
        Update gridliner object with axis locators, and toggle gridlines on and off.
        """
        # Update gridliner collection properties
        # WARNING: Here we use native matplotlib 'grid' rc param for geographic
        # gridlines. If rc mode is 1 (first format call) use context=False
        kwlines = rc._get_gridline_props(which=which, native=False)
        kwtext = rc._get_ticklabel_props(native=False)
        gl.collection_kwargs.update(kwlines)
        gl.xlabel_style.update(kwtext)
        gl.ylabel_style.update(kwtext)

        # Apply tick locations from dummy _LonAxis and _LatAxis axes
        # NOTE: This will re-apply existing gridline locations if unchanged.
        if nsteps is not None:
            gl.n_steps = nsteps
        latmax = self._lataxis.get_latmax()
        if _version_cartopy >= "0.19":
            gl.ylim = (-latmax, latmax)
        longrid = rc._get_gridline_bool(longrid, axis="x", which=which, native=False)
        if longrid is not None:
            gl.xlines = longrid
        latgrid = rc._get_gridline_bool(latgrid, axis="y", which=which, native=False)
        if latgrid is not None:
            gl.ylines = latgrid
        lonlines = self._get_lonticklocs(which=which)
        latlines = self._get_latticklocs(which=which)
        if _version_cartopy >= "0.18":  # see lukelbd/ultraplot#208
            lonlines = (np.asarray(lonlines) + 180) % 360 - 180  # only for cartopy
        gl.xlocator = mticker.FixedLocator(lonlines)
        gl.ylocator = mticker.FixedLocator(latlines)
        self.stale = True

    def _update_major_gridlines(
        self,
        longrid=None,
        latgrid=None,
        lonarray=None,
        latarray=None,
        loninline=None,
        latinline=None,
        labelpad=None,
        rotatelabels=None,
        nsteps=None,
    ):
        """
        Update major gridlines.
        """
        # Update gridline locations and style
        gl = self._gridlines_major
        if gl is None:
            gl = self._gridlines_major = self._init_gridlines()
        self._update_gridlines(
            gl,
            which="major",
            longrid=longrid,
            latgrid=latgrid,
            nsteps=nsteps,
        )
        gl.xformatter = self._lonaxis.get_major_formatter()
        gl.yformatter = self._lataxis.get_major_formatter()
        # Turn the tick labels off as they are handled
        # separately from the matplotlib defaults
        self.xaxis.set_major_formatter(mticker.NullFormatter())
        self.yaxis.set_major_formatter(mticker.NullFormatter())

        # Update gridline label parameters
        # NOTE: Cartopy 0.18 and 0.19 can not draw both edge and inline labels. Instead
        # requires both a set 'side' and 'x_inline' is True (applied in GeoAxes.format).
        # NOTE: The 'xpadding' and 'ypadding' props were introduced in v0.16
        # with default 5 points, then set to default None in v0.18.
        # TODO: Cartopy has had two formatters for a while but we use the newer one.
        # See https://github.com/SciTools/cartopy/pull/1066
        if labelpad is not None:
            gl.xpadding = labelpad
            gl.ypadding = labelpad
        if loninline is not None:
            gl.x_inline = bool(loninline)
        if latinline is not None:
            gl.y_inline = bool(latinline)
        if rotatelabels is not None:
            gl.rotate_labels = bool(rotatelabels)  # ignored in cartopy < 0.18
        if latinline is not None or loninline is not None:
            lon, lat = loninline, latinline
            b = True if lon and lat else "x" if lon else "y" if lat else None
            gl.inline_labels = b  # ignored in cartopy < 0.20

        # Gridline label toggling
        # Issue warning instead of error!
        if _version_cartopy < "0.18" and not isinstance(
            self.projection, (ccrs.Mercator, ccrs.PlateCarree)
        ):
            if any(latarray):
                warnings._warn_ultraplot(
                    "Cannot add gridline labels to cartopy "
                    f"{type(self.projection).__name__} projection."
                )
                latarray = [False] * 5
            if any(lonarray):
                warnings._warn_ultraplot(
                    "Cannot add gridline labels to cartopy "
                    f"{type(self.projection).__name__} projection."
                )
                lonarray = [False] * 5
        sides = dict()
        # The ordering of these sides are important. The arrays are ordered lrbtg
        for side, lon, lat in zip(
            "left right bottom top geo".split(), lonarray, latarray
        ):
            if lon and lat:
                sides[side] = True
            elif lon:
                sides[side] = "x"
            elif lat:
                sides[side] = "y"
            elif lon is not None or lat is not None:
                sides[side] = False
        self._toggle_gridliner_labels(**sides)

    def _update_minor_gridlines(self, longrid=None, latgrid=None, nsteps=None):
        """
        Update minor gridlines.
        """
        gl = self._gridlines_minor
        if gl is None:
            gl = self._gridlines_minor = self._init_gridlines()
        self._update_gridlines(
            gl,
            which="minor",
            longrid=longrid,
            latgrid=latgrid,
            nsteps=nsteps,
        )

    def get_extent(self, crs=None):
        # Get extent and try to repair longitude bounds.
        if crs is None:
            crs = ccrs.PlateCarree()
        extent = super().get_extent(crs=crs)
        if isinstance(crs, ccrs.PlateCarree):
            if np.isclose(extent[0], -180) and np.isclose(extent[-1], 180):
                # Repair longitude bounds to reflect dateline position
                # NOTE: This is critical so we can prevent duplicate gridlines
                # on dateline. See _update_gridlines.
                lon0 = self._get_lon0()
                extent[:2] = [lon0 - 180, lon0 + 180]
        return extent

    def get_tightbbox(self, renderer, *args, **kwargs):
        # Perform extra post-processing steps
        # For now this just draws the gridliners
        self._apply_axis_sharing()
        if self.get_autoscale_on() and self.ignore_existing_data_limits:
            self.autoscale_view()

        # Adjust location
        if _version_cartopy >= "0.18":
            self.patch._adjust_location()  # this does the below steps
        elif getattr(self.background_patch, "reclip", None) and hasattr(
            self.background_patch, "orig_path"
        ):
            clipped_path = self.background_patch.orig_path.clip_to_bbox(self.viewLim)
            self.outline_patch._path = clipped_path
            self.background_patch._path = clipped_path

        # Apply aspect
        self.apply_aspect()
        if _version_cartopy >= "0.23":
            gridliners = [
                a for a in self.artists if isinstance(a, cgridliner.Gridliner)
            ]
        else:
            gridliners = self._gridliners

        for gl in gridliners:
            if _version_cartopy >= "0.18":
                gl._draw_gridliner(renderer=renderer)
            else:
                gl._draw_gridliner(background_patch=self.background_patch)

        # Remove gridliners
        if _version_cartopy < "0.18":
            self._gridliners = []

        return super().get_tightbbox(renderer, *args, **kwargs)

    def set_extent(self, extent, crs=None):
        # Fix paths, so axes tight bounding box gets correct box! From this issue:
        # https://github.com/SciTools/cartopy/issues/1207#issuecomment-439975083
        # Also record the requested longitude latitude extent so we can use these
        # values for LongitudeLocator and LatitudeLocator. Otherwise if longitude
        # extent is across dateline LongitudeLocator fails because get_extent()
        # reports -180 to 180: https://github.com/SciTools/cartopy/issues/1564
        # NOTE: This is *also* not perfect because if set_extent() was called
        # and extent crosses map boundary of rectangular projection, the *actual*
        # resulting extent is the opposite. But that means user has messed up anyway
        # so probably doesn't matter if gridlines are also wrong.
        if crs is None:
            crs = ccrs.PlateCarree()
        if isinstance(crs, ccrs.PlateCarree):
            self._set_view_intervals(extent)
            with rc.context(mode=2):  # do not reset gridline properties!
                if self._gridlines_major is not None:
                    self._update_gridlines(self._gridlines_major, which="major")
                if self._gridlines_minor is not None:
                    self._update_gridlines(self._gridlines_minor, which="minor")
            if _version_cartopy < "0.18":
                clipped_path = self.outline_patch.orig_path.clip_to_bbox(self.viewLim)
                self.outline_patch._path = clipped_path
                self.background_patch._path = clipped_path
        return super().set_extent(extent, crs=crs)

    def set_global(self):
        # Set up "global" extent and update _LatAxis and _LonAxis view intervals
        result = super().set_global()
        self._set_view_intervals(self._get_global_extent())
        return result


class _BasemapAxes(GeoAxes):
    """
    Axes subclass for plotting basemap projections.
    """

    _name = "basemap"
    _proj_class = Basemap
    _proj_north = ("npaeqd", "nplaea", "npstere")
    _proj_south = ("spaeqd", "splaea", "spstere")
    _proj_polar = _proj_north + _proj_south
    _proj_non_rectangular = _proj_polar + (  # do not use axes spines as boundaries
        "ortho",
        "geos",
        "nsper",
        "moll",
        "hammer",
        "robin",
        "eck4",
        "kav7",
        "mbtfpq",
        "sinu",
        "vandg",
    )

    def __init__(self, *args, map_projection=None, **kwargs):
        """
        Parameters
        ----------
        map_projection : ~mpl_toolkits.basemap.Basemap
            The map projection.
        *args, **kwargs
            Passed to `GeoAxes`.
        """
        # First assign projection and set axis bounds for locators
        # WARNING: Unlike cartopy projections basemaps cannot normally be reused.
        # To make syntax similar we make a copy.
        # WARNING: Investigated whether Basemap.__init__() could be called
        # twice with updated proj kwargs to modify map bounds after creation
        # and python immmediately crashes. Do not try again.
        import mpl_toolkits.basemap  # noqa: F401 verify package is available

        self.projection = copy.copy(map_projection)  # verify
        lon0 = self._get_lon0()
        if self.projection.projection in self._proj_polar:
            latmax = 80  # default latmax for gridlines
            extent = [-180 + lon0, 180 + lon0]
            bound = getattr(self.projection, "boundinglat", 0)
            north = self.projection.projection in self._proj_north
            extent.extend([bound, 90] if north else [-90, bound])
        else:
            latmax = 90
            attrs = ("lonmin", "lonmax", "latmin", "latmax")
            extent = [getattr(self.projection, attr, None) for attr in attrs]
            if any(_ is None for _ in extent):
                extent = [180 - lon0, 180 + lon0, -90, 90]  # fallback

        # Initialize axes
        self._map_boundary = None  # see format()
        self._has_recurred = False  # use this to override plotting methods
        self._lonlines_major = None  # store gridliner objects this way
        self._lonlines_minor = None
        self._latlines_major = None
        self._latlines_minor = None
        self._lonarray = 4 * [False]  # cached label toggles
        self._latarray = 4 * [False]  # cached label toggles
        self._lonaxis = _LonAxis(self)
        self._lataxis = _LatAxis(self, latmax=latmax)
        self._set_view_intervals(extent)
        super().__init__(*args, **kwargs)

        self._turnoff_tick_labels(self._lonlines_major)
        self._turnoff_tick_labels(self._latlines_major)

    def _turnoff_tick_labels(self, locator: mticker.Formatter):
        """
        For GeoAxes with are dealing with a duality. Basemap axes behave differently than Cartopy axes and vice versa. UltraPlot abstracts away from these by providing GeoAxes. For basemap axes we need to turn off the tick labels as they will be handles by GeoAxis
        """
        for loc, objects in locator.items():
            for object in objects:
                # text is wrapped in a list
                if isinstance(object, list) and len(object) > 0:
                    object = object[0]
                if isinstance(object, mtext.Text):
                    object.set_visible(False)

    def _get_lon0(self):
        """
        Get the central longitude.
        """
        return getattr(self.projection, "projparams", {}).get("lon_0", 0)

    @staticmethod
    def _iter_gridlines(dict_):
        """
        Iterate over longitude latitude lines.
        """
        dict_ = dict_ or {}
        for pi in dict_.values():
            for pj in pi:
                for obj in pj:
                    yield obj

    def _update_background(self, **kwargs):
        """
        Update the map boundary patches. This is called in `Axes.format`.
        """
        # Non-rectangular projections
        # WARNING: Map boundary must be drawn before all other tasks. See __init__.
        # WARNING: With clipping on boundary lines are clipped by the axes bbox.
        if self.projection.projection in self._proj_non_rectangular:
            self.patch.set_facecolor("none")  # make sure main patch is hidden
            kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
            kw = {**kw_face, **kw_edge, "rasterized": False, "clip_on": False}
            self._map_boundary.update(kw)
        # Rectangular projections
        else:
            kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
            self.patch.update({**kw_face, "edgecolor": "none"})
            for spine in self.spines.values():
                spine.update(kw_edge)

    def _update_boundary(self, round=None):
        """
        No-op. Boundary mode cannot be changed in basemap.
        """
        # NOTE: Unlike the cartopy method we do not look up the rc setting here.
        if round is None:
            return
        else:
            warnings._warn_ultraplot(
                f"Got round={round!r}, but you cannot change the bounds of a polar "
                "basemap projection after creating it. Please pass 'round' to uplt.Proj "  # noqa: E501
                "instead (e.g. using the uplt.subplots() dictionary keyword 'proj_kw')."
            )

    def _update_extent_mode(self, extent=None, boundinglat=None):  # noqa: U100
        """
        No-op. Extent mode cannot be changed in basemap.
        """
        # NOTE: Unlike the cartopy method we do not look up the rc setting here.
        if extent is None:
            return
        if extent not in ("globe", "auto"):
            raise ValueError(
                f"Invalid extent mode {extent!r}. Must be 'auto' or 'globe'."
            )
        if extent == "auto":
            warnings._warn_ultraplot(
                f"Got extent={extent!r}, but you cannot use auto extent mode "
                "in basemap projections. Please consider switching to cartopy."
            )

    def _update_extent(self, lonlim=None, latlim=None, boundinglat=None):
        """
        No-op. Map bounds cannot be changed in basemap.
        """
        lonlim = _not_none(lonlim, (None, None))
        latlim = _not_none(latlim, (None, None))
        if boundinglat is not None or any(_ is not None for _ in (*lonlim, *latlim)):
            warnings._warn_ultraplot(
                f"Got lonlim={lonlim!r}, latlim={latlim!r}, boundinglat={boundinglat!r}"
                ', but you cannot "zoom into" a basemap projection after creating it. '
                "Please pass any of the following keyword arguments to uplt.Proj "
                "instead (e.g. using the uplt.subplots() dictionary keyword 'proj_kw'):"
                "'boundinglat', 'lonlim', 'latlim', 'llcrnrlon', 'llcrnrlat', "
                "'urcrnrlon', 'urcrnrlat', 'llcrnrx', 'llcrnry', 'urcrnrx', 'urcrnry', "
                "'width', or 'height'."
            )

    def _update_features(self):
        """
        Update geographic features.
        """
        # NOTE: Also notable are drawcounties, blumarble, drawlsmask,
        # shadedrelief, and etopo methods.
        for name, method in constructor.FEATURES_BASEMAP.items():
            # Draw feature or toggle on and off
            b = rc.find(name, context=True)
            attr = f"_{name}_feature"
            feat = getattr(self, attr, None)
            drawn = feat is not None  # if exists, apply *updated* settings
            if b is not None:
                if not b:
                    if drawn:  # toggle existing feature off
                        for obj in feat:
                            feat.set_visible(False)
                else:
                    if not drawn:
                        feat = getattr(self.projection, method)(ax=self)
                    if not isinstance(feat, (list, tuple)):  # list of artists?
                        feat = (feat,)
                    setattr(self, attr, feat)

            # Update settings
            if feat is not None:
                kw = rc.category(name, context=drawn)
                for obj in feat:
                    obj.update(kw)

    def _update_gridlines(
        self,
        which="major",
        longrid=None,
        latgrid=None,
        lonarray=None,
        latarray=None,
    ):
        """
        Apply changes to the basemap axes.
        """
        latmax = self._lataxis.get_latmax()
        for axis, name, grid, array, method in zip(
            ("x", "y"),
            ("lon", "lat"),
            (longrid, latgrid),
            (lonarray, latarray),
            ("drawmeridians", "drawparallels"),
        ):
            # Correct lonarray and latarray label toggles by changing from lrbt to lrtb.
            # Then update the cahced toggle array. This lets us change gridline locs
            # while preserving the label toggle setting from a previous format() call.
            grid = rc._get_gridline_bool(grid, axis=axis, which=which, native=False)
            axis = getattr(self, f"_{name}axis")
            if len(array) == 5:  # should be always
                array = array[:4]
            bools = 4 * [False] if which == "major" else getattr(self, f"_{name}array")
            array = [*array[:2], *array[2:4][::-1]]  # flip lrbt to lrtb and skip geo
            for i, b in enumerate(array):
                if b is not None:
                    bools[i] = b  # update toggles

            # Get gridlines
            # NOTE: This may re-apply existing gridlines.
            lines = list(getattr(self, f"_get_{name}ticklocs")(which=which))
            if name == "lon" and np.isclose(lines[0] + 360, lines[-1]):
                lines = lines[:-1]  # prevent double labels
            # Figure out whether we have to redraw meridians/parallels
            # NOTE: Always update minor gridlines if major locator also changed
            attr = f"_{name}lines_{which}"
            objs = getattr(self, attr)  # dictionary of previous objects
            attrs = ["isDefault_majloc"]  # always check this one
            attrs.append("isDefault_majfmt" if which == "major" else "isDefault_minloc")
            rebuild = lines and (
                not objs
                or any(_ is not None for _ in array)  # user-input or initial toggles
                or any(not getattr(axis, attr) for attr in attrs)  # none tracked yet
            )
            if rebuild and objs and grid is None:  # get *previous* toggle state
                grid = all(obj.get_visible() for obj in self._iter_gridlines(objs))

            # Draw or redraw meridian or parallel lines
            # Also mark formatters and locators as 'default'
            if rebuild:
                kwdraw = {}
                formatter = axis.get_major_formatter()
                if formatter is not None:  # use functional formatter
                    kwdraw["fmt"] = formatter
                for obj in self._iter_gridlines(objs):
                    obj.set_visible(False)
                objs = getattr(self.projection, method)(
                    lines, ax=self, latmax=latmax, labels=bools, **kwdraw
                )
                setattr(self, attr, objs)

            # Update gridline settings
            # We use native matplotlib 'grid' rc param for geographic gridlines
            kwlines = rc._get_gridline_props(which=which, native=False, rebuild=rebuild)
            kwtext = rc._get_ticklabel_props(native=False, rebuild=rebuild)
            for obj in self._iter_gridlines(objs):
                if isinstance(obj, mtext.Text):
                    obj.update(kwtext)
                else:
                    obj.update(kwlines)

            # Toggle existing gridlines on and off
            if grid is not None:
                for obj in self._iter_gridlines(objs):
                    if not isinstance(obj, mtext.Text):
                        obj.set_visible(grid)

    def _update_major_gridlines(
        self,
        longrid=None,
        latgrid=None,
        lonarray=None,
        latarray=None,
        loninline=None,
        latinline=None,
        rotatelabels=None,
        labelpad=None,
        nsteps=None,
    ):
        """
        Update major gridlines.
        """
        loninline, latinline, labelpad, rotatelabels, nsteps  # avoid U100 error
        self._update_gridlines(
            which="major",
            longrid=longrid,
            latgrid=latgrid,
            lonarray=lonarray,
            latarray=latarray,
        )
        sides = {}
        for side, lonon, laton in zip(
            "left right top bottom geo".split(), lonarray, latarray
        ):
            if lonon or laton:
                sides[side] = True
        self._toggle_gridliner_labels(**sides)

    def _update_minor_gridlines(self, longrid=None, latgrid=None, nsteps=None):
        """
        Update minor gridlines.
        """
        # Update gridline locations
        nsteps  # avoid U100 error
        array = [None] * 4  # NOTE: must be None not False (see _update_gridlines)
        self._update_gridlines(
            which="minor",
            longrid=longrid,
            latgrid=latgrid,
            lonarray=array,
            latarray=array,
        )
        # Set isDefault_majloc, etc. to True for both axes
        # NOTE: This cannot be done inside _update_gridlines or minor gridlines
        # will not update to reflect new major gridline locations.
        for axis in (self._lonaxis, self._lataxis):
            axis.isDefault_majfmt = True
            axis.isDefault_majloc = True
            axis.isDefault_minloc = True

    @override
    def _get_gridliner_labels(
        self,
        bottom=None,
        top=None,
        left=None,
        right=None,
    ):
        # For basemap object, the text is organized
        # as a dictionary. The keys are the numerical
        # location values, and the values are a list
        # where the version item is the tick and the
        # the rest are mtext.Text objects. The labels
        # are clustereed on the location per axis.
        # This means that top and bottom labels are assigned
        # to the same numerical loc.
        # We therefore create a mapping per direction to make
        # it more semantically logical.
        def group_labels(
            labels: list[mtext.Text],
            which: str,
            bottom=None,
            top=None,
            left=None,
            right=None,
        ) -> dict[str, list[mtext.Text]]:
            group = {}
            # We take zero here as a baseline
            for label in labels:
                position = label.get_position()
                target = None
                if which == "x":
                    if bottom is not None and position[1] < 0:
                        target = "bottom"
                    elif top is not None and position[1] >= 0:
                        target = "top"
                else:
                    if left is not None and position[0] < 0:
                        target = "left"
                    elif right is not None and position[0] >= 0:
                        target = "right"
                if target is not None:
                    group[target] = group.get(target, []) + [label]
            return group

        # Group the text object based on their location
        grouped = {}
        for which, gl in zip("xy", self.gridlines_major):
            for loc, (line, labels) in gl.items():
                tmp = group_labels(
                    labels=labels,
                    which=which,
                    bottom=bottom,
                    top=top,
                    left=left,
                    right=right,
                )
                for key, values in tmp.items():
                    grouped[key] = grouped.get(key, []) + values
        return grouped


# Apply signature obfuscation after storing previous signature
GeoAxes._format_signatures[GeoAxes] = inspect.signature(GeoAxes.format)
GeoAxes.format = docstring._obfuscate_kwargs(GeoAxes.format)


def _is_rectilinear_projection(ax):
    """Check if the axis has a flat projection (works with Cartopy)."""
    # Determine what the projection function is
    # Create a square and determine if the lengths are preserved
    # For geoaxes projc is always set in format, and thus is not None
    proj = getattr(ax, "projection", None)
    transform = None
    if hasattr(proj, "transform_point"):  # cartopy
        if proj.transform_point is not None:
            transform = partial(proj.transform_point, src_crs=proj.as_geodetic())
    elif hasattr(proj, "projection"):  # basemap
        transform = proj

    if transform is not None:
        # Create three collinear points (in a straight line)
        line_points = [(0, 0), (10, 10), (20, 20)]

        # Transform the points using the projection
        transformed_points = [transform(x, y) for x, y in line_points]

        # Check if the transformed points are still collinear
        # Points are collinear if the slopes between consecutive points are equal
        x0, y0 = transformed_points[0]
        x1, y1 = transformed_points[1]
        x2, y2 = transformed_points[2]

        # Calculate slopes
        xdiff1 = x1 - x0
        xdiff2 = x2 - x1
        if np.allclose(xdiff1, 0) or np.allclose(xdiff2, 0):  # Avoid division by zero
            # Check if both are vertical lines
            return np.allclose(xdiff1, 0) and np.allclose(xdiff2, 0)

        slope1 = (y1 - y0) / xdiff1
        slope2 = (y2 - y1) / xdiff2

        # If slopes are equal (within a small tolerance), the projection preserves straight lines
        return np.allclose(slope1 - slope2, 0)
    # Cylindrical projections are generally rectilinear
    rectilinear_projections = {
        # Cartopy projections
        "platecarree",
        "mercator",
        "lambertcylindrical",
        "miller",
        # Basemap projections
        "cyl",
        "merc",
        "mill",
        "rect",
        "rectilinear",
        "unknown",
    }

    # For Cartopy
    if hasattr(proj, "name"):
        return proj.name.lower() in rectilinear_projections
    # For Basemap
    elif hasattr(proj, "projection"):
        return proj.projection.lower() in rectilinear_projections
    # If we can't determine, assume it's not rectilinear
    return False
