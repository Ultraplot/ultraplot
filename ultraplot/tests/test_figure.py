import pytest, ultraplot as uplt, numpy as np


def test_unsharing_after_creation(rng):
    """
    By default UltraPlot shares the axes. We test here if
    we can unshare them after we create the figure. This
    is used on the GeoAxes when the plot contains both
    rectilinear and non-rectilinear axes.
    """
    fig, ax = uplt.subplots(ncols=3, nrows=3, share="all")
    fig._unshare_axes()
    # This should be reset
    assert fig._sharey == False
    assert fig._sharex == False
    for axi in ax:
        # This should be reset
        assert axi._sharey is None
        assert axi._sharex is None
        # Also check the actual grouper
        for which, grouper in axi._shared_axes.items():
            siblings = list(grouper.get_siblings(axi))
            assert len(siblings) == 1

    # Test that the lims are different after unsharing
    base_data = rng.random((2, 100))
    ax[0].scatter(*base_data)
    xlim1 = np.array(ax[0].get_xlim())
    for idx in range(1, 4):
        data = base_data + idx * 100
        ax[idx].scatter(*data)
        xlim2 = np.array(ax[idx].get_xlim())
        l2_norm = np.linalg.norm(xlim1 - xlim2)
        assert not np.allclose(l2_norm, 0)


def test_unsharing_on_creation():
    """
    Test that figure sharing is disabled by default.
    """
    fig, ax = uplt.subplots(ncols=3, nrows=3, share=0)
    assert fig._sharey == False
    assert fig._sharex == False
    for axi in ax:
        # This should be reset
        assert axi._sharey is None
        assert axi._sharex is None
        # Also check the actual grouper
        for which, grouper in axi._shared_axes.items():
            siblings = list(grouper.get_siblings(axi))
            assert len(siblings) == 1
            assert axi in siblings


def test_unsharing_different_rectilinear():
    """
    Even if the projections are rectilinear, the coordinates systems may be different, as such we only allow sharing for the same kind of projections.
    """
    with pytest.warns(uplt.internals.warnings.UltraPlotWarning):
        fig, ax = uplt.subplots(ncols=2, proj=("cyl", "merc"), share="all")
    uplt.close(fig)


def test_figure_sharing_toggle():
    """
    Check if axis sharing and unsharing works
    """

    def compare_with_reference(layout):
        # Create reference
        ref_data = np.array([[0, 100], [0, 200]])
        ref_fig, ref_ax = uplt.subplots(layout.copy(), share=1)
        ref_ax.plot(*ref_data)
        ref_fig.suptitle("Reference")

        # Create "toggled" figure
        fig, ax = uplt.subplots(layout.copy(), share=1)
        fig.suptitle("Toggler")
        # We create a figure with sharing, then toggle it
        # to see if we can update the axis
        fig._toggle_axis_sharing(which="x", share=False)
        fig._toggle_axis_sharing(which="y", share=False)
        for axi in ax:
            assert axi._sharex is None
            assert axi._sharey is None
            for which in "xy":
                siblings = axi._shared_axes[which].get_siblings(axi)
                assert len(list(siblings)) == 1
                assert axi in siblings

        fig._toggle_axis_sharing(which="x", share=True)
        fig._toggle_axis_sharing(which="y", share=True)
        ax.plot(*ref_data)

        for ref, axi in zip(ref_ax, ax):
            for which in "xy":
                ref_axi = getattr(ref, f"_share{which}")
                axi = getattr(ref, f"_share{which}")
                if ref_axi is None:
                    assert ref_axi == axi
                else:
                    assert ref_axi.number == axi.number
                    ref_lim = getattr(ref_axi, f"{which}axis").get_view_interval()
                    lim = getattr(axi, f"{which}axis").get_view_interval()
                    l1 = np.linalg.norm(np.asarray(ref_lim) - np.asarray(lim))
                    assert np.allclose(l1, 0)

        for f in [fig, ref_fig]:
            uplt.close(f)

    # Create a reference
    gs = uplt.gridspec.GridSpec(ncols=3, nrows=3)
    compare_with_reference(gs)

    layout = [
        [1, 2, 0],
        [1, 2, 5],
        [3, 4, 5],
        [3, 4, 0],
    ]
    compare_with_reference(layout)

    layout = [
        [1, 0, 2],
        [0, 3, 0],
        [5, 0, 6],
    ]
    compare_with_reference(layout)

    return None


def test_toggle_input_axis_sharing():
    fig = uplt.figure()
    with pytest.warns(uplt.internals.warnings.UltraPlotWarning):
        fig._toggle_axis_sharing(which="does not exist")


def test_suptitle_alignment():
    """
    Test that suptitle uses the original centering behavior with includepanels parameter.
    """
    # Test 1: Default behavior uses original centering algorithm
    fig1, ax1 = uplt.subplots(ncols=3)
    for ax in ax1:
        ax.panel("top", width="1em")  # Add panels
    fig1.suptitle("Default")
    fig1.canvas.draw()  # Trigger alignment
    pos1 = fig1._suptitle.get_position()

    # Test 2: includepanels=False should use original centering behavior
    fig2, ax2 = uplt.subplots(ncols=3, includepanels=False)
    for ax in ax2:
        ax.panel("top", width="1em")  # Add panels
    fig2.suptitle("includepanels=False")
    fig2.canvas.draw()  # Trigger alignment
    pos2 = fig2._suptitle.get_position()

    # Test 3: includepanels=True should use original centering behavior
    fig3, ax3 = uplt.subplots(ncols=3, includepanels=True)
    for ax in ax3:
        ax.panel("top", width="1em")  # Add panels
    fig3.suptitle("includepanels=True")
    fig3.canvas.draw()  # Trigger alignment
    pos3 = fig3._suptitle.get_position()

    # With reverted behavior, all use the same original centering algorithm
    # Note: In the original code, includepanels didn't actually affect suptitle positioning
    assert (
        abs(pos1[0] - pos2[0]) < 0.001
    ), f"Default and includepanels=False should be same: {pos1[0]} vs {pos2[0]}"

    assert (
        abs(pos2[0] - pos3[0]) < 0.001
    ), f"includepanels=False and True should be same with reverted behavior: {pos2[0]} vs {pos3[0]}"

    uplt.close("all")


import pytest


@pytest.mark.parametrize(
    "suptitle, suptitle_kw, expected_ha, expected_va",
    [
        ("Default alignment", {}, "center", "bottom"),  # Test 1: Default alignment
        (
            "Left aligned",
            {"ha": "left"},
            "left",
            "bottom",
        ),  # Test 2: Custom horizontal alignment
        (
            "Top aligned",
            {"va": "top"},
            "center",
            "top",
        ),  # Test 3: Custom vertical alignment
        (
            "Custom aligned",
            {"ha": "right", "va": "top"},
            "right",
            "top",
        ),  # Test 4: Both custom alignments
    ],
)
def test_suptitle_kw_alignment(suptitle, suptitle_kw, expected_ha, expected_va):
    """
    Test that suptitle_kw alignment parameters work correctly and are not overridden.
    """
    fig, ax = uplt.subplots()
    fig.format(suptitle=suptitle, suptitle_kw=suptitle_kw)
    fig.canvas.draw()
    assert (
        fig._suptitle.get_ha() == expected_ha
    ), f"Expected ha={expected_ha}, got {fig._suptitle.get_ha()}"
    assert (
        fig._suptitle.get_va() == expected_va
    ), f"Expected va={expected_va}, got {fig._suptitle.get_va()}"


@pytest.mark.parametrize(
    "ha, expectation",
    [
        ("left", 0),
        ("center", 0.5),
        ("right", 1),
    ],
)
def test_suptitle_kw_position_reverted(ha, expectation):
    """
    Test that position remains the same while alignment properties differ.
    """
    fig, ax = uplt.subplots(ncols=3)
    fig.format(suptitle=ha, suptitle_kw=dict(ha=ha))
    fig.canvas.draw()  # trigger alignment
    x, y = fig._suptitle.get_position()

    # Note values are dynamic so atol is a bit wide here
    assert np.isclose(x, expectation, atol=0.1), f"Expected x={expectation}, got {x=}"

    uplt.close("all")
