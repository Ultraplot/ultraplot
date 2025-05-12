import ultraplot as uplt, pytest, numpy as np
from unittest import mock
from packaging import version


@pytest.mark.parametrize(
    "mpl_version",
    [
        "3.10.0",
        "3.9.0",
    ],
)
def test_inset_mpl_versions(
    mpl_version: str,
):
    """
    Test the change in logic inset axes. In mpl 3.10.0, the InsetIndicator class was introduced.
    This test verifies that _format_inset uses the correct implementation based on the matplotlib version.
    """
    # Setup
    fig, ax = uplt.subplots()
    bounds = (0.1, 0.1, 0.2, 0.2)  # x, y, width, height
    parent = fig.axes[0]

    # Create a spy to monitor calls to indicate_inset on the parent
    with (
        mock.patch.object(parent, "indicate_inset") as mock_indicate_inset,
        mock.patch("ultraplot.axes.base._version_mpl", new=mpl_version),
    ):
        # Set appropriate return value based on matplotlib version
        if version.parse(mpl_version) >= version.parse("3.10.0"):
            # For mpl 3.10+, indicate_inset returns InsetIndicator object
            mock_indicator = mock.MagicMock(name="InsetIndicator")
            mock_indicator.rectangle = mock.MagicMock()
            mock_indicator.connectors = [mock.MagicMock()]
            mock_indicate_inset.return_value = mock_indicator
            expected_result = mock_indicator
        else:
            # For older mpl, indicate_inset returns a tuple of (rectangle, connects)
            mock_rectangle = mock.MagicMock()
            mock_connects = [mock.MagicMock()]
            mock_indicate_inset.return_value = (mock_rectangle, mock_connects)
            expected_result = (mock_rectangle, mock_connects)

        # Apply the version patch and call _format_inset
        with mock.patch("ultraplot.internals.versions._version_mpl", new=mpl_version):
            # Call the method we want to test
            result = ax.axes._format_inset(bounds, parent=parent)

            # Verify mpl.indicate_inset was called
            mock_indicate_inset.assert_called_once()

            # Verify the result type matches expected for the matplotlib version
            if version.parse(mpl_version) >= version.parse("3.10.0"):
                # For 3.10+ we expect an InsetIndicator object
                assert result is expected_result
            else:
                # For older versions we expect a tuple of (rectangle, connects)
                assert isinstance(result, tuple)
                assert len(result) == 2
                # Check tuple components - can't use direct tuple comparison with 'is'
                assert result[0] is expected_result[0]
                assert result[1] is expected_result[1]


def test_unsharing_resets_formatters():
    """
    Test if the formatters are reset after sharing
    """
    fig, ax = uplt.subplots(ncols=2, share="all")
    ax[0].set_xscale("asinh")
    ax[0].set_yscale("log")
    # The right plot should now have the same scales
    assert ax[1].get_yscale() == "log"
    assert ax[1].get_xscale() == "asinh"

    assert ax[0].xaxis.get_major_locator() == ax[1].xaxis.get_major_locator()
    assert ax[0].yaxis.get_major_locator() == ax[1].yaxis.get_major_locator()
    for which in "x y view".split():
        ax[0]._unshare(which=which)
    ax[0].set_xscale("linear")
    ax[0].set_yscale("linear")
    assert ax[1].get_yscale() == "log"
    assert ax[1].get_xscale() == "asinh"
    assert ax[0].get_xscale() == "linear"
    assert ax[0].get_yscale() == "linear"

    assert ax[0].xaxis.get_major_locator() != ax[1].xaxis.get_major_locator()
    assert ax[0].yaxis.get_major_locator() != ax[1].yaxis.get_major_locator()
    uplt.close(fig)


def test_unshare_setting_share_x_or_y():
    """
    When axes are shared they get a sharex or y attribute.
    Unsharing should reset these
    """
    fig, ax = uplt.subplots(ncols=2)
    # 1 is sharing its y, 0 is not
    assert ax[0]._sharey is None
    assert ax[1]._sharey == ax[0]

    # x should not be shared
    assert ax[0]._sharex is None
    assert ax[0]._sharex is None
    ax[0]._unshare(which="y")
    assert ax[0]._sharey is None
    assert ax[1]._sharey is None
    uplt.close(fig)
    fig, ax = uplt.subplots(nrows=2)
    # 0 is sharing its x, 1 is not
    assert ax[0]._sharex == ax[1]

    # ys should not be shared
    assert ax[0]._sharey is None
    assert ax[1]._sharey is None

    ax[0]._unshare(which="x")
    assert ax[0]._sharex is None
    assert ax[1]._sharex is None
    uplt.close(fig)
