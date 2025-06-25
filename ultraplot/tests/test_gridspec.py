import ultraplot as uplt
import pytest
from ultraplot.gridspec import SubplotGrid


def test_grid_has_dynamic_methods():
    """
    Check that we can apply the methods to a SubplotGrid object.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    for method in ("altx", "dualx", "twinx", "panel"):
        assert hasattr(axs, method)
        assert callable(getattr(axs, method))
        args = []
        if method == "dualx":
            # needs function argument
            args = ["linear"]
        subplotgrid = getattr(axs, method)(*args)
        assert isinstance(subplotgrid, SubplotGrid)
        assert len(subplotgrid) == 2


def test_altx_calls_all_axes_methods():
    """
    Check the return types of newly added methods such as altx, dualx, and twinx.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    result = axs.altx()
    assert isinstance(result, SubplotGrid)
    assert len(result) == 2
    for ax in result:
        assert isinstance(ax, uplt.axes.Axes)


def test_missing_command_is_skipped_gracefully():
    """For missing commands, we should raise an error."""
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    # Pretend we have a method that doesn't exist on these axes
    with pytest.raises(AttributeError):
        axs.nonexistent()


def test_docstring_injection():
    """
    @_apply_to_all should inject the docstring
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    doc = axs.altx.__doc__
    assert "for every axes in the grid" in doc
    assert "Returns" in doc


def test_subplot_repr():
    """
    Panels don't have a subplotspec, so they return "unknown" in their repr, but normal subplots should
    """
    fig, ax = uplt.subplots()
    panel = ax.panel("r")
    assert panel.get_subplotspec().__repr__() == "SubplotSpec(unknown)"
    assert (
        ax[0].get_subplotspec().__repr__()
        == "SubplotSpec(nrows=1, ncols=1, index=(0, 0))"
    )


def test_tight_layout_disabled():
    """
    Some methods are disabled in gridspec, such as tight_layout.
    This should raise a RuntimeErrror when called on a SubplotGrid.
    """
    fig, ax = uplt.subplots()
    gs = ax.get_subplotspec().get_gridspec()
    with pytest.raises(RuntimeError):
        gs.tight_layout(fig)
