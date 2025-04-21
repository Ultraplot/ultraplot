from matplotlib.colorbar import Colorbar
import matplotlib as mpl, numpy as np
import matplotlib.contour as mcontour
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
import matplotlib.ticker as mticker


from ultraplot import rc
from .internals import _not_none, warnings, guides, _pop_params
from .internals.docstring import _snippet_manager
from .utils import units
from . import colors as pcolors
from . import ticker as pticker
from . import constructor


class UltraColorbar(Colorbar):
    """
    Enhanced colorbar class that extends matplotlib's Colorbar
    with additional functionality for appearance customization
    and better control over ticks, labels, and formatting.
    """

    _args_docstring = """
    mappable : mappable, colormap-spec, sequence of color-spec, \
    or sequence of `~matplotlib.artist.Artist`
        There are four options here:

        1. A `~matplotlib.cm.ScalarMappable` (e.g., an object returned by
           `~ultraplot.axes.PlotAxes.contourf` or `~ultraplot.axes.PlotAxes.pcolormesh`).
        2. A `~matplotlib.colors.Colormap` or registered colormap name used to build a
           `~matplotlib.cm.ScalarMappable` on-the-fly. The colorbar range and ticks depend
           on the arguments `values`, `vmin`, `vmax`, and `norm`. The default for a
           :class:`~ultraplot.colors.ContinuousColormap` is ``vmin=0`` and ``vmax=1`` (note that
           passing `values` will "discretize" the colormap). The default for a
           :class:`~ultraplot.colors.DiscreteColormap` is ``values=np.arange(0, cmap.N)``.
        3. A sequence of hex strings, color names, or RGB[A] tuples. A
           :class:`~ultraplot.colors.DiscreteColormap` will be generated from these colors and
           used to build a `~matplotlib.cm.ScalarMappable` on-the-fly. The colorbar
           range and ticks depend on the arguments `values`, `norm`, and
           `norm_kw`. The default is ``values=np.arange(0, len(mappable))``.
        4. A sequence of `matplotlib.artist.Artist` instances (e.g., a list of
           `~matplotlib.lines.Line2D` instances returned by `~ultraplot.axes.PlotAxes.plot`).
           A colormap will be generated from the colors of these objects (where the
           color is determined by ``get_color``, if available, or ``get_facecolor``).
           The colorbar range and ticks depend on the arguments `values`, `norm`, and
           `norm_kw`. The default is to infer colorbar ticks and tick labels
           by calling `~matplotlib.artist.Artist.get_label` on each artist.

    values : sequence of float or str, optional
        Ignored if `mappable` is a `~matplotlib.cm.ScalarMappable`. This maps the colormap
        colors to numeric values using `~ultraplot.colors.DiscreteNorm`. If the colormap is
        a :class:`~ultraplot.colors.ContinuousColormap` then its colors will be "discretized".
        These These can also be strings, in which case the list indices are used for
        tick locations and the strings are applied as tick labels.
    """
    _kwargs_docstring = """
    orientation : {None, 'horizontal', 'vertical'}, optional
        The colorbar orientation. By default this depends on the "side" of the subplot
        or figure where the colorbar is drawn. Inset colorbars are always horizontal.
    norm : norm-spec, optional
        Ignored if `mappable` is a `~matplotlib.cm.ScalarMappable`. This is the continuous
        normalizer used to scale the :class:`~ultraplot.colors.ContinuousColormap` (or passed
        to `~ultraplot.colors.DiscreteNorm` if `values` was passed). Passed to the
        `~ultraplot.constructor.Norm` constructor function.
    norm_kw : dict-like, optional
        Ignored if `mappable` is a `~matplotlib.cm.ScalarMappable`. These are the
        normalizer keyword arguments. Passed to `~ultraplot.constructor.Norm`.
    vmin, vmax : float, optional
        Ignored if `mappable` is a `~matplotlib.cm.ScalarMappable`. These are the minimum
        and maximum colorbar values. Passed to `~ultraplot.constructor.Norm`.
    label, title : str, optional
        The colorbar label. The `title` keyword is also accepted for
        consistency with `~matplotlib.axes.Axes.legend`.
    reverse : bool, optional
        Whether to reverse the direction of the colorbar. This is done automatically
        when descending levels are used with `~ultraplot.colors.DiscreteNorm`.
    rotation : float, default: 0
        The tick label rotation.
    grid, edges, drawedges : bool, default: :rc:`colorbar.grid`
        Whether to draw "grid" dividers between each distinct color.
    extend : {'neither', 'both', 'min', 'max'}, optional
        Direction for drawing colorbar "extensions" (i.e. color keys for out-of-bounds
        data on the end of the colorbar). Default behavior is to use the value of `extend`
        passed to the plotting command or use ``'neither'`` if the value is unknown.
    extendfrac : float, optional
        The length of the colorbar "extensions" relative to the length of the colorbar.
        This is a native matplotlib `~matplotlib.figure.Figure.colorbar` keyword.
    extendsize : unit-spec, default: :rc:`colorbar.extend` or :rc:`colorbar.insetextend`
        The length of the colorbar "extensions" in physical units. Default is
        :rcraw:`colorbar.extend` for outer colorbars and :rcraw:`colorbar.insetextend`
        for inset colorbars. %(units.em)s
    extendrect : bool, default: False
        Whether to draw colorbar "extensions" as rectangles. If ``False`` then
        the extensions are drawn as triangles.
    locator, ticks : locator-spec, optional
        Used to determine the colorbar tick positions. Passed to the
        `~ultraplot.constructor.Locator` constructor function. By default
        `~matplotlib.ticker.AutoLocator` is used for continuous color levels
        and `~ultraplot.ticker.DiscreteLocator` is used for discrete color levels.
    locator_kw : dict-like, optional
        Keyword arguments passed to `matplotlib.ticker.Locator` class.
    minorlocator, minorticks
        As with `locator`, `ticks` but for the minor ticks. By default
        `~matplotlib.ticker.AutoMinorLocator` is used for continuous color levels
        and `~ultraplot.ticker.DiscreteLocator` is used for discrete color levels.
    minorlocator_kw
        As with `locator_kw`, but for the minor ticks.
    format, formatter, ticklabels : formatter-spec, optional
        The tick label format. Passed to the `~ultraplot.constructor.Formatter`
        constructor function.
    formatter_kw : dict-like, optional
        Keyword arguments passed to `matplotlib.ticker.Formatter` class.
    frame, frameon : bool, default: :rc:`colorbar.frameon`
        For inset colorbars only. Indicates whether to draw a "frame",
        just like `~matplotlib.axes.Axes.legend`.
    tickminor : bool, optional
        Whether to add minor ticks using `~matplotlib.colorbar.ColorbarBase.minorticks_on`.
    tickloc, ticklocation : {'bottom', 'top', 'left', 'right'}, optional
        Where to draw tick marks on the colorbar. Default is toward the outside
        of the subplot for outer colorbars and ``'bottom'`` for inset colorbars.
    tickdir, tickdirection : {'out', 'in', 'inout'}, default: :rc:`tick.dir`
        Direction of major and minor colorbar ticks.
    ticklen : unit-spec, default: :rc:`tick.len`
        Major tick lengths for the colorbar ticks.
    ticklenratio : float, default: :rc:`tick.lenratio`
        Relative scaling of `ticklen` used to determine minor tick lengths.
    tickwidth : unit-spec, default: `linewidth`
        Major tick widths for the colorbar ticks.
        or :rc:`tick.width` if `linewidth` was not passed.
    tickwidthratio : float, default: :rc:`tick.widthratio`
        Relative scaling of `tickwidth` used to determine minor tick widths.
    ticklabelcolor, ticklabelsize, ticklabelweight \
    : default: :rc:`tick.labelcolor`, :rc:`tick.labelsize`, :rc:`tick.labelweight`.
        The font color, size, and weight for colorbar tick labels
    labelloc, labellocation : {'bottom', 'top', 'left', 'right'}
        The colorbar label location. Inherits from `tickloc` by default. Default is toward
        the outside of the subplot for outer colorbars and ``'bottom'`` for inset colorbars.
    labelcolor, labelsize, labelweight \
    : default: :rc:`label.color`, :rc:`label.size`, and :rc:`label.weight`.
        The font color, size, and weight for the colorbar label.
    a, alpha, framealpha, fc, facecolor, framecolor, ec, edgecolor, ew, edgewidth : default\
    : :rc:`colorbar.framealpha`, :rc:`colorbar.framecolor`
        For inset colorbars only. Controls the transparency and color of
        the background frame.
    lw, linewidth, c, color : optional
        Controls the line width and edge color for both the colorbar
        outline and the level dividers.
    %(axes.edgefix)s
    rasterize : bool, default: :rc:`colorbar.rasterize`
        Whether to rasterize the colorbar solids. The matplotlib default was ``True``
        but ultraplot changes this to ``False`` since rasterization can cause misalignment
        between the color patches and the colorbar outline.
    **kwargs
        Passed to `~matplotlib.figure.Figure.colorbar`.
    """

    def __init__(
        self,
        ax,
        mappable,
        values=None,
        *,
        loc=None,
        align=None,
        space=None,
        pad=None,
        width=None,
        length=None,
        shrink=None,
        label=None,
        title=None,
        reverse=False,
        rotation=None,
        grid=None,
        edges=None,
        drawedges=None,
        extend=None,
        extendsize=None,
        extendfrac=None,
        ticks=None,
        locator=None,
        locator_kw=None,
        format=None,
        formatter=None,
        ticklabels=None,
        formatter_kw=None,
        minorticks=None,
        minorlocator=None,
        minorlocator_kw=None,
        tickminor=None,
        ticklen=None,
        ticklenratio=None,
        tickdir=None,
        tickdirection=None,
        tickwidth=None,
        tickwidthratio=None,
        ticklabelsize=None,
        ticklabelweight=None,
        ticklabelcolor=None,
        labelloc=None,
        labellocation=None,
        labelsize=None,
        labelweight=None,
        labelcolor=None,
        c=None,
        color=None,
        lw=None,
        linewidth=None,
        edgefix=None,
        rasterized=None,
        **kwargs,
    ):
        """
        Initialize the enhanced colorbar with extended options.

        Parameters
        ----------
        ax : matplotlib Axes
            The parent axes for the colorbar
        mappable : matplotlib ScalarMappable
            The mappable whose colormap and norm will be used
        values : array-like, optional
            The values to use for colormap normalization

        And many other parameters for customization...
        """
        # Process and store parameters
        self.parent_ax = ax
        self._params = self._process_input_parameters(
            length,
            shrink,
            title,
            label,
            labelloc,
            labellocation,
            ticks,
            locator,
            ticklabels,
            formatter,
            format,
            minorticks,
            minorlocator,
            c,
            color,
            lw,
            linewidth,
            grid,
            edges,
            drawedges,
            ticklen,
            tickdir,
            tickdirection,
            tickwidth,
            ticklenratio,
            tickwidthratio,
            rasterized,
            reverse,
            extendsize,
            loc,
        )

        # Build styling keyword dictionaries
        self._kw_dicts = self._build_keyword_dicts(
            labelsize,
            labelweight,
            labelcolor,
            ticklabelsize,
            ticklabelweight,
            ticklabelcolor,
            rotation,
            locator_kw,
            formatter_kw,
            minorlocator_kw,
            kwargs,
        )

        # Handle the colorbar axes
        cax, kwargs = self._prepare_axes(
            ax,
            loc,
            align,
            self._params["length"],
            width,
            space,
            pad,
            self._params["label"],
            extendsize,
            kwargs,
        )

        # Process the mappable
        mappable, kwargs = self._process_mappable(mappable, values, cax, kwargs)

        # Handle extend settings
        self._params["extendfrac"] = self._process_extend(
            cax, self._params["extendsize"], extendfrac, kwargs
        )

        # Process tick locators and formatters
        locator, minorlocator, formatter, tickminor = self._process_ticks(
            mappable.norm,
            self._params["locator"],
            self._kw_dicts["locator_kw"],
            minorlocator,
            self._kw_dicts["minorlocator_kw"],
            self._params["formatter"],
            self._kw_dicts["formatter_kw"],
            tickminor,
        )

        # Handle extend for non-ContourSet
        if not isinstance(mappable, mcontour.ContourSet):
            kwargs["extend"] = _not_none(extend, "neither")
        elif extend is not None and extend != mappable.extend:
            warnings._warn_ultraplot(
                f"Ignoring extend={extend!r}. ContourSet extend cannot be changed."
            )

        # Initialize the parent matplotlib colorbar
        super().__init__(
            ax=cax,
            mappable=mappable,
            ticks=locator,
            format=formatter,
            drawedges=self._params["grid"],
            **kwargs,
        )

        # Set initial colorbar settings
        self._configure_colorbar(minorlocator, tickminor)

        # Update appearance
        self._update_appearance(loc, labelloc, edgefix)

    def _process_input_parameters(
        self,
        length,
        shrink,
        title,
        label,
        labelloc,
        labellocation,
        ticks,
        locator,
        ticklabels,
        formatter,
        format,
        minorticks,
        minorlocator,
        c,
        color,
        lw,
        linewidth,
        grid,
        edges,
        drawedges,
        ticklen,
        tickdir,
        tickdirection,
        tickwidth,
        ticklenratio,
        tickwidthratio,
        rasterized,
        reverse,
        extendsize,
        loc,
    ):
        """Process and normalize colorbar parameters."""
        params = {}
        params["length"] = _not_none(length=length, shrink=shrink)
        params["label"] = _not_none(title=title, label=label)
        params["labelloc"] = _not_none(labelloc=labelloc, labellocation=labellocation)
        params["locator"] = _not_none(ticks=ticks, locator=locator)
        params["formatter"] = _not_none(
            ticklabels=ticklabels, formatter=formatter, format=format
        )
        params["minorlocator"] = _not_none(
            minorticks=minorticks, minorlocator=minorlocator
        )
        params["color"] = _not_none(c=c, color=color, default=rc["axes.edgecolor"])
        params["linewidth"] = _not_none(lw=lw, linewidth=linewidth)
        params["ticklen"] = units(_not_none(ticklen, rc["tick.len"]), "pt")
        params["tickdir"] = _not_none(tickdir=tickdir, tickdirection=tickdirection)
        params["tickwidth"] = units(
            _not_none(tickwidth, linewidth, rc["tick.width"]), "pt"
        )
        params["linewidth"] = units(
            _not_none(linewidth, default=rc["axes.linewidth"]), "pt"
        )
        params["ticklenratio"] = _not_none(ticklenratio, rc["tick.lenratio"])
        params["tickwidthratio"] = _not_none(tickwidthratio, rc["tick.widthratio"])
        params["rasterized"] = _not_none(rasterized, rc["colorbar.rasterized"])
        params["grid"] = _not_none(
            grid=grid, edges=edges, drawedges=drawedges, default=rc["colorbar.grid"]
        )
        if loc in ("fill", "left", "right", "top", "bottom"):
            params["extendsize"] = _not_none(extendsize, rc["colorbar.extend"])
        else:
            params["extendsize"] = _not_none(extendsize, rc["colorbar.insetextend"])

        params["reverse"] = reverse

        return params

    def _build_keyword_dicts(
        self,
        labelsize,
        labelweight,
        labelcolor,
        ticklabelsize,
        ticklabelweight,
        ticklabelcolor,
        rotation,
        locator_kw,
        formatter_kw,
        minorlocator_kw,
        kwargs,
    ):
        """Build keyword argument dictionaries for labels and tickers."""
        kw_dicts = {}

        # Label formatting
        kw_dicts["label"] = {}
        for key, value in (
            ("size", labelsize),
            ("weight", labelweight),
            ("color", labelcolor),
        ):
            if value is not None:
                kw_dicts["label"][key] = value

        # Tick label formatting
        kw_dicts["ticklabels"] = {}
        for key, value in (
            ("size", ticklabelsize),
            ("weight", ticklabelweight),
            ("color", ticklabelcolor),
            ("rotation", rotation),
        ):
            if value is not None:
                kw_dicts["ticklabels"][key] = value

        # Ticker keyword args
        kw_dicts["locator_kw"] = locator_kw or {}
        kw_dicts["formatter_kw"] = formatter_kw or {}
        kw_dicts["minorlocator_kw"] = minorlocator_kw or {}

        # Handle deprecated parameters
        for b, kw in enumerate((kw_dicts["locator_kw"], kw_dicts["minorlocator_kw"])):
            key = "maxn_minor" if b else "maxn"
            name = "minorlocator" if b else "locator"
            nbins = kwargs.pop("maxn_minor" if b else "maxn", None)
            if nbins is not None:
                kw["nbins"] = nbins
                warnings._warn_ultraplot(
                    f"The colorbar() keyword {key!r} was deprecated in v0.10. To "
                    "achieve the same effect, you can pass 'nbins' to the new default "
                    f"locator DiscreteLocator using {name}_kw={{'nbins': {nbins}}}."
                )

        return kw_dicts

    def _prepare_axes(
        self,
        parent_ax,
        loc,
        align,
        length,
        width,
        space,
        pad,
        label,
        extendsize,
        kwargs,
    ):
        """Prepare colorbar axes based on location."""
        if loc in ("fill", "left", "right", "top", "bottom"):
            length = _not_none(length, rc["colorbar.length"])
            kwargs.update({"align": align, "length": length})
            extendsize = _not_none(extendsize, rc["colorbar.extend"])
            ax = parent_ax._add_guide_panel(
                loc, align, length=length, width=width, space=space, pad=pad
            )
            cax, kwargs = ax._parse_colorbar_filled(**kwargs)
        else:
            kwargs.update({"label": label, "length": length, "width": width})
            extendsize = _not_none(extendsize, rc["colorbar.insetextend"])
            cax, kwargs = parent_ax._parse_colorbar_inset(loc=loc, pad=pad, **kwargs)

        return cax, kwargs

    def _process_mappable(self, mappable, values, cax, kwargs):
        """Process the colorbar mappable."""
        # Handle special case of 1D methods with artist list
        if (
            np.iterable(mappable)
            and len(mappable) == 1
            and isinstance(mappable[0], mcm.ScalarMappable)
        ):
            mappable = mappable[0]

        if not isinstance(mappable, mcm.ScalarMappable):
            mappable, kwargs = cax._parse_colorbar_arg(mappable, values, **kwargs)
        else:
            pop = _pop_params(kwargs, cax._parse_colorbar_arg, ignore_internal=True)
            if pop:
                warnings._warn_ultraplot(
                    f"Input is already a ScalarMappable. "
                    f"Ignoring unused keyword arg(s): {pop}"
                )

        return mappable, kwargs

    def _process_extend(self, cax, extendsize, extendfrac, kwargs):
        """Process colorbar extend size and fraction."""
        # Determine orientation
        vert = kwargs.get("orientation", "vertical") == "vertical"

        if extendsize is not None and extendfrac is not None:
            warnings._warn_ultraplot(
                f"You cannot specify both an absolute extendsize={extendsize!r} "
                f"and a relative extendfrac={extendfrac!r}. Ignoring 'extendfrac'."
            )
            extendfrac = None

        if extendfrac is None:
            width, height = cax._get_size_inches()
            scale = height if vert else width
            extendsize = units(extendsize, "em", "in")
            extendfrac = extendsize / max(scale - 2 * extendsize, units(1, "em", "in"))

        return extendfrac

    def _process_ticks(
        self,
        norm,
        locator,
        locator_kw,
        minorlocator,
        minorlocator_kw,
        formatter,
        formatter_kw,
        tickminor,
    ):
        """Process colorbar tick locators and formatters."""
        formatter = _not_none(formatter, getattr(norm, "_labels", None), "auto")
        formatter_kw.setdefault("tickrange", (norm.vmin, norm.vmax))
        formatter = constructor.Formatter(formatter, **formatter_kw)
        categorical = isinstance(formatter, mticker.FixedFormatter)

        if locator is not None:
            locator = constructor.Locator(locator, **locator_kw)

        if minorlocator is not None:  # overrides tickminor
            minorlocator = constructor.Locator(minorlocator, **minorlocator_kw)
        elif tickminor is None:
            orientation = getattr(self, "orientation", "vertical")
            tickminor = (
                False
                if categorical
                else rc["xy"[orientation == "vertical"] + "tick.minor.visible"]
            )

        if isinstance(norm, mcolors.BoundaryNorm):
            ticks = getattr(norm, "_ticks", norm.boundaries)
            segmented = isinstance(getattr(norm, "_norm", None), pcolors.SegmentedNorm)

            if locator is None:
                if categorical or segmented:
                    locator = mticker.FixedLocator(ticks)
                else:
                    locator = pticker.DiscreteLocator(ticks)

            if tickminor and minorlocator is None:
                minorlocator = pticker.DiscreteLocator(ticks, minor=True)

        # Handle empty locators
        if isinstance(locator, mticker.NullLocator):
            minorlocator, tickminor = None, False
        elif (
            hasattr(locator, "locs")
            and isinstance(locator.locs, (list, np.ndarray))
            and len(locator.locs) == 0
        ):
            minorlocator, tickminor = None, False

        return locator, minorlocator, formatter, tickminor

    def _configure_colorbar(self, minorlocator, tickminor):
        """Configure initial colorbar settings."""
        self.ax.grid(False)

        # Update ticks method for backwards compatibility
        # self.update_ticks = guides._update_ticks.__get__(self)

        # Set minor ticks
        if minorlocator is not None:
            current = self.minorlocator
            if current != minorlocator:
                self.minorlocator = minorlocator
            self.update_ticks()
        elif tickminor:
            self.minorticks_on()
        else:
            self.minorticks_off()

        # Handle norm inversion
        axis = self._long_axis()
        if getattr(self.norm, "descending", None):
            axis.set_inverted(True)
        if self._params.get("reverse", False):
            axis.set_inverted(True)

    def _long_axis(self):
        """Return the long axis of the colorbar (x for horizontal, y for vertical)."""
        return self.ax.yaxis if self.orientation == "vertical" else self.ax.xaxis

    def _short_axis(self):
        """Return the short axis of the colorbar (x for vertical, y for horizontal)."""
        return self.ax.xaxis if self.orientation == "vertical" else self.ax.yaxis

    def _update_appearance(self, loc, labelloc, edgefix):
        """Update colorbar appearance settings."""
        # Get the primary axis
        axis = self._long_axis()

        # Update tick parameters
        axis.set_tick_params(
            which="both", color=self._params["color"], direction=self._params["tickdir"]
        )
        axis.set_tick_params(
            which="major",
            length=self._params["ticklen"],
            width=self._params["tickwidth"],
        )
        axis.set_tick_params(
            which="minor",
            length=self._params["ticklen"] * self._params["ticklenratio"],
            width=self._params["tickwidth"] * self._params["tickwidthratio"],
        )

        # Set label if provided
        if self._params["label"] is not None:
            if loc in ("top", "bottom"):
                if labelloc in (None, "top", "bottom"):
                    self.set_label(self._params["label"])
                elif labelloc in ("left", "right"):
                    self.ax.set_ylabel(self._params["label"])
                else:
                    raise ValueError("Could not determine position")
            elif loc in ("left", "right"):
                if labelloc in (None, "left", "right"):
                    self.set_label(self._params["label"])
                elif labelloc in ("top", "bottom"):
                    self.ax.set_xlabel(self._params["label"])
                else:
                    raise ValueError("Could not determine position")
            else:
                self.set_label(self._params["label"])

        # Update label position if specified
        if labelloc is not None:
            # Update axis to short when modifying labels
            if loc in ("top", "bottom") and labelloc in ("left", "right"):
                axis = self._short_axis()
            elif loc in ("left", "right") and labelloc in ("top", "bottom"):
                axis = self._short_axis()
            axis.set_label_position(labelloc)

        # Update style of labels
        axis.label.update(self._kw_dicts["label"])
        for label in self._long_axis().get_ticklabels():
            label.update(self._kw_dicts["ticklabels"])

        # Update outline appearance
        kw_outline = {
            "edgecolor": self._params["color"],
            "linewidth": self._params["linewidth"],
        }
        if self.outline is not None:
            self.outline.update(kw_outline)
        if self.dividers is not None:
            self.dividers.update(kw_outline)

        # Set rasterization and edge fixes
        if self.solids:
            from .axes import PlotAxes

            self.solids.set_rasterized(self._params["rasterized"])
            PlotAxes._fix_patch_edges(self.solids, edgefix=edgefix)

    # Add additional methods to extend functionality
    def update_label(self, label=None, **kwargs):
        """
        Update the colorbar label with new text and/or styling.

        Parameters
        ----------
        label : str, optional
            The new label text
        **kwargs
            Additional styling parameters for the label
        """
        if label is not None:
            self._params["label"] = label
            self.set_label(label)

        if kwargs:
            self._kw_dicts["label"].update(kwargs)
            self._long_axis().label.update(kwargs)

    def update_ticks(self, locator=None, formatter=None, manual_only=False, **kwargs):
        """
        Update tick locators and formatters.

        Parameters
        ----------
        locator : Locator or str, optional
            The new tick locator
        formatter : Formatter or str, optional
            The new tick formatter
        **kwargs
            Additional parameters for tick configuration
        """
        # Implementation would depend on the actual tick update logic

        """
        Refined colorbar tick updater without subclassing.
        """
        # TODO: Add this to generalized colorbar subclass?
        # NOTE: Matplotlib 3.5+ does not define _use_auto_colorbar_locator since
        # ticks are always automatically adjusted by its colorbar subclass. This
        # override is thus backwards and forwards compatible.

        axis = self._long_axis()

        if locator is not None:
            locator = constructor.Locator(locator)
            axis.set_major_locator(locator)

        if formatter is not None:
            formatter = constructor.Formatter(formatter)
            axis.set_major_formatter(formatter)

        # Update tick parameters if provided
        if kwargs:
            axis.set_tick_params(**kwargs)
        attr = "_use_auto_colorbar_locator"
        if not hasattr(self, attr) or getattr(self, attr)():
            if manual_only:
                pass
            else:
                super().update_ticks()  # AutoMinorLocator auto updates
        else:
            super().update_ticks()  # update necessary
            minorlocator = getattr(self, "minorlocator", None)
            if minorlocator is None:
                pass
            elif hasattr(self, "_ticker"):
                # Use ticker method if available
                ticks, *_ = self._ticker(self.minorlocator, mticker.NullFormatter())
                axis = (
                    self.ax.yaxis if self.orientation == "vertical" else self.ax.xaxis
                )
                axis.set_ticks(ticks, minor=True)
                axis.set_ticklabels([], minor=True)
            else:
                # Fall back to using MinorLocator directly
                if hasattr(minorlocator, "tick_values"):
                    try:
                        vmin, vmax = axis.get_view_interval()
                        ticks = minorlocator.tick_values(vmin, vmax)
                        axis.set_ticks(ticks, minor=True)
                        axis.set_ticklabels([], minor=True)
                    except Exception:
                        warnings._warn_ultraplot(
                            f"Cannot use user-input colorbar minor locator {minorlocator!r} (error computing ticks). Turning on minor ticks instead."
                        )
                        self.minorlocator = None
                        self.minorticks_on()  # at least turn them on
                else:
                    warnings._warn_ultraplot(
                        f"Cannot use user-input colorbar minor locator {minorlocator!r} (older matplotlib version). Turning on minor ticks instead."
                    )  # noqa: E501
                    self.minorlocator = None
                    self.minorticks_on()  # at least turn them on


_snippet_manager["ultracolorbar"] = (
    UltraColorbar._args_docstring + UltraColorbar._kwargs_docstring
)
