#!/usr/bin/env python3
"""
Test twin, inset, and panel axes.
"""
import numpy as np
import pytest
import ultraplot as uplt
from ultraplot.internals.warnings import UltraPlotWarning


def test_axis_access():
    # attempt to access the ax object 2d and linearly
    fig, ax = uplt.subplots(ncols=2, nrows=2)
    ax[0, 0]
    ax[1, 0]
    with pytest.raises(IndexError):
        ax[0, 3]
    ax[3]


@pytest.mark.mpl_image_compare
def test_inset_colors_1():
    """
    Test color application for zoom boxes.
    """
    fig, ax = uplt.subplots()
    ax.format(xlim=(0, 100), ylim=(0, 100))
    ix = ax.inset_axes((0.5, 0.5, 0.3, 0.3), zoom=True, zoom_kw={"fc": "r", "ec": "b"})
    ix.format(xlim=(10, 20), ylim=(10, 20), grid=False)
    return fig


@pytest.mark.mpl_image_compare
def test_inset_colors_2():
    fig, ax = uplt.subplots()
    ax.format(xlim=(0, 100), ylim=(0, 100))
    ix = ax.inset_axes(
        (0.3, 0.5, 0.5, 0.3),
        zoom=True,
        zoom_kw={"lw": 3, "ec": "red9", "a": 1, "fc": uplt.set_alpha("red4", 0.5)},
    )
    ix.format(xlim=(10, 20), ylim=(10, 20))
    return fig


@pytest.mark.mpl_image_compare
def test_inset_zoom_update():
    """
    Test automatic limit adjusment with successive changes. Without the extra
    lines in `draw()` and `get_tight_bbox()` this fails.
    """
    fig, ax = uplt.subplots()
    ax.format(xlim=(0, 100), ylim=(0, 100))
    ix = ax.inset_axes((40, 40, 20, 20), zoom=True, transform="data")
    ix.format(xlim=(10, 20), ylim=(10, 20), grid=False)
    ix.format(xlim=(10, 20), ylim=(10, 30))
    ax.format(ylim=(0, 300))
    return fig


@pytest.mark.mpl_image_compare
def test_panels_with_sharing():
    """
    Previously the below text would hide the second y label.
    """
    fig, axs = uplt.subplots(ncols=2, share=False, refwidth=1.5)
    axs.panel("left")
    fig.format(ylabel="ylabel", xlabel="xlabel")
    return fig


@pytest.mark.mpl_image_compare
def test_panels_without_sharing_1():
    """
    What should happen if `share=False` but figure-wide sharing enabled?
    Strange use case but behavior appears "correct."
    """
    fig, axs = uplt.subplots(ncols=2, share=True, refwidth=1.5, includepanels=False)
    axs.panel("left", share=False)
    fig.format(ylabel="ylabel", xlabel="xlabel")
    return fig


@pytest.mark.mpl_image_compare
def test_panels_without_sharing_2():
    fig, axs = uplt.subplots(ncols=2, refwidth=1.5, includepanels=True)
    for _ in range(3):
        p = axs[0].panel("l", space=0)
        p.format(xlabel="label")
    fig.format(xlabel="xlabel")
    return fig


@pytest.mark.mpl_image_compare
def test_panels_suplabels_three_hor_panels():
    """
    Test label sharing for `includepanels=True`.
    Test for 1 subplot with 3 left panels
    Include here centers the x label to include the panels
    The xlabel should be centered along the main plot with the included side panels
    """
    fig = uplt.figure()
    ax = fig.subplots(refwidth=1.5, includepanels=True)
    for _ in range(3):
        ax[0].panel("l")
    ax.format(xlabel="xlabel", ylabel="ylabel\nylabel\nylabel", suptitle="sup")
    return fig


@pytest.mark.mpl_image_compare
def test_panels_suplabels_three_hor_panels_donotinlcude():
    """
    Test label sharing for `includepanels=True`.
    Test for 1 subplot with 3 left panels
    The xlabel should be centered on the main plot
    """
    fig = uplt.figure()
    ax = fig.subplots(refwidth=1.5, includepanels=False)
    for _ in range(3):
        ax[0].panel("l")
    ax.format(
        xlabel="xlabel",
        ylabel="ylabel\nylabel\nylabel",
        suptitle="sup",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_twin_axes_1():
    """
    Adjust twin axis positions. Should allow easily switching the location.
    """
    # Test basic twin creation and tick, spine, label location changes
    fig = uplt.figure()
    ax = fig.subplot()
    ax.format(
        ycolor="blue",
        ylabel="orig",
        ylabelcolor="blue9",
        yspineloc="l",
        labelweight="bold",
        xlabel="xlabel",
        xtickloc="t",
        xlabelloc="b",
    )
    ax.alty(loc="r", color="r", labelcolor="red9", label="other", labelweight="bold")
    return fig


@pytest.mark.mpl_image_compare
def test_twin_axes_2():
    # Simple example but doesn't quite work. Figure out how to specify left vs. right
    # spines for 'offset' locations... maybe needs another keyword.
    fig, ax = uplt.subplots()
    ax.format(ymax=10, ylabel="Reference")
    ax.alty(color="green", label="Green", max=8)
    ax.alty(color="red", label="Red", max=15, loc=("axes", -0.2))
    ax.alty(color="blue", label="Blue", max=5, loc=("axes", 1.2), ticklabeldir="out")
    return fig


@pytest.mark.mpl_image_compare
def test_twin_axes_3(rng):
    # A worked example from Riley Brady
    # Uses auto-adjusting limits
    fig, ax = uplt.subplots()
    axs = [ax, ax.twinx(), ax.twinx()]
    axs[-1].spines["right"].set_position(("axes", 1.2))
    colors = ("Green", "Red", "Blue")
    for ax, color in zip(axs, colors):
        data = rng.random(1) * rng.random(10)
        ax.plot(data, marker="o", linestyle="none", color=color)
        ax.format(ylabel="%s Thing" % color, ycolor=color)
    axs[0].format(xlabel="xlabel")
    return fig


def test_subset_format():
    fig, axs = uplt.subplots(nrows=1, ncols=3)
    axs[1:].format(title=["a", "b"])  # allowed
    # Subset formatting
    axs[1:].format(title=["c", "d", "e"])  # allowed but does not use e
    assert axs[-1].get_title() == "d"
    assert axs[0].get_title() == ""
    # Shorter than number of axs
    with pytest.raises(ValueError):
        axs.format(title=["a"])


def test_unsharing():
    """
    Test some basic properties of unsharing axes.
    """
    fig, ax = uplt.subplots(ncols=2)
    # Does nothing since key is not an axis or a view
    with pytest.warns(uplt.internals.warnings.UltraPlotWarning):
        ax[0]._unshare(which="key does not exist")
    # 1 shares with 0 but not vice versa
    assert ax[1]._sharey == ax[0]
    assert ax[0]._sharey is None

    ax[0]._unshare(which="y")
    # Nothing should be sharing now
    assert ax[0]._sharey == None
    assert ax[0]._sharex == None
    assert ax[1]._sharey == None
    assert ax[1]._sharex == None


def test_toggling_spines():
    """Test private function to toggle spines"""
    fig, ax = uplt.subplots()
    # Need to get the actual ax not the SubplotGridspec
    # Turn all spines on
    ax[0]._toggle_spines(True)
    assert ax.spines["bottom"].get_visible()
    assert ax.spines["top"].get_visible()
    assert ax.spines["left"].get_visible()
    assert ax.spines["right"].get_visible()
    # Turn all spines off
    ax[0]._toggle_spines(False)
    assert not ax.spines["bottom"].get_visible()
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["left"].get_visible()
    assert not ax.spines["right"].get_visible()
    # Test toggling specific spines
    ax[0]._toggle_spines(spines=["left"])
    assert ax.spines["left"].get_visible()

    # If we toggle right only right is on
    # So left should be off again
    ax[0]._toggle_spines(spines="right")
    assert ax.spines["right"].get_visible()
    assert not ax.spines["left"].get_visible()
    with pytest.raises(ValueError):
        ax[0]._toggle_spines(spines=1)


def test_sharing_labels_top_right():
    fig, ax = uplt.subplots(ncols=3, nrows=3, share="all")
    # On the first format sharexy is modified
    ax.format(
        xticklabelloc="t",
        yticklabelloc="r",
    )
    # If we format again, we expect all the limits to be changed
    # Plot on one shared axis a non-trivial point
    # and check whether the limits are correctly adjusted
    # for all other plots
    ax[0].scatter([30, 40], [30, 40])
    xlim = ax[0].get_xlim()
    ylim = ax[0].get_ylim()

    for axi in ax:
        for i, j in zip(axi.get_xlim(), xlim):
            assert i == j
        for i, j in zip(axi.get_ylim(), ylim):
            assert i == j


@pytest.mark.parametrize(
    "layout, share, tick_loc, y_visible_indices, x_visible_indices",
    [
        # Test case 1: Irregular layout with share=3 (default)
        (
            [
                [1, 2, 0],
                [1, 2, 5],
                [3, 4, 5],
                [3, 4, 0],
            ],
            3,  # default sharing level
            {"xticklabelloc": "t", "yticklabelloc": "r"},
            [1, 3, 4],  # y-axis labels visible indices
            [0, 1, 4],  # x-axis labels visible indices
        ),
        # Test case 2: Irregular layout with share=1
        (
            [
                [1, 0, 2],
                [0, 3, 0],
                [4, 0, 5],
            ],
            1,  # share only labels, not tick labels
            {"xticklabelloc": "t", "yticklabelloc": "r"},
            [0, 1, 2, 3, 4],  # all y-axis labels visible
            [0, 1, 2, 3, 4],  # all x-axis labels visible
        ),
    ],
)
def test_sharing_labels_with_layout(
    layout, share, tick_loc, y_visible_indices, x_visible_indices
):
    """
    Test if tick labels are correctly visible or hidden based on layout and sharing.

    Parameters
    ----------
    layout : list of list of int
        The layout configuration for the subplots
    share : int
        The sharing level (0-4)
    tick_loc : dict
        Tick label location settings
    y_visible_indices : list
        Indices in the axes array where y-tick labels should be visible
    x_visible_indices : list
        Indices in the axes array where x-tick labels should be visible
    """

    # Helper function to check if the labels on an axis direction are visible
    def check_state(ax, numbers, state, which):
        for number in numbers:
            for label in getattr(ax[number], f"get_{which}ticklabels")():
                assert label.get_visible() == state, (
                    f"Expected {which}-tick label visibility to be {state} "
                    f"for axis {number}, but got {not state}"
                )

    # Create figure with the specified layout and sharing level
    fig, ax = uplt.subplots(layout, share=share)

    # Format axes with the specified tick label locations
    ax.format(**tick_loc)

    # Calculate the indices where labels should be hidden
    all_indices = list(range(len(ax)))
    y_hidden_indices = [i for i in all_indices if i not in y_visible_indices]
    x_hidden_indices = [i for i in all_indices if i not in x_visible_indices]

    # Check that labels are visible or hidden as expected
    check_state(ax, y_visible_indices, True, which="y")
    check_state(ax, y_hidden_indices, False, which="y")
    check_state(ax, x_visible_indices, True, which="x")
    check_state(ax, x_hidden_indices, False, which="x")

    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_alt_axes_y_shared():
    layout = [[1, 2], [3, 4]]
    fig, ax = uplt.subplots(ncols=2, nrows=2)

    for axi in ax:
        alt = axi.alty()
        alt.set_ylabel("Alt Y")
        assert alt.get_ylabel() == "Alt Y"
        assert alt.get_xlabel() == ""
        axi.set_ylabel("Y")
    return fig


@pytest.mark.mpl_image_compare
def test_alt_axes_x_shared():
    layout = [[1, 2], [3, 4]]
    fig, ax = uplt.subplots(ncols=2, nrows=2)

    for axi in ax:
        alt = axi.altx()
        alt.set_xlabel("Alt X")
        assert alt.get_xlabel() == "Alt X"
        assert alt.get_ylabel() == ""
        axi.set_xlabel("X")
    return fig
