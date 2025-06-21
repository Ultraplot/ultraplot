import ultraplot as uplt
import pytest
from ultraplot.gridspec import SubplotGrid


def test_grid_has_dynamic_methods():
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    for method in ("altx", "dualx", "twinx"):
        assert hasattr(axs, method)
        assert callable(getattr(axs, method))


def test_altx_calls_all_axes_methods():
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    result = axs.altx()
    assert isinstance(result, SubplotGrid)
    assert len(result) == 2
    for ax in result:
        assert isinstance(ax, uplt.axes.Axes)


def test_missing_command_is_skipped_gracefully():
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    # Pretend we have a method that doesn't exist on these axes
    with pytest.raises(AttributeError):
        axs.nonexistent()


def test_docstring_injection():
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    doc = axs.altx.__doc__
    assert "Call `altx()` for every axes in the grid" in doc
    assert "Returns" in doc
