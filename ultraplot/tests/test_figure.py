import pytest, ultraplot as uplt, numpy as np


def test_unsharing_after_creation():
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
    base_data = np.random.rand(2, 100)
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
