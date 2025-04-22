from typing import MutableMapping, List, Tuple, Union, Optional, Any, Iterable

# Import dataclass components
from dataclasses import dataclass, field, fields

# Import matplotlib components
from matplotlib.colorbar import Colorbar
import matplotlib as mpl, numpy as np
import matplotlib.contour as mcontour
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
import matplotlib.ticker as mticker
import matplotlib.container as mcontainer  # Added for container check

# Assume internal imports are correct based on the file context (e.g., ProPlot)
from ultraplot import rc
from .internals import _not_none, warnings, guides, _pop_params
from .internals.docstring import _snippet_manager
from .utils import units, edges
from . import colors as pcolors
from . import constructor
from . import ticker as pticker

# Define basic type hints if not available globally
Number = Union[int, float]


# Define maps for processing kwargs - Keep outside class
# Map dataclass field name -> list of kwargs aliases (in preference order)
KWARGS_ALIASES = {
    "length": ["length", "shrink"],
    "label": ["title", "label"],
    "labelloc": ["labelloc", "labellocation"],
    "locator": ["ticks", "locator"],  # User-provided spec/object
    "formatter": ["ticklabels", "formatter", "format"],  # User-provided spec/object
    "minorlocator": ["minorticks", "minorlocator"],  # User-provided spec/object
    # Note: 'color', 'tickdir', extend* parameters, and grid/edges/drawedges
    # have slightly different or dedicated handling below.
}

# Map dataclass field name -> default value if not found via aliases or kwargs directly
# These are defaults applied during settings initialization
FIELD_DEFAULTS = {
    "reverse": False,
    "grid": rc["colorbar.grid"],  # Default for 'grid' field, also used by aliases
    "rasterized": rc["colorbar.rasterized"],
    "color": rc["axes.edgecolor"],  # Default for 'color' field, also used by alias 'c'
    "linewidth": rc["axes.linewidth"],
    "ticklen": rc["tick.len"],
    "tickwidth": rc["tick.width"],
    "ticklenratio": rc["tick.lenratio"],
    "tickwidthratio": rc["tick.widthratio"],
    "extendrect": False,  # Default for extendrect
    # Note: Default for extendsize depends on loc, handled in _finalize_extends
    # Note: Default for extendfrac is calculated, handled in _finalize_extends
    # Note: Default for loc, align, space, pad, width, values is None (from dataclass definition)
    # Note: Default for locator_kw, formatter_kw, minorlocator_kw is {} (from dataclass field default)
    # Note: Default for tickminor, rotation, labelsize, labelweight, labelcolor,
    # ticklabelsize, ticklabelweight, ticklabelcolor is None (from dataclass definition)
}

# Define which fields need the units() conversion *after* getting the value from _not_none
UNITIZED_FIELDS = ["linewidth", "ticklen", "tickwidth"]


@dataclass(slots=True)
class UltraColorbarSettings:
    # --- Optional fields - will get values from kwargs or defaults ---
    # These fields are not covered by KWARGS_ALIASES map, handled by direct lookup
    loc: str | None = None  # Location string ('right', 'bottom', etc.)
    align: str | None = None
    space: float | None = None
    pad: float | None = None
    width: float | None = None
    orientation: str | None = (
        None  # 'vertical' or 'horizontal' - Crucial for extendfrac calculation (derived)
    )

    # --- Parameters processed via KWARGS_ALIASES map ---
    # Define all target fields from KWARGS_ALIASES here
    length: float | None = None  # target for length/shrink alias
    label: str | None = None  # target for label/title alias
    labelloc: str | None = None  # target for labelloc/labellocation alias

    # --- Parameters with simple aliases or direct mapping + defaults ---
    color: str | None = None  # target for color/c alias
    tickdir: str | None = None  # target for tickdir/tickdirection alias
    ticklenratio: float | None = None
    tickwidthratio: float | None = None
    linewidth: float | None = (
        None  # target for linewidth alias (also alias for tickwidth)
    )
    ticklen: float | None = None
    tickwidth: float | None = None  # target for tickwidth/linewidth aliases

    # --- Tick/Label/Formatter specs (user inputs, processed before settings creation) ---
    # These are the processed spec/object or kw dicts after maxn/maxn_minor handling
    locator: Any | None = None
    formatter: Any | None = None
    minorlocator: Any | None = None
    locator_kw: dict = field(default_factory=dict)  # Default to empty dict
    formatter_kw: dict = field(default_factory=dict)
    minorlocator_kw: dict = field(default_factory=dict)
    tickminor: bool | None = None  # User requested tickminor on/off
    rotation: float | None = None  # Tick label rotation

    # Specific text/label formatting params (user inputs)
    ticklabelsize: Number | None = None
    ticklabelweight: str | None = None
    ticklabelcolor: str | None = None
    labelsize: Number | None = None
    labelweight: str | None = None
    labelcolor: str | None = None

    # --- Display flags with defaults ---
    reverse: bool = False  # target for reverse alias
    grid: bool = False  # target for grid/edges/drawedges aliases
    rasterized: bool = False  # target for rasterized alias
    extendrect: bool = False  # default False

    # --- Extend parameters (raw inputs) ---
    extendsize: float | None = None
    extendfrac: float | None = None

    # --- Derived/Calculated parameters (calculated *after* __init__) ---
    # orientation is also derived, but needed for _finalize_extends, so can be set before
    _calculated_extendfrac: float | None = field(
        default=None, init=False
    )  # Calculated in _finalize_extends

    # The __init__ takes a dictionary of kwargs (after initial preprocessing in Colorbar.__init__)
    def __init__(self, **kwargs):
        # Iterate through all fields defined in the dataclass
        all_fields_dict = {f.name: f for f in fields(self)}
        # Fields handled internally (derived or calculated *after* init)
        # Note: Orientation is set externally before calling _finalize_extends
        internal_fields = {"_calculated_extendfrac"}

        for field_name, field_obj in all_fields_dict.items():
            if field_name in internal_fields:
                continue  # Skip fields derived later

            # Get value from kwargs, handling aliases and defaults
            # Use the alias mapping if the field is a target for aliases
            aliases = KWARGS_ALIASES.get(field_name)
            if aliases:
                not_none_args = {alias: kwargs.get(alias, None) for alias in aliases}
                default_value = FIELD_DEFAULTS.get(
                    field_name, field_obj.default
                )  # Prioritize FIELD_DEFAULTS
                not_none_args["default"] = default_value
                value = _not_none(**not_none_args)

                # Apply units conversion if needed
                if field_name in UNITIZED_FIELDS:
                    if value is not None:
                        value = units(value, "pt")  # Assuming "pt" is the target unit

            else:
                # Fields without aliases get value directly from kwargs or default
                default_value = FIELD_DEFAULTS.get(
                    field_name, field_obj.default
                )  # Prioritize FIELD_DEFAULTS

                # Handle specific simple aliases using _not_none (not in KWARGS_ALIASES map)
                if field_name == "color":
                    value = _not_none(
                        c=kwargs.get("c", None),
                        color=kwargs.get("color", None),
                        default=default_value,
                    )
                elif field_name == "tickdir":
                    value = _not_none(
                        tickdir=kwargs.get("tickdir", None),
                        tickdirection=kwargs.get("tickdirection", None),
                        default=default_value,
                    )
                elif field_name == "grid":
                    value = _not_none(
                        grid=kwargs.get("grid", None),
                        edges=kwargs.get("edges", None),
                        drawedges=kwargs.get("drawedges", None),
                        default=default_value,
                    )
                # Handle extend parameters explicitly - they don't use _not_none aliases logic
                # and their default comes later in _finalize_extends. Get raw value from kwargs.
                elif field_name in ("extendsize", "extendfrac"):
                    value = kwargs.get(
                        field_name, field_obj.default
                    )  # Default is None from dataclass field

                # Handle locator/formatter/minorlocator kws - get dict directly
                # These should be the dicts potentially modified by maxn/maxn_minor handling
                # Default factory ensures empty dict if not in kwargs or None
                elif field_name in ("locator_kw", "formatter_kw", "minorlocator_kw"):
                    value = kwargs.get(field_name, field_obj.default)

                else:
                    # General case: direct kwarg lookup with default fallback
                    # This covers fields like loc, align, space, pad, width, rotation,
                    # tickminor, labelsize, labelweight, labelcolor, ticklabelsize, etc.
                    value = kwargs.get(field_name, default_value)

            # Set the attribute on the instance
            setattr(self, field_name, value)

    def _finalize_extends(self, cax: "Axes"):
        """
        Process colorbar extend size and fraction using the actual colorbar axes.
        Sets the _calculated_extendfrac attribute.

        This method requires self.orientation and self.loc to be set.
        """
        # Get initial values stored in the settings object
        extendsize_raw = self.extendsize  # User input extendsize (None or value)
        extendfrac_raw = self.extendfrac  # User input extendfrac (None or value)
        orientation = (
            self.orientation
        )  # Determined orientation ('vertical' or 'horizontal')
        loc = self.loc  # User input loc string

        # Validate required inputs for calculation
        if orientation is None:
            # This shouldn't happen if orientation is determined before calling
            warnings._warn_ultraplot(
                "UltraColorbarSettings._finalize_extends called before orientation was determined."
            )
            self._calculated_extendfrac = None
            return

        # --- Logic from original _get_extendfrac ---
        # Prioritize extendfrac if both are given
        if extendsize_raw is not None and extendfrac_raw is not None:
            warnings._warn_ultraplot(
                f"You cannot specify both an absolute extendsize={extendsize_raw!r} "
                f"and a relative extendfrac={extendfrac_raw!r}. Ignoring 'extendsize'."
            )
            # Use the raw user value for extendfrac
            calculated_extendfrac = extendfrac_raw

        # Calculate extendfrac if it was not specified initially (i.e., extendfrac_raw is None)
        elif extendfrac_raw is None:
            # Determine the default extendsize based on loc
            if loc in ("fill", "left", "right", "top", "bottom"):  # Outer panels
                default_extendsize_based_on_loc = rc["colorbar.extend"]
            else:  # Inset or other loc
                default_extendsize_based_on_loc = rc["colorbar.insetextend"]

            # Use _not_none to get the effective extendsize (user-provided extendsize or default)
            effective_extendsize = _not_none(
                extendsize=extendsize_raw, default=default_extendsize_based_on_loc
            )

            # If effective_extendsize is still None (e.g. rc param was None), cannot calculate frac
            if effective_extendsize is None:
                warnings._warn_ultraplot(
                    "Effective extendsize is None, cannot calculate extendfrac."
                )
                calculated_extendfrac = None  # Cannot calculate
            else:
                # Perform the extendfrac calculation using the effective_extendsize and cax size
                # Assuming cax has _get_size_inches() method from ProPlot or similar custom Axes class
                width, height = cax._get_size_inches()
                scale = height if orientation == "vertical" else width

                # Need to ensure effective_extendsize is converted to inches for comparison/division
                effective_extendsize_in_inches = units(
                    effective_extendsize, "em", "in"
                )  # Assuming 'em' input unit

                # Ensure minimum scale for division based on the original logic (1 em minimum length)
                min_scale_for_division = units(1, "em", "in")  # Convert 1 em to inches

                # Denominator is the length of the colorbar body excluding the extends
                denominator = max(
                    scale - 2 * effective_extendsize_in_inches, min_scale_for_division
                )

                # Ensure denominator is positive to avoid division by zero or negative results
                if denominator <= 0:
                    warnings._warn_ultraplot(
                        f"Calculated length for colorbar body is zero or negative ({scale=:.2f} in, {effective_extendsize_in_inches=:.2f} in). Cannot calculate extendfrac."
                    )
                    calculated_extendfrac = None
                else:
                    calculated_extendfrac = effective_extendsize_in_inches / denominator

        else:  # extendfrac_raw is not None, extendsize_raw is None - use user provided frac
            calculated_extendfrac = extendfrac_raw

        # Store the final calculated/user-provided extend fraction on the settings object
        self._calculated_extendfrac = calculated_extendfrac

        # Method doesn't need to return value, just updates state


class UltraColorbar(Colorbar):
    """
    Enhanced colorbar class that extends matplotlib's ColorbarBase
    with additional functionality for appearance customization
    and better control over ticks, labels, and formatting,
    integrated with UltraPlot's units and settings system.
    """

    # --- Docstrings (assuming already present and correct) ---
    _args_docstring = """..."""
    _kwargs_docstring = """..."""

    def __init__(
        self,
        ax,  # parent axes
        mappable,  # initial mappable/spec/list
        values=None,  # initial values list
        *,  # all subsequent args must be keywords
        # Explicit parameters matching the original __init__ signature
        # These will be combined with **kwargs and parsed by UltraColorbarSettings
        # norm, norm_kw, vmin, vmax are *not* passed to settings, they are for mappable processing
        norm=None,
        norm_kw=None,
        vmin=None,
        vmax=None,
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
        extendrect=False,  # Added extendrect explicit arg
        # Deprecated args - included for handling but ideally discouraged in user code
        maxn=None,
        maxn_minor=None,
        **kwargs,  # catch any further unknown kwargs
    ):
        # Store parent ax
        self.parent_ax = ax

        # 0. Combine explicit args and **kwargs into a single dictionary for settings parsing.
        # Process deprecated/aliased kwargs (like maxn/maxn_minor) on this combined dictionary.
        combined_settings_kwargs = kwargs.copy()  # Start with **kwargs

        # Add explicit __init__ arguments to the dictionary, prioritizing them.
        # Note: norm, norm_kw, vmin, vmax, values are *not* added here, they are
        # used only by _process_input_mappable. 'extend' is also processed separately.
        explicit_args_for_settings = {
            "loc": loc,
            "align": align,
            "space": space,
            "pad": pad,
            "width": width,
            "length": length,
            "shrink": shrink,
            "label": label,
            "title": title,
            "reverse": reverse,
            "rotation": rotation,
            "grid": grid,
            "edges": edges,
            "drawedges": drawedges,
            "extendsize": extendsize,
            "extendfrac": extendfrac,  # Raw extend size/frac passed to settings
            "ticks": ticks,
            "locator": locator,
            "locator_kw": locator_kw,
            "format": format,
            "formatter": formatter,
            "ticklabels": ticklabels,
            "formatter_kw": formatter_kw,
            "minorticks": minorticks,
            "minorlocator": minorlocator,
            "minorlocator_kw": minorlocator_kw,
            "tickminor": tickminor,
            "ticklen": ticklen,
            "ticklenratio": ticklenratio,
            "tickdir": tickdir,
            "tickdirection": tickdirection,
            "tickwidth": tickwidth,
            "tickwidthratio": tickwidthratio,
            "ticklabelsize": ticklabelsize,
            "ticklabelweight": ticklabelweight,
            "ticklabelcolor": ticklabelcolor,
            "labelloc": labelloc,
            "labellocation": labellocation,
            "labelsize": labelsize,
            "labelweight": labelweight,
            "labelcolor": labelcolor,
            "c": c,
            "color": color,
            "lw": lw,
            "linewidth": linewidth,
            "edgefix": edgefix,
            "rasterized": rasterized,
            "extendrect": extendrect,
            "maxn": maxn,
            "maxn_minor": maxn_minor,  # Include deprecated args here for processing
        }
        for key, value in explicit_args_for_settings.items():
            if value is not None:
                combined_settings_kwargs[key] = value

        # Process deprecated maxn/maxn_minor on the locator_kw/minorlocator_kw within combined_settings_kwargs
        # Get potentially existing kw dicts (will be {} if not in combined_settings_kwargs)
        user_locator_kw = combined_settings_kwargs.get("locator_kw", {})
        user_minorlocator_kw = combined_settings_kwargs.get("minorlocator_kw", {})

        # Handle maxn/maxn_minor if present in combined_settings_kwargs
        maxn_val = combined_settings_kwargs.pop("maxn", None)
        maxn_minor_val = combined_settings_kwargs.pop("maxn_minor", None)

        if maxn_val is not None:
            user_locator_kw["nbins"] = maxn_val
            combined_settings_kwargs["locator_kw"] = user_locator_kw  # Put it back
            warnings._warn_ultraplot(
                "The colorbar() keyword 'maxn' was deprecated in vX.Y. To achieve the same effect, use locator_kw={'nbins': ...}."
            )
        if maxn_minor_val is not None:
            user_minorlocator_kw["nbins"] = maxn_minor_val
            combined_settings_kwargs["minorlocator_kw"] = (
                user_minorlocator_kw  # Put it back
            )
            warnings._warn_ultraplot(
                "The colorbar() keyword 'maxn_minor' was deprecated in vX.Y. To achieve the same effect, use minorlocator_kw={'nbins': ...}."
            )

        # 1. Process input mappable, norm, values.
        # This static method takes the *initial* mappable/specs and norm/value specs.
        # It does NOT take or consume **kwargs from the combined dict.
        processed_mappable, processed_values = UltraColorbar._process_input_mappable(
            mappable,
            values_in=values,
            norm_in=norm,
            norm_kw_in=norm_kw,
            vmin_in=vmin,
            vmax_in=vmax,
        )

        # 2. Create settings object from the combined_settings_kwargs.
        # The settings object will store all parameters parsed from kwargs.
        settings = UltraColorbarSettings(**combined_settings_kwargs)
        self._settings = settings  # Store settings on the instance

        # 3. Prepare the colorbar axes (cax). This uses settings and CONSUMES kwargs from combined_settings_kwargs.
        # Pass parent_ax and the combined_settings_kwargs dict.
        # _prepare_axes modifies combined_settings_kwargs in place by popping used keys.
        cax, remaining_kwargs_after_axes_prep = self._prepare_axes(
            self.parent_ax, self._settings, combined_settings_kwargs
        )
        self.ax = cax  # Set the colorbar axes as self.ax

        # 4. Finalize settings that depend on cax or other derived values.
        # Determine orientation
        # Use the determined orientation as a default if settings.orientation was None
        determined_orientation = guides._get_orientation(self._settings.loc)
        self._settings.orientation = _not_none(
            self._settings.orientation, determined_orientation
        )

        # Calculate final extendfrac using the settings and the created axes
        self._settings._finalize_extends(
            cax
        )  # This sets self._settings._calculated_extendfrac

        # 5. Process tick locators/formatters based on the processed_mappable.norm and settings.
        # _process_ticks needs processed_mappable.norm and reads specs/kws from settings.
        final_locator, final_minorlocator, final_formatter, final_tickminor = (
            self._process_ticks(processed_mappable.norm, self._settings)
        )

        # 6. Build kwargs for super().__init__ from settings and processed objects.
        # These are the explicit arguments ColorbarBase takes.
        # remaining_kwargs_after_axes_prep are passed as **kwargs to super().
        # Ensure explicit args override anything in remaining_kwargs_after_axes_prep if duplicated.
        super_init_kwargs = {
            "ax": self.ax,  # The created cax
            "mappable": processed_mappable,
            "ticks": final_locator,  # The mpl locator object
            "format": final_formatter,  # The mpl formatter object
            "drawedges": self._settings.grid,  # From settings
            "extend": processed_mappable.extend,  # Get extend type from the processed mappable
            "extendfrac": self._settings._calculated_extendfrac,  # Use the calculated fraction from settings
            "orientation": self._settings.orientation,  # Use the determined orientation from settings
            "label": self._settings.label,  # Text label from settings
            "ticklocation": self._settings.labelloc,  # mpl arg name for tick side
            "tickdirection": self._settings.tickdir,  # mpl arg name for tick direction
            "rasterized": self._settings.rasterized,  # From settings
            "extendrect": self._settings.extendrect,  # From settings
            # ColorbarBase also takes `alpha`, `norm`, `cmap`, `boundaries`, `values`.
            # norm/cmap/boundaries/values come implicitly from `mappable` (processed_mappable).
            # `alpha` is not explicitly in settings. It might be passed via remaining **kwargs.
        }

        # Combine explicit super args with any remaining kwargs.
        # Explicit args from settings/processed objects take precedence.
        final_super_kwargs = (
            remaining_kwargs_after_axes_prep.copy()
        )  # Start with what's left after axes prep
        final_super_kwargs.update(super_init_kwargs)  # Overlay explicit args

        # 7. Call super().__init__ with the final kwargs dict.
        super().__init__(**final_super_kwargs)

        # 8. Configure initial colorbar settings (minor ticks, norm inversion).
        # Use the final mpl minor locator and the final tickminor flag
        self._configure_colorbar(final_minorlocator, final_tickminor)

        # 9. Update appearance using the settings.
        self._update_appearance()  # Reads from self._settings

    # --- Static/Helper Methods ---

    @staticmethod
    def _process_input_mappable(
        mappable_in: Any,  # Use a different name to avoid shadowing param in __init__
        values_in: List[Union[float, str, None]] | None = None,
        norm_in: Any | None = None,  # Norm spec or object
        norm_kw_in: dict | None = None,
        vmin_in: Number | None = None,
        vmax_in: Number | None = None,
    ) -> Tuple["ScalarMappable", List[Union[float, str, None]] | None]:
        """
        Process flexible colorbar input (mappable/spec/list) into a ScalarMappable
        and determine associated values/labels.

        Takes initial mappable/spec/values/norm/vmin/vmax inputs.
        Does NOT take or consume **kwargs.
        Returns the processed ScalarMappable and the final values list (can be None).
        """
        # Handle container objects if input is iterable
        if (
            np.iterable(mappable_in)
            and len(mappable_in) > 0
            and all(isinstance(obj, mcontainer.Container) for obj in mappable_in)
        ):
            mappable = [
                obj[0] for obj in mappable_in
            ]  # Get first artist from each container
        else:
            mappable = mappable_in  # Use the input directly otherwise

        # Initial determination of cmap and initial values (if derived from artists or discrete cmap)
        cmap = None
        initial_values_from_mappable = (
            None  # Values potentially inferred *from* the mappable input type
        )

        # Use match statement for different input types
        match mappable:
            # Already a ScalarMappable
            case mcm.ScalarMappable():
                # If input is already mappable, use it directly.
                # Norm/values args provided by user are ignored (handled in __init__ warning)
                processed_mappable = mappable
                # Final values list is user-provided values_in, or None if not provided
                final_values = values_in
                # Return early as mappable is already processed
                return processed_mappable, final_values

            # Colormap object or string name
            case mcolors.Colormap() | str():
                cmap = constructor.Colormap(mappable)
                # If discrete cmap and values wasn't provided by user, prepare discrete values
                # (indices 0..N-1, potentially None placeholders for labels)
                if values_in is None and isinstance(cmap, pcolors.DiscreteColormap):
                    initial_values_from_mappable = [None] * cmap.N

            # List of colors
            case np.iterable(mappable) if all(
                mcolors.is_color_like(obj) for obj in mappable
            ):
                cmap = pcolors.DiscreteColormap(list(mappable), "_no_name")
                # If values wasn't provided by user, prepare discrete values (indices 0..N-1)
                if values_in is None:
                    initial_values_from_mappable = np.arange(
                        len(mappable)
                    ).tolist()  # Use indices as default values

            # List of artists (check for color/facecolor getters)
            case np.iterable(mappable) if all(
                hasattr(obj, "get_color") or hasattr(obj, "get_facecolor")
                for obj in mappable
            ):
                # This static method infers cmap (DiscreteColormap from artist colors)
                # and values (list populated with labels if available) from artists
                cmap, initial_values_from_mappable = (
                    UltraColorbar._infer_cmap_and_values_from(
                        artists=mappable,
                        values=values_in,  # Pass user-provided values_in as a starting point for labels
                    )
                )

            case _:
                # If none of the above, raise error
                raise ValueError(
                    "Input colorbar() argument must be a scalar mappable, colormap name "
                    f"or object, list of colors, or list of artists. Got {mappable!r}."
                )

        # If we reached here, cmap was successfully determined (from spec/list/artists)
        # Now determine the final norm and values list

        # Prioritize user-provided input_values_in over inferred initial_values_from_mappable
        final_values = _not_none(
            values=values_in, initial_values=initial_values_from_mappable
        )

        # If a values list is provided, create a discrete norm
        if final_values is not None:
            # This static method infers or creates norm/cmap based on final_values
            # (and user-provided norm_in spec/obj and the determined cmap_obj)
            final_norm, final_cmap = UltraColorbar._infer_norm_and_cmap_from(
                final_values, norm_in, cmap
            )

        else:  # No values list provided, create a continuous norm
            # Use user-provided norm spec/kw/vmin/vmax
            final_norm = UltraColorbar._make_norm(
                norm=norm_in,
                norm_kw=norm_kw_in,
                vmin=vmin_in,
                vmax=vmax_in,
            )
            final_cmap = cmap  # Use the cmap determined from input

        # Create the final ScalarMappable
        processed_mappable = mcm.ScalarMappable(norm=final_norm, cmap=final_cmap)
        # processed_values is already finalized as final_values

        # Return the processed mappable and the final values list
        return processed_mappable, final_values

    # _infer_cmap_and_values_from (static) - seems mostly correct from previous analysis
    @staticmethod
    def _infer_cmap_and_values_from(
        artists: List[Any],  # Use Any for artist type hint if no base class available
        values_in: (
            List[Union[float, str, None]] | None
        ),  # Allow None elements in input values
    ) -> Tuple["Colormap", List[Union[float, str, None]]]:
        """
        Infers a DiscreteColormap from artist colors and populates a values list
        using artist labels where the list elements are None.
        """
        # Generate colormap from colors
        colors = []
        for artist in artists:
            # for e.g. pcolor
            if hasattr(artist, "update_scalarmappable"):
                artist.update_scalarmappable()

            # Get color, prioritizing get_color
            color = None
            if hasattr(artist, "get_color"):
                color = artist.get_color()
            elif hasattr(artist, "get_facecolor"):
                color = artist.get_facecolor()
            else:
                # If no color getter, raise error for this artist type
                raise ValueError(
                    f"Cannot make colorbar from artist type {type(artist).__name__}: No color attribute found."
                )

            # Handle potential color arrays (e.g., single color scatter)
            if isinstance(color, np.ndarray):
                color = color.squeeze()
                # After squeeze, check if it's still multi-dimensional or too long to be a single color
                if (
                    color.ndim > 0 and color.size > 4
                ):  # Check if it's more than a single RGBA color array
                    raise ValueError(
                        "Cannot make colorbar from artists with multi-color attributes or non-color attributes."
                    )

            # Final check if the obtained color is a valid color specification
            if not mcolors.is_color_like(color):
                raise ValueError(
                    f"Cannot make colorbar from artist with invalid color specification: {color!r}."
                )

            colors.append(color)

        # If no colors were successfully extracted (e.g. input list was empty or only contained unhandled types)
        if not colors:
            raise ValueError(
                "Cannot make colorbar from artists: no valid colors could be extracted."
            )

        # Create the discrete colormap from the extracted colors
        cmap = pcolors.DiscreteColormap(colors, "_no_name")

        # Populate the values list, prioritizing user input, then artist labels
        if values_in is None:
            # If user didn't provide values, create a list of None placeholders
            processed_values = [None] * len(artists)
        else:
            # Use a mutable copy of the user-provided list
            processed_values = list(values_in)
            # Optionally, warn if the length doesn't match the number of artists/colors
            if len(processed_values) != len(artists):
                warnings._warn_ultraplot(
                    f"Provided values list has length {len(processed_values)}, "
                    f"but there are {len(artists)} artists. Labels may not align correctly."
                )

        # Populate the values list with labels where the slot is None
        # Iterate over artists and the (potentially shorter) values list
        for i, artist in enumerate(artists):
            # Only attempt to get label if the corresponding slot exists and is None
            if i < len(processed_values) and processed_values[i] is None:
                label = artist.get_label() if hasattr(artist, "get_label") else None
                if label and label[0] != "_":  # Skip default private labels
                    processed_values[i] = label  # Assign label if valid

        # The processed_values list might still contain None if no label was found for a slot
        return cmap, processed_values

    # _infer_norm_and_cmap_from (static) - seems correct based on previous analysis
    @staticmethod
    def _infer_norm_and_cmap_from(
        values: List[
            Union[float, str, None]
        ],  # Must be a list if this method is called
        norm_spec_in: Any | None,  # User input norm spec/object
        cmap_obj_in: "Colormap",  # The cmap object determined earlier
    ) -> Tuple["Norm", "Colormap"]:
        """
        Infers/creates the norm (BoundaryNorm or similar) and potentially modifies
        the cmap based on the provided values list. Assumes values is NOT None.
        """
        # Logic to get potential tick positions and labels from the values list
        # The values list can contain floats, strings, or None.
        # Numeric values (or None) will influence tick *positions*.
        # String values will force index-based tick *positions* and become tick *labels*.
        potential_ticks = []
        potential_labels = []  # Initialize labels list

        for i, val in enumerate(values):
            # Attempt to use the value directly for tick position if float-like
            try:
                float_val = float(val)
                potential_ticks.append(float_val)
                potential_labels.append(
                    str(val)
                )  # Store string representation as potential label
            except (TypeError, ValueError):
                # If not float-like, use index for tick position and store string as label
                potential_ticks.append(float(i))  # Use index (as float) for position
                potential_labels.append(str(val))  # Store string as label

        # Determine final tick positions and labels list based on content
        # If ANY value in the original 'values' list was non-floatable (e.g., string or None),
        # OR if any value in the 'potential_ticks' list couldn't become a number,
        # OR if the resulting 'potential_ticks' contains duplicate values,
        # use index-based tick positions and the 'potential_labels' list.
        original_has_non_floatable = any(
            v is not None and not isinstance(v, Number) and not hasattr(v, "__float__")
            for v in values
        )
        has_duplicate_potential_ticks = len(potential_ticks) != len(
            set(potential_ticks)
        )

        if original_has_non_floatable or has_duplicate_potential_ticks:
            # Use indices for tick positions
            final_tick_positions = np.arange(len(values)).tolist()
            # Use the potential_labels list (derived from string representation of values)
            final_tick_labels = potential_labels
        else:
            # If all values were numeric (or None which became index), use the numeric values/indices as ticks
            final_tick_positions = potential_ticks
            final_tick_labels = (
                None  # No explicit string labels; formatter will determine labels
            )

        # Check if we actually have any items to create a norm/cmap for
        if not final_tick_positions:
            warnings._warn_ultraplot("Cannot determine levels from empty values list.")
            # Fallback to continuous norm from input spec or linear
            final_norm = constructor.Norm(norm_spec_in or "linear", vmin=0, vmax=1)
            final_cmap = cmap_obj_in
            return final_norm, final_cmap

        # Calculate levels for a discrete norm based on final_tick_positions
        if len(final_tick_positions) == 1:
            # Levels surround the single tick position (e.g., [0-0.5, 0+0.5] if index-based)
            level_positions = [
                final_tick_positions[0] - 0.5,
                final_tick_positions[0] + 0.5,
            ]
        else:
            # Assuming 'edges' calculates boundaries between tick positions
            # Ensure tick positions are sorted before calculating edges if they weren't indices
            sorted_tick_positions = sorted(
                final_tick_positions
            )  # Edges assumes sorted input
            level_positions = edges(np.asarray(sorted_tick_positions))

        # Use PlotAxes._parse_level_norm to get the BoundaryNorm (or similar discrete norm)
        # and potentially adjusted cmap.
        # It needs level_positions, the input norm spec/obj, the input cmap obj,
        # the final tick positions, and the final tick labels.
        # Ensure PlotAxes is imported and has _parse_level_norm
        # from .axes.plot import PlotAxes # Assuming already imported

        from .axes.plot import PlotAxes

        final_norm, final_cmap, _ = PlotAxes._parse_level_norm(
            level_positions,
            norm_spec_in,
            cmap_obj_in,
            discrete_ticks=final_tick_positions,
            discrete_labels=final_tick_labels,
        )

        return final_norm, final_cmap

    # _make_norm (static) - Seems correct as is for creating a continuous norm
    @staticmethod
    def _make_norm(
        norm: mcm.colors.Normalize | str | None,  # Allow str input
        norm_kw: dict | None,
        vmin: Number | None,
        vmax: Number | None,
    ) -> "Norm":
        """Creates a continuous norm."""
        norm_kw = norm_kw or {}
        norm_spec = norm or "linear"
        vmin = _not_none(vmin=vmin, norm_kw_vmin=norm_kw.pop("vmin", None), default=0)
        vmax = _not_none(vmax=vmax, norm_kw_vmax=norm_kw.pop("vmax", None), default=1)
        # Ensure vmin/vmax are not None before passing to constructor if it doesn't handle None
        # Assuming constructor.Norm handles None or defaults internally if vmin/vmax are None.
        return constructor.Norm(norm_spec, vmin=vmin, vmax=vmax, **norm_kw)

    # _prepare_axes (method) - Needs to take settings and kwargs, pop used keys, return cax and remaining kwargs
    def _prepare_axes(
        self,
        parent_ax: "Axes",
        settings: UltraColorbarSettings,
        kwargs: MutableMapping,  # Dictionary to pop from (mutated in place)
    ) -> Tuple["Axes", MutableMapping]:
        """
        Prepare colorbar axes based on location, popping used kwargs.

        Modifies the input kwargs dictionary in place.
        Returns the created cax and the kwargs dictionary after popping keys used
        as explicit arguments for panel/inset creation functions.
        """
        loc = settings.loc  # Get loc from settings

        # Determine default length for panel colorbars if not set in settings
        panel_length = settings.length
        if loc in ("fill", "left", "right", "top", "bottom") and panel_length is None:
            panel_length = rc["colorbar.length"]

        # Define the keys that are used as *explicit positional or keyword arguments*
        # by the internal panel/inset creation functions (_add_guide_panel,
        # _parse_colorbar_filled, _parse_colorbar_inset).
        # These keys should be popped from the kwargs dictionary passed into *this* method
        # to avoid passing them twice (once via the explicit arg, once via **kwargs).
        # Keys based on assumed signatures:
        # _add_guide_panel(loc, align, length, width, space, pad)
        # _parse_colorbar_filled(extendsize, kwargs)
        # _parse_colorbar_inset(loc, pad, extendsize, length, width, align, space, label, kwargs)
        # Note: 'kwargs' here refers to the mutable dictionary argument itself.
        # The *contents* of that dictionary are then unpacked via **kwargs *inside* those methods.

        # Keys to pop from the input `kwargs` dictionary:
        keys_used_as_explicit_axes_args = [
            "loc",
            "align",
            "space",
            "pad",
            "width",
            "length",
            "extendsize",
            "label",  # label passed to inset
            # Note: This list should be carefully confirmed based on the actual internal function signatures.
            # If an internal function takes a key as an explicit arg *and* also processes it from its **kwargs,
            # this could lead to issues. Assuming explicit args take precedence and should be popped.
        ]

        # Pop these keys from the input kwargs dictionary (mutating it)
        popped_axes_kwargs = _pop_params(kwargs, keys=keys_used_as_explicit_axes_args)

        if loc in ("fill", "left", "right", "top", "bottom"):
            # Create panel axes first
            ax = parent_ax._add_guide_panel(
                loc,  # Use loc from settings
                settings.align,  # Use align from settings
                length=panel_length,  # Use possibly defaulted panel_length
                width=settings.width,  # Use width from settings
                space=settings.space,  # Use space from settings
                pad=settings.pad,  # Use pad from settings
            )
            # Then parse the colorbar within the panel axes
            # Pass extendsize from settings and the *mutated* kwargs dictionary
            # Assuming _parse_colorbar_filled takes the mutable dict as a named arg 'kwargs'
            cax = ax._parse_colorbar_filled(settings.extendsize, kwargs=kwargs)

        else:  # Assume inset or other location handled by _parse_colorbar_inset
            # Pass loc, pad, extendsize, length, width, align, space, label from settings
            # and the *mutated* kwargs dictionary.
            # Assuming _parse_colorbar_inset takes the mutable dict as a named arg 'kwargs'
            cax = parent_ax._parse_colorbar_inset(
                loc=loc,
                pad=settings.pad,
                extendsize=settings.extendsize,
                length=settings.length,
                width=settings.width,
                align=settings.align,
                space=settings.space,
                label=settings.label,  # label explicitly passed here
                kwargs=kwargs,  # Pass the mutable kwargs dictionary
            )

        # Return the created cax and the *same* kwargs dictionary (now potentially modified)
        return cax, kwargs

    # _process_ticks (method) - Needs to take norm and settings, return final objects/flag
    def _process_ticks(
        self,
        norm: "Normalize",  # Use the norm from the processed mappable
        settings: UltraColorbarSettings,  # Pass settings object
    ) -> Tuple[
        Union["Locator", None], Union["MinorLocator", None], Union["Formatter", bool]
    ]:
        """Process colorbar tick locators and formatters, using settings."""
        # Get specs and kw dicts from settings
        locator_spec = settings.locator
        minorlocator_spec = settings.minorlocator
        formatter_spec_user = settings.formatter  # User provided spec
        locator_kw = settings.locator_kw or {}
        minorlocator_kw = settings.minorlocator_kw or {}
        formatter_kw = settings.formatter_kw or {}
        tickminor_user = settings.tickminor  # User's tickminor flag

        # Determine default formatter spec from the norm if user didn't provide one
        default_formatter_spec = getattr(
            norm, "_labels", None
        )  # E.g., from BoundaryNorm
        if default_formatter_spec is None:
            default_formatter_spec = "auto"  # mpl default

        # Combine user spec and defaults
        formatter_spec = _not_none(formatter_spec_user, default_formatter_spec)

        # Set tickrange default for formatter_kw
        formatter_kw.setdefault("tickrange", (norm.vmin, norm.vmax))

        # Create formatter object
        formatter = constructor.Formatter(formatter_spec, **formatter_kw)
        categorical = isinstance(
            formatter, mticker.FixedFormatter
        )  # Check if categorical

        # Create locator object
        if locator_spec is not None:
            # Use constructor.Locator with user spec and kw
            locator = constructor.Locator(locator_spec, **locator_kw)
        else:
            # Determine default locator based on norm type
            if isinstance(norm, mcolors.BoundaryNorm):
                ticks_from_norm = getattr(
                    norm, "_ticks", norm.boundaries
                )  # Get ticks from norm or its boundaries
                segmented = isinstance(
                    getattr(norm, "_norm", None), pcolors.SegmentedNorm
                )  # Check for SegmentedNorm base
                if categorical or segmented:
                    locator = mticker.FixedLocator(
                        ticks_from_norm
                    )  # Use FixedLocator for fixed labels or segmented
                else:
                    # Default DiscreteLocator for BoundaryNorm otherwise
                    try:
                        # Assuming pticker and DiscreteLocator exist
                        locator = pticker.DiscreteLocator(ticks_from_norm)
                    except NameError:
                        warnings._warn_ultraplot(
                            "pticker.DiscreteLocator not found, falling back to mpl default locator for BoundaryNorm."
                        )
                        # Fallback to mpl's default which might be AutoLocator for BoundaryNorm?
                        # Need to check mpl behavior or specify a safe fallback.
                        # Let's raise if the required ProPlot locator isn't available.
                        raise

            else:
                # Default for continuous norm is AutoLocator
                locator = mticker.AutoLocator()

        # Determine final tickminor flag
        if tickminor_user is not None:
            final_tickminor = tickminor_user
        elif categorical:
            final_tickminor = False  # No minor ticks for categorical colorbars
        else:
            # Default based on rcParams and the determined orientation
            orientation = settings.orientation
            axis_key = "xy"[
                orientation == "vertical"
            ]  # 'x' for horizontal, 'y' for vertical
            final_tickminor = rc[axis_key + "tick.minor.visible"]  # Get rcParam

        # Create minor locator object
        minorlocator = None  # Initialize minorlocator object as None
        if minorlocator_spec is not None:
            # Use constructor.Locator with user spec and kw for minor locator
            minorlocator = constructor.Locator(minorlocator_spec, **minorlocator_kw)
            # If user specified minor locator, turn minors on regardless of tickminor flag
            final_tickminor = True

        elif final_tickminor and isinstance(norm, mcolors.BoundaryNorm):
            # Default minor locator for BoundaryNorm is DiscreteLocator(minor=True)
            ticks_from_norm = getattr(norm, "_ticks", norm.boundaries)
            try:
                # Assuming pticker and DiscreteLocator exist
                minorlocator = pticker.DiscreteLocator(ticks_from_norm, minor=True)
            except NameError:
                warnings._warn_ultraplot(
                    "pticker.DiscreteLocator not found, cannot set default minor locator for BoundaryNorm."
                )
                minorlocator = None  # Cannot set default
                final_tickminor = False  # Cannot have minor ticks without a locator

        elif final_tickminor and not isinstance(norm, mcolors.BoundaryNorm):
            # Default minor locator for continuous norm is AutoMinorLocator
            minorlocator = mticker.AutoMinorLocator()

        # Handle empty locators - Check if locator has locs and it's empty, or if it's NullLocator
        # If major locator is effectively empty, disable minor ticks and minor locator
        if isinstance(locator, mticker.NullLocator) or (
            hasattr(locator, "locs")
            and isinstance(getattr(locator, "locs", None), (list, np.ndarray))
            and len(getattr(locator, "locs", [])) == 0
        ):
            minorlocator = None
            final_tickminor = False  # Turn off minor ticks if major locator is empty

        return locator, minorlocator, formatter, final_tickminor

    # _configure_colorbar (method) - Needs final minorlocator and tickminor flag
    def _configure_colorbar(
        self, minorlocator: Union["MinorLocator", None], tickminor: bool
    ):
        """Configure initial colorbar settings."""
        # Use self.ax (the cax created in __init__) directly
        self.ax.grid(False)  # Turn off grid on colorbar axes

        # Update ticks method if a custom one exists (as hinted in commented code)
        # If guides._update_ticks exists and should be used, uncomment this:
        # try:
        #     self.update_ticks = guides._update_ticks.__get__(self)
        # except (AttributeError, NameError):
        #     # Fallback if custom update_ticks isn't available
        #     pass # Use default ColorbarBase.update_ticks

        # Set minor ticks and minor locator
        if minorlocator is not None:
            # If a minor locator object was successfully created, set it on the ColorbarBase instance
            self.minorlocator = minorlocator  # This is a property of ColorbarBase
            # Calling update_ticks() after setting minorlocator applies it.
            # This should be called *after* super().__init__ finishes.
            self.update_ticks()  # Call the update_ticks method (either default or custom)

        elif tickminor:
            # If tickminor flag is True but no minor locator object was created,
            # turn on matplotlib's default auto minor ticks
            self.minorticks_on()  # Inherited method from ColorbarBase

        else:
            # If tickminor is False and no minor locator, turn minor ticks off
            self.minorticks_off()  # Inherited method from ColorbarBase

        # Handle norm inversion
        # Get the long axis (x for horizontal, y for vertical) using the orientation set by super().__init__
        axis = (
            self._long_axis()
        )  # This method relies on self.orientation being set by ColorbarBase

        # Check if the norm is descending (e.g., ProPlot's InvertedNorm or similar custom norm)
        norm_is_descending = getattr(
            self.norm, "descending", False
        )  # Get norm from self (set by super().__init__)

        # Get the user's reverse setting from the settings object
        settings_reverse = self._settings.reverse

        # Invert the axis if either the norm is descending OR the user specified reverse=True
        if norm_is_descending or settings_reverse:
            axis.set_inverted(True)

    # _long_axis, _short_axis (methods) - seem correct, rely on self.orientation

    # _update_appearance (method) - Reads from self._settings
    def _update_appearance(self):
        """Update colorbar appearance settings using values from self._settings."""
        settings = self._settings  # Get settings object

        # Get the primary axis (where ticks are drawn, based on orientation set by super.__init__)
        axis = self._long_axis()

        # Update tick parameters (color and direction apply to both major/minor)
        axis.set_tick_params(
            which="both",
            color=settings.color,  # From settings
            direction=settings.tickdir,  # From settings
        )
        # Length/width apply specifically to major ticks
        axis.set_tick_params(
            which="major",
            length=settings.ticklen,  # From settings (unit-converted)
            width=settings.tickwidth,  # From settings (unit-converted)
        )
        # Length/width apply specifically to minor ticks, scaled by ratios
        # Ensure ratios are treated as floats for multiplication, default None means no scaling
        ticklen_minor = settings.ticklen
        if settings.ticklenratio is not None and ticklen_minor is not None:
            ticklen_minor *= float(settings.ticklenratio)

        tickwidth_minor = settings.tickwidth
        if settings.tickwidthratio is not None and tickwidth_minor is not None:
            tickwidth_minor *= float(settings.tickwidthratio)

        axis.set_tick_params(
            which="minor",
            length=ticklen_minor,
            width=tickwidth_minor,
        )

        # Set label text and initial position based on orientation
        label_text = settings.label
        if label_text is not None:
            # Use mpl's set_label method, which handles text and initial axis choice
            # based on self.orientation. The label Text artist is attached to self as self._label.
            self.set_label(label_text)

        # Update label position if labelloc is specified
        labelloc = settings.labelloc
        if labelloc is not None:
            # This logic (from original code) attempts to set label position on the 'short' axis
            # if the requested labelloc is orthogonal to colorbar orientation.
            # Replicate original logic:
            loc = settings.loc  # Need the original location string
            if loc in ("top", "bottom") and labelloc in ("left", "right"):
                axis_for_label_pos = self._short_axis()
            elif loc in ("left", "right") and labelloc in ("top", "bottom"):
                axis_for_label_pos = self._short_axis()
            else:
                # If labelloc is along the long axis, set position on the long axis
                axis_for_label_pos = self._long_axis()

            # Set the label position on the chosen axis artist
            axis_for_label_pos.set_label_position(labelloc)

        # Update style of label text (font size, weight, color)
        # Build the style dict from settings fields, filtering None
        label_settings = {
            "size": settings.labelsize,
            "weight": settings.labelweight,
            "color": settings.labelcolor,
        }
        label_settings = {k: v for k, v in label_settings.items() if v is not None}

        # Apply label style to the actual label artist (self._label)
        if hasattr(self, "_label") and self._label is not None:
            self._label.update(label_settings)

        # Update style of tick label text (font size, weight, color, rotation)
        # Build the style dict from settings fields, filtering None
        ticklabel_settings = {
            "size": settings.ticklabelsize,
            "weight": settings.ticklabelweight,
            "color": settings.ticklabelcolor,
            "rotation": settings.rotation,
        }
        ticklabel_settings = {
            k: v for k, v in ticklabel_settings.items() if v is not None
        }

        # Apply tick label style to each tick label artist on the long axis
        axis_with_ticks = self._long_axis()  # Ticks are always on the long axis
        for label_artist in axis_with_ticks.get_ticklabels():
            label_artist.update(ticklabel_settings)

        # Update outline and divider appearance
        kw_outline = {
            "edgecolor": settings.color,  # From settings
            "linewidth": settings.linewidth,  # From settings (unit-converted)
        }
        # Ensure artists exist before updating
        if self.outline is not None:
            self.outline.update(kw_outline)
        if self.dividers is not None:
            self.dividers.update(kw_outline)

        # Set rasterization and edge fixes
        # self.solids is the artist for the color patches
        if self.solids:
            # Assuming PlotAxes._fix_patch_edges exists and is imported
            # from .axes import PlotAxes # Assuming already imported

            self.solids.set_rasterized(
                settings.rasterized
            )  # Rasterized setting from settings
            # edgefix setting from settings
            from .axes.plot import PlotAxes

            PlotAxes._fix_patch_edges(self.solids, edgefix=settings.edgefix)

    # update_label and update_ticks methods could be updated to modify settings
    # and then re-apply settings, but the provided implementations seem to update
    # the mpl objects directly. Let's keep them as provided for now, assuming
    # they work by modifying the underlying mpl objects/properties.
    # They would interact with the settings object if they needed to query
    # other parameter values or persist the changes back to the settings.

    # update_label (method) - as provided
    def update_label(self, label=None, **kwargs):
        # This method seems to bypass the settings object's label field
        # and update the underlying mpl label directly.
        # If label=None is passed, it updates style from kwargs only.
        # If label is text, it updates text and style.
        # The handling of _params is not consistent with the new settings object.
        # This method likely needs refactoring to use/update the settings object.
        # For now, keep as provided but note the potential inconsistency.
        """
        Update the colorbar label with new text and/or styling.

        Parameters
        ----------
        label : str, optional
            The new label text
        **kwargs
            Additional styling parameters for the label (e.g., size, weight, color)
        """
        # The original logic for _params["label"] and _kw_dicts["label"]
        # is inconsistent with the UltraColorbarSettings object.
        # A settings-consistent update would modify settings.label and relevant
        # label size/weight/color fields in settings, then call _update_appearance
        # or a specific method to re-apply *just* the label settings.

        # Simplified direct update assuming **kwargs are label text properties
        if label is not None:
            # Update text via mpl method
            self.set_label(label)
            # Ideally, update settings.label too?
            # self._settings.label = label # Requires settings object to be mutable or use setattr

        # Update style properties (size, weight, color) via update method on label artist
        # The Text artist for the label is attached to self as self._label
        if hasattr(self, "_label") and self._label is not None:
            self._label.update(kwargs)  # Apply arbitrary kwargs as style updates
            # Ideally, update corresponding settings fields too?
            # For key, value in kwargs.items():
            #     if hasattr(self._settings, 'label' + key): # e.g., settings.labelsize
            #         setattr(self._settings, 'label' + key, value) # Requires naming convention

    # update_ticks (method) - as provided
    def update_ticks(self, locator=None, formatter=None, manual_only=False, **kwargs):
        # This method also seems to directly interact with mpl locator/formatter
        # and tick parameters, bypassing the settings object's specs and kw dicts.
        # It should ideally modify the settings object's specs/kw dicts and then
        # re-run the tick processing/application logic.
        # Keep as provided but note the potential inconsistency.
        """
        Update tick locators and formatters.

        Parameters
        ----------
        locator : Locator or str, optional
            The new tick locator or locator-spec
        formatter : Formatter or str, optional
            The new tick formatter or formatter-spec
        manual_only : bool, default: False
            If True, do not call the base class `update_ticks` method,
            useful for applying purely manual tick settings.
        **kwargs
            Additional parameters for tick configuration passed to
            the major axis `set_tick_params`.
        """
        # Get the relevant axis (ticks are on the long axis)
        axis = self._long_axis()

        # Update major locator if provided
        if locator is not None:
            # Use constructor to get the mpl locator object
            mpl_locator = constructor.Locator(locator)
            axis.set_major_locator(mpl_locator)
            # Ideally, update settings.locator too?
            # self._settings.locator = locator # Requires settings object to be mutable or use setattr

        # Update major formatter if provided
        if formatter is not None:
            # Use constructor to get the mpl formatter object
            mpl_formatter = constructor.Formatter(formatter)
            axis.set_major_formatter(mpl_formatter)
            # Ideally, update settings.formatter too?
            # self._settings.formatter = formatter

        # Update tick parameters if additional kwargs are provided
        if kwargs:
            axis.set_tick_params(**kwargs)  # Apply arbitrary kwargs to tick params
            # Ideally, update relevant settings fields? (e.g., settings.ticklen)

        # Call base class update_ticks conditionally
        # Note: The logic involving _use_auto_colorbar_locator and manual_only
        # seems specific to how ProPlot handles tick updates.
        # It might also interact with the minor locator update logic.
        # The default mpl ColorbarBase.update_ticks handles applying major/minor locators.
        # Assuming the custom update_ticks logic is needed.

        attr = "_use_auto_colorbar_locator"
        # Check if the custom logic to determine auto locator usage exists/applies
        if not hasattr(self, attr) or getattr(self, attr)():
            # Use auto locator behavior (calls base update_ticks)
            if not manual_only:
                super().update_ticks()  # Calls base class method to update ticks

        else:
            # Use manual locator behavior (calls base update_ticks then potentially custom minor tick setting)
            super().update_ticks()  # Base update needed for major ticks

            # Custom minor tick update logic
            minorlocator = getattr(
                self, "minorlocator", None
            )  # Get the mpl minor locator object (set by _configure_colorbar or manually)
            if minorlocator is not None:
                # If a minor locator is set, apply minor ticks using the custom logic or fallback
                if hasattr(self, "_ticker"):  # Check for custom _ticker method
                    try:
                        # Use custom _ticker method if available
                        ticks, *_ = self._ticker(
                            self.minorlocator, mticker.NullFormatter()
                        )
                        # Set minor ticks on the long axis
                        axis.set_ticks(ticks, minor=True)
                        axis.set_ticklabels(
                            [], minor=True
                        )  # Minor ticks usually don't have labels
                    except Exception as e:
                        warnings._warn_ultraplot(
                            f"Error computing minor ticks with custom _ticker method for {minorlocator!r}: {e}. Turning on matplotlib's default minor ticks instead."
                        )
                        # Fallback to mpl default minor ticks
                        self.minorlocator = None  # Clear the custom locator
                        self.minorticks_on()

                elif hasattr(
                    minorlocator, "tick_values"
                ):  # Check for tick_values method on locator object
                    try:
                        # Use the locator's tick_values method
                        vmin, vmax = axis.get_view_interval()  # Get axis limits
                        ticks = minorlocator.tick_values(vmin, vmax)
                        # Set minor ticks
                        axis.set_ticks(ticks, minor=True)
                        axis.set_ticklabels([], minor=True)
                    except Exception as e:
                        warnings._warn_ultraplot(
                            f"Cannot use user-input colorbar minor locator {minorlocator!r} (error computing ticks: {e}). Turning on matplotlib's default minor ticks instead."
                        )
                        self.minorlocator = None
                        self.minorticks_on()  # Fallback

                else:
                    warnings._warn_ultraplot(
                        f"Cannot use user-input colorbar minor locator {minorlocator!r} (no tick_values method). Turning on matplotlib's default minor ticks instead."
                    )
                    self.minorlocator = None
                    self.minorticks_on()  # Fallback

            # Note: If minorlocator was None here, minorticks_off() might be needed depending
            # on the state and desired behavior if tickminor_user was False.
            # The _configure_colorbar already handles the initial on/off based on tickminor.


_snippet_manager["ultracolorbar"] = (
    UltraColorbar._args_docstring + UltraColorbar._kwargs_docstring
)
