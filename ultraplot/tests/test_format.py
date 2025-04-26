#!/usr/bin/env python3
"""
Test format and rc behavior.
"""
import locale, numpy as np, ultraplot as uplt, pytest
import warnings


# def test_colormap_assign():
#     """
#     Test below line is possible and naming schemes.
#     """
#     uplt.rc["image.cmap"] = uplt.Colormap("phase", shift=180, left=0.2)
#     assert uplt.rc["cmap"] == uplt.rc["cmap.sequential"] == "_Phase_copy_s"
#     uplt.rc["image.cmap"] = uplt.Colormap("magma", reverse=True, right=0.8)
#     assert uplt.rc["image.cmap"] == uplt.rc["cmap.sequential"] == "_magma_copy_r"


@pytest.mark.skip(reason="This is failing on github but not locally")
def test_ignored_keywords():
    """
    Test ignored keywords and functions.
    """
    with warnings.catch_warnings(record=True) as record:
        fig, ax = uplt.subplots(
            gridspec_kw={"left": 3},
            subplot_kw={"proj": "cart"},
            subplotpars={"left": 0.2},
        )
    # only capture ultraplot warnings not general mpl warnings, e.g. deprecation warnings
    record = [r for r in record if "UltraPlotWarning" in str(r)]
    assert len(record) == 3
    with warnings.catch_warnings(record=True) as record:
        fig.subplots_adjust(left=0.2)
    assert len(record) == 1


@pytest.mark.mpl_image_compare
def test_init_format():
    """
    Test application of format args on initialization.
    """
    fig, axs = uplt.subplots(
        ncols=2,
        xlim=(0, 10),
        xlabel="xlabel",
        abc=True,
        title="Subplot title",
        collabels=["Column 1", "Column 2"],
        suptitle="Figure title",
    )
    axs[0].format(hatch="xxx", hatchcolor="k", facecolor="blue3")
    return fig


@pytest.mark.mpl_image_compare
def test_patch_format():
    """
    Test application of patch args on initialization.
    """
    fig = uplt.figure(suptitle="Super title")
    fig.subplot(
        121, proj="cyl", labels=True, land=True, latlines=20, abcloc="l", abc="[A]"
    )
    fig.subplot(
        122,
        facecolor="gray1",
        color="red",
        titleloc="l",
        title="Hello",
        abcloc="l",
        abc="[A]",
        xticks=0.1,
        yformatter="scalar",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_multi_formatting():
    """
    Support formatting in multiple projections.
    """
    # Mix Cartesian with a projection
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "cyl"))
    axs[0].pcolormesh(np.random.rand(5, 5))

    # Warning is raised based on projection. Cart does not have lonlim, latllim or labels
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        fig.format(
            land=1,
            labels=1,
            lonlim=(0, 90),
            latlim=(0, 90),
            xlim=(0, 10),
            ylim=(0, 10),
        )
        axs[:1].format(
            land=1,
            labels=1,
            lonlim=(0, 90),
            latlim=(0, 90),
            xlim=(0, 10),
            ylim=(0, 10),
        )
    return fig


@pytest.mark.mpl_image_compare
def test_inner_title_zorder():
    """
    Test prominence of contour labels and whatnot.
    """
    fig, ax = uplt.subplots()
    ax.format(
        title="TITLE", titleloc="upper center", titleweight="bold", titlesize="xx-large"
    )
    ax.format(xlim=(0, 1), ylim=(0, 1))
    ax.text(
        0.5,
        0.95,
        "text",
        ha="center",
        va="top",
        color="red",
        weight="bold",
        size="xx-large",
    )
    x = [[0.4, 0.6]] * 2
    y = z = [[0.9, 0.9], [1.0, 1.0]]
    ax.contour(
        x,
        y,
        z,
        color="k",
        labels=True,
        levels=None,
        labels_kw={"color": "blue", "weight": "bold", "size": "xx-large"},
    )
    return fig


@pytest.mark.mpl_image_compare
def test_font_adjustments():
    """
    Test font name application. Somewhat hard to do.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs.format(
        abc="A.",
        fontsize=15,
        fontname="Fira Math",
        xlabel="xlabel",
        ylabel="ylabel",
        title="Title",
        figtitle="Figure title",
        collabels=["Column 1", "Column 2"],
    )
    return fig


@pytest.mark.mpl_image_compare
def test_axes_colors():
    """
    Test behavior of passing color to format.
    """
    fig, axs = uplt.subplots(
        ncols=3,
        nrows=2,
        share=False,
        proj=("cyl", "cart", "polar", "cyl", "cart", "polar"),
        wratios=(2, 2, 1),
    )
    axs[:, 0].format(labels=True)
    axs[:3].format(edgecolor="red", gridlabelsize="med-large", gridlabelweight="bold")
    axs[:3].format(color="red")  # without this just colors the edge
    axs[1].format(xticklabelcolor="gray")
    # axs[2].format(ticklabelcolor='red')
    axs[1].format(tickcolor="blue")
    axs[3:].format(color="red")  # ensure propagates
    # axs[-1].format(gridlabelcolor='green')  # should work
    return fig


@pytest.mark.parametrize("loc", ["en_US.UTF-8"])
@pytest.mark.mpl_image_compare
def test_locale_formatting(loc):
    """
    Ensure locale formatting works. Also zerotrim should account
    for non-period decimal separators.
    """
    # dealing with read the docs
    original_locale = locale.getlocale()
    try:
        try:
            locale.setlocale(locale.LC_ALL, loc)
        except locale.Error:
            pytest.skip(f"Locale {loc} not available on this system")

        # Your test code that is sensitive to the locale settings
        assert locale.getlocale() == (loc.split(".")[0], loc.split(".")[1])

        uplt.rc["formatter.use_locale"] = False
        uplt.rc["formatter.zerotrim"] = True
        with uplt.rc.context({"formatter.use_locale": True}):
            fig, ax = uplt.subplots()
            ticks = uplt.arange(-1, 1, 0.1)
            ax.format(ylim=(min(ticks), max(ticks)), yticks=ticks)
        return fig
    finally:
        # Always reset to the original locale
        locale.setlocale(locale.LC_ALL, original_locale)
    uplt.rc["formatter.use_locale"] = False
    uplt.rc["formatter.zerotrim"] = True
    with uplt.rc.context({"formatter.use_locale": True}):
        fig, ax = uplt.subplots()
        ticks = uplt.arange(-1, 1, 0.1)
        ax.format(ylim=(min(ticks), max(ticks)), yticks=ticks)
    return fig


@pytest.mark.mpl_image_compare
def test_bounds_ticks():
    """
    Test spine bounds and location. Previously applied `fixticks`
    automatically but no longer the case.
    """
    fig, ax = uplt.subplots()
    # ax.format(xlim=(-10, 10))
    ax.format(xloc="top")
    ax.format(xlim=(-10, 15), xbounds=(0, 10))
    return fig


@pytest.mark.mpl_image_compare
def test_cutoff_ticks():
    """
    Test spine cutoff ticks.
    """
    fig, ax = uplt.subplots()
    # ax.format(xlim=(-10, 10))
    ax.format(xlim=(-10, 10), xscale=("cutoff", 0, 2), xloc="top", fixticks=True)
    ax.axvspan(0, 100, facecolor="k", alpha=0.1)
    return fig


@pytest.mark.mpl_image_compare
def test_spine_side():
    """
    Test automatic spine selection when passing `xspineloc` or `yspineloc`.
    """
    fig, ax = uplt.subplots()
    ax.plot(uplt.arange(-5, 5), (10 * np.random.rand(11, 5) - 5).cumsum(axis=0))
    ax.format(xloc="bottom", yloc="zero")
    ax.alty(loc="right")
    return fig


@pytest.mark.mpl_image_compare
def test_spine_offset():
    """
    Test offset axes.
    """
    fig, ax = uplt.subplots()
    ax.format(xloc="none")  # test none instead of neither
    ax.alty(loc=("axes", -0.2), color="red")
    # ax.alty(loc=('axes', 1.2), color='blue')
    ax.alty(loc=("axes", -0.4), color="blue")
    ax.alty(loc=("axes", 1.1), color="green")
    return fig


@pytest.mark.mpl_image_compare
def test_tick_direction():
    """
    Test tick direction arguments.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].format(tickdir="in")
    axs[1].format(xtickdirection="inout", ytickdir="out")  # rc setting should be used?
    return fig


@pytest.mark.mpl_image_compare
def test_tick_length():
    """
    Test tick length args. Ensure ratios can be applied successively.
    """
    fig, ax = uplt.subplots()
    ax.format(yticklen=100)
    ax.format(xticklen=50, yticklenratio=0.1)
    return fig


@pytest.mark.mpl_image_compare
def test_tick_width():
    """
    Test tick width args. Ensure ratios can be applied successively, setting
    width to `zero` adjusts length for label padding, and ticks can appear
    without spines if requested.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=2, share=False)
    ax = axs[0]
    ax.format(linewidth=2, ticklen=20, xtickwidthratio=1)
    ax.format(ytickwidthratio=0.3)
    ax = axs[1]
    ax.format(axeslinewidth=0, ticklen=20, tickwidth=2)  # should permit ticks
    ax = axs[2]
    ax.format(tickwidth=0, ticklen=50)  # should set length to zero
    ax = axs[3]
    ax.format(linewidth=0, ticklen=20, tickwidth="5em")  # should override linewidth
    return fig


@pytest.mark.mpl_image_compare
def test_tick_labels():
    """
    Test default and overwriting properties of auto tick labels.
    """
    import pandas as pd

    data = np.random.rand(5, 3)
    data = pd.DataFrame(data, index=["foo", "bar", "baz", "bat", "bot"])
    fig, axs = uplt.subplots(abc="A.", abcloc="ul", ncols=2, refwidth=3, span=False)
    for i, ax in enumerate(axs):
        data.index.name = "label"
        if i == 1:
            ax.format(xformatter="null")  # overrides result
        ax.bar(data, autoformat=True)
        if i == 0:
            data.index = ["abc", "def", "ghi", "jkl", "mno"]
            data.index.name = "foobar"  # label should be updated
        ax.bar(-data, autoformat=True)
    return fig


@pytest.mark.mpl_image_compare
def test_label_settings():
    """
    Test label colors and ensure color change does not erase labels.
    """
    fig, ax = uplt.subplots()
    ax.format(xlabel="xlabel", ylabel="ylabel")
    ax.format(labelcolor="red")
    return fig


def test_colormap_parsing():
    """Test colormaps merging"""
    reds = uplt.colormaps.get_cmap("reds")
    blues = uplt.colormaps.get_cmap("blues")

    # helper function to test specific values in the colormaps
    # threshold is used due to rounding errors
    def test_range(
        a: uplt.Colormap,
        b: uplt.Colormap,
        threshold=1e-10,
        ranges=[0.0, 1.0],
    ):
        for i in ranges:
            if not np.allclose(a(i), b(i)):
                raise ValueError(f"Colormaps differ !")

    # Test if the colormaps are the same
    test_range(uplt.Colormap("blues"), blues)
    test_range(uplt.Colormap("reds"), reds)
    # For joint colormaps, the lower value should be the lower of the first cmap and the highest should be the highest of the second cmap
    test_range(uplt.Colormap("blues", "reds"), reds, ranges=[1.0])
    # Note: the ranges should not match either of the original colormaps
    with pytest.raises(ValueError):
        test_range(uplt.Colormap("blues", "reds"), reds)


def test_input_parsing_cycle():
    """
    Test the potential inputs to cycle
    """
    # The first argument is a string or an iterable of strings
    with pytest.raises(ValueError):
        cycle = uplt.Cycle(None)

    # Empty should also be handled
    cycle = uplt.Cycle()

    # Test singular string
    cycle = uplt.Cycle("Blues")
    target = uplt.colormaps.get_cmap("blues")
    first_color = cycle.get_next()["color"]
    first_color = uplt.colors.to_rgba(first_color)
    assert np.allclose(first_color, target(0))

    # Test composition
    cycle = uplt.Cycle("Blues", "Reds", N=2)
    lower_half = uplt.colormaps.get_cmap("blues")
    upper_half = uplt.colormaps.get_cmap("reds")
    first_color = uplt.colors.to_rgba(cycle.get_next()["color"])
    last_color = uplt.colors.to_rgba(cycle.get_next()["color"])
    assert np.allclose(first_color, lower_half(0.0))
    assert np.allclose(last_color, upper_half(1.0))


def test_scaler():
    # Test a ultraplot scaler and a matplotlib native scaler; should not race errors
    fig, ax = uplt.subplots(ncols=2, share=0)
    ax[0].set_yscale("mercator")
    ax[1].set_yscale("asinh")
    return fig


@pytest.mark.mpl_image_compare
def test_outer_labels():
    """
    Produces a plot where the abc loc is in top left or top right of a plot. Padding can be used for finer adjustment if necessary.
    """
    fig, ax = uplt.subplots(ncols=2)
    ax[0].format(
        abc="a.",
        abcloc="ol",
        title="testing",
    )
    ax[1].format(
        abc="a.",
        abcloc="outer right",
        title="testing",
        abcpad=-0.25,
    )
    return fig


def test_abc_padding():
    """
    Test the specific calculation for ABC padding in title positioning.
    """
    fig, ax = uplt.subplots()

    # Set up test scenario
    ax.set_title("Test Title")
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
    )
    # Get initial position
    initial_abc_x = ax.axes._title_dict["abc"].get_position()[0]

    # Pad the position and check the offset
    padding_value = 12

    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=padding_value,
    )
    fig.canvas.draw()

    # Verify the new position
    new_abc_x = ax.axes._title_dict["abc"].get_position()[0]

    # Assert position has changed
    assert new_abc_x != initial_abc_x, "ABC padding didn't affect position"

    # Reset padding and position
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=0,
    )
    fig.canvas.draw()
    reference_position = ax.axes._title_dict["abc"].get_position()[0]

    # Apply padding again
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=padding_value,
    )
    # Verify the exact offset matches our expectation
    actual_offset = ax.axes._title_dict["abc"].get_position()[0] - reference_position
    diff = actual_offset - ax.axes._abc_pad  # Note pad is signed!
    assert np.allclose(diff, -padding_value), "ABC padding offset calculation incorrect"
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_unequal_abc_padding():
    """Check if labels are pushed out based on the largest labl length"""
    fig, ax = uplt.subplots(ncols=2, nrows=2, share=0)
    ax[0, 0].set_yscale("asinh")
    ax[1, 0].set_yscale("mercator")
    ax[1, 1].set_yscale("logit")
    ax.format(abc="a.", abcloc="ol")
    return fig


def test_abc_with_labels():
    """
    This test should check the "normal" conditions in which the yaxis has labels and the location for abc is adjusted for the outer labels (left or right)
    """
    fig, ax = uplt.subplots()
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["one", "two", "three"])
    ax.format(abc="a.", abcloc="ol")
    uplt.close(fig)


def test_abc_number():
    """
    Test handling of `abc` with lists of labels that exceed or match the number of axes.
    """
    # The keyword `abc` can take on lists, if the lists exceeds the number of the axes
    with pytest.raises(ValueError):
        fig, ax = uplt.subplots(ncols=3)
        ax.format(abc=["a", "bb"])
    # This should work fine
    fig, ax = uplt.subplots(ncols=2)
    ax.format(abc=["a", "b"])
    uplt.close(fig)


def test_loc_positions():
    """
    Test all locations the abc labels can be in
    """
    from ultraplot.internals.rcsetup import TEXT_LOCS

    fig, ax = uplt.subplots()
    ax.set_title(
        "Dummy title"
    )  # trigger sync with abc to ensure they both move correctly
    for loc in TEXT_LOCS:
        ax.format(abc="a.", abcloc=loc)
    uplt.close(fig)


@pytest.mark.parametrize("angle", [0, 45, 89, 63, 90])
def test_axis_label_anchor(angle):
    """
    Check if the rotation of the xticklabels is correctly handle by xrotation and yrotation
    """
    fig, ax = uplt.subplots(ncols=2)
    ax[0].format(xrotation=angle, yrotation=angle)

    # Need fixed ticks for it to work (set locator explicitly)
    ax[1].set_xticks(ax[1].get_xticks())
    ax[1].set_yticks(ax[1].get_yticks())

    kw = dict()
    if angle in (0, 90, -90):
        kw["ha"] = "right"
    ax[1].set_xticklabels(
        ax[1].get_xticklabels(), rotation=angle, rotation_mode="anchor", **kw
    )
    ax[1].set_yticklabels(
        ax[1].get_yticklabels(), rotation=angle, rotation_mode="anchor", **kw
    )

    # Ticks should be in the same position
    for tick1, tick2 in zip(ax[0].get_xticklabels(), ax[1].get_xticklabels()):
        assert tick1.get_rotation() == angle
        assert tick2.get_rotation() == angle
        assert tick1.get_position()[0] == tick2.get_position()[0]
        assert tick1.get_position()[1] == tick2.get_position()[1]

    for tick1, tick2 in zip(ax[0].get_yticklabels(), ax[1].get_yticklabels()):
        assert tick1.get_rotation() == angle
        assert tick2.get_rotation() == angle
        assert tick1.get_position()[0] == tick2.get_position()[0]
        assert tick1.get_position()[1] == tick2.get_position()[1]
