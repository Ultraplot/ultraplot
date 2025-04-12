import ultraplot as uplt, numpy as np, pytest
from unittest import mock


@pytest.mark.parametrize(
    "mpl_version, expected_key, expected_value",
    [
        ("3.10.0", "orientation", "vertical"),
        ("3.9.0", "vert", True),
    ],
)
def test_violin_labels():
    """
    Test the labels functionality of violinplot and violinploth.
    """
    fig, ax = uplt.subplots()
    ax.violinplot(y=[1, 2, 3], vert=True, labels=["hello world!"])
    xtick_labels = ax.get_xticklabels()
    assert len(xtick_labels) == 1
    assert xtick_labels[0].get_text() == "hello world!"

    ax.violinploth(y=[1, 2, 3], vert=True, labels=["hello world!"])

    # Also test the horizontal ticks
    ax.violinploth(x=[1, 2, 3], labels=["hello world!"])
    ytick_labels = ax.get_yticklabels()
    assert len(ytick_labels) == 1
    assert ytick_labels[0].get_text() == "hello world!"


def test_violinplot_versions(
    mpl_version: str,
    expected_key: str,
    expected_value: bool | str,
):
    """
    Test specific logic for violinplot to ensure that past and current versions work as expected.
    """
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            # Note: implicit testing of labels passing. It should work
            ax.violinplot(y=[1, 2, 3], vert=True)

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            assert kwargs[expected_key] == expected_value
            if expected_key == "orientation":
                assert "vert" not in kwargs
            else:
                assert "orientation" not in kwargs


def test_hatches():
    """
    Test the input on the hatches parameter. Either a singular or a list of strings. When a list is provided, it must be of the same length as the number of violins.
    """
    # should be ok
    fig, ax = uplt.subplots()
    ax.violinplot(y=[1, 2, 3], vert=True, hatch="x")

    with pytest.raises(ValueError):
        ax.violinplot(y=[1, 2, 3], vert=True, hatches=["x", "o"])
