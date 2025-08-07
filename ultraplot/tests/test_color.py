import ultraplot as uplt, pytest


@pytest.mark.parametrize(
    "vmin, vmax, vcenter, expected",
    [
        (0, 1, 0, 0.0),  # Set explicit
        (-1, 1, None, 0),  # Symmetric around zero
        (2, 1, None, 1.5),  # Negative range
        (1, 2, 0, 0),  # Positive range
        (0, 0, 0, 0),  # Zero range
    ],
)
def test_diverging_norm_with_range(vmin, vmax, vcenter, expected):
    """
    Ensure that vcenter is correctly set
    """
    norm = uplt.colors.DivergingNorm(vmin=vmin, vmax=vmax, vcenter=vcenter)
    msg = f"Expected vcenter {expected} for vmin={vmin}, vmax={vmax}, vcenter={vcenter}"
    assert norm.vcenter == expected, msg
