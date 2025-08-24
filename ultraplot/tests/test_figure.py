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
    Test that suptitle alignment works correctly with includepanels parameter.
    """
    # Test 1: Default behavior should center at figure center (0.5)
    fig1, ax1 = uplt.subplots(ncols=3)
    for ax in ax1:
        ax.panel('top', width='1em')  # Add panels
    fig1.suptitle('Default')
    fig1.canvas.draw()  # Trigger alignment
    pos1 = fig1._suptitle.get_position()
    
    # Test 2: includepanels=False should center at figure center (0.5)
    fig2, ax2 = uplt.subplots(ncols=3, includepanels=False)
    for ax in ax2:
        ax.panel('top', width='1em')  # Add panels
    fig2.suptitle('includepanels=False')
    fig2.canvas.draw()  # Trigger alignment
    pos2 = fig2._suptitle.get_position()
    
    # Test 3: includepanels=True should center over content area
    fig3, ax3 = uplt.subplots(ncols=3, includepanels=True)
    for ax in ax3:
        ax.panel('top', width='1em')  # Add panels
    fig3.suptitle('includepanels=True')  
    fig3.canvas.draw()  # Trigger alignment
    pos3 = fig3._suptitle.get_position()
    
    # Assertions
    assert abs(pos1[0] - 0.5) < 0.01, f"Default should center at 0.5, got {pos1[0]}"
    assert abs(pos2[0] - 0.5) < 0.01, f"includepanels=False should center at 0.5, got {pos2[0]}" 
    assert abs(pos3[0] - 0.5) > 0.005, f"includepanels=True should be offset from 0.5, got {pos3[0]}"
    
    # The difference between False and True should be significant
    diff = abs(pos3[0] - pos2[0])
    assert diff > 0.005, f"includepanels should make a difference, difference is {diff}"
    
    uplt.close('all')


def test_suptitle_kw_alignment():
    """
    Test that suptitle_kw alignment parameters work correctly and are not overridden.
    """
    # Test 1: Default alignment should be center/bottom
    fig1, ax1 = uplt.subplots()
    fig1.format(suptitle='Default alignment')
    fig1.canvas.draw()
    assert fig1._suptitle.get_ha() == 'center', f"Default ha should be center, got {fig1._suptitle.get_ha()}"
    assert fig1._suptitle.get_va() == 'bottom', f"Default va should be bottom, got {fig1._suptitle.get_va()}"
    
    # Test 2: Custom horizontal alignment via suptitle_kw
    fig2, ax2 = uplt.subplots()
    fig2.format(suptitle='Left aligned', suptitle_kw={'ha': 'left'})
    fig2.canvas.draw()
    assert fig2._suptitle.get_ha() == 'left', f"Custom ha should be left, got {fig2._suptitle.get_ha()}"
    assert fig2._suptitle.get_va() == 'bottom', f"Default va should be bottom, got {fig2._suptitle.get_va()}"
    
    # Test 3: Custom vertical alignment via suptitle_kw
    fig3, ax3 = uplt.subplots()
    fig3.format(suptitle='Top aligned', suptitle_kw={'va': 'top'})
    fig3.canvas.draw()
    assert fig3._suptitle.get_ha() == 'center', f"Default ha should be center, got {fig3._suptitle.get_ha()}"
    assert fig3._suptitle.get_va() == 'top', f"Custom va should be top, got {fig3._suptitle.get_va()}"
    
    # Test 4: Both custom alignments via suptitle_kw
    fig4, ax4 = uplt.subplots()
    fig4.format(suptitle='Custom aligned', suptitle_kw={'ha': 'right', 'va': 'top'})
    fig4.canvas.draw()
    assert fig4._suptitle.get_ha() == 'right', f"Custom ha should be right, got {fig4._suptitle.get_ha()}"
    assert fig4._suptitle.get_va() == 'top', f"Custom va should be top, got {fig4._suptitle.get_va()}"
    
    # Test 5: Position should differ based on alignment
    fig5, ax5 = uplt.subplots(ncols=3)
    fig5.format(suptitle='Left', suptitle_kw={'ha': 'left'})
    fig5.canvas.draw()
    pos_left = fig5._suptitle.get_position()
    
    fig6, ax6 = uplt.subplots(ncols=3) 
    fig6.format(suptitle='Right', suptitle_kw={'ha': 'right'})
    fig6.canvas.draw()
    pos_right = fig6._suptitle.get_position()
    
    # Left alignment should have smaller x coordinate than right alignment
    assert pos_left[0] < pos_right[0], f"Left alignment x={pos_left[0]} should be < right alignment x={pos_right[0]}"
    
    uplt.close('all')
