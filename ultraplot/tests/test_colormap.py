import ultraplot as uplt, pytest, numpy as np


def test_colormap_reversal():
    # Rainbow uses a callable which went wrong see
    # https://github.com/Ultraplot/UltraPlot/issues/294#issuecomment-3016653770
    cmap = uplt.Colormap("rainbow")
    cmap_r = cmap.reversed()
    for i in range(256):
        assert np.allclose(
            cmap(i), cmap_r(255 - i)
        ), f"Reversed colormap mismatch at index {i}"
