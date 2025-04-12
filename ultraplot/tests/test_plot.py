import ultraplot as uplt, numpy as np, pytest
from unittest import mock


@pytest.mark.parametrize(
    "mpl_version, expected_key_and_value",
    [
        ("3.10.0", dict(orientation="vertical", ticklabels=["hello", "world", "!"])),
        ("3.9.0", dict(vert=True, labels=["hello", "world", "!"])),
    ],
)
def test_violinplot_versions(
    mpl_version: str,
    expected_key_and_value: dict,
):
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            ax.violinplot(y=[1, 2, 3], vert=True, labels=["hello", "world", "!"])

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            print(_)
            for expected_key, expected_value in expected_key_and_value.items():
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
