import ultraplot as uplt, numpy as np, pytest


@pytest.mark.mpl_image_compare
def test_vcenter_values():
    """
    Test that vcenter values are correctly set in colorbars.
    """
    rng = np.random.default_rng(seed=10)
    mvals = rng.normal(size=(32, 32))
    cmap = "spectral"
    # The middle and right plot should look the same
    # The colors should spread out where the extremes are visible
    fig, axs = uplt.subplots(ncols=3, share=0)
    for i, ax in enumerate(axs):
        specs = {}
        if i > 0:
            vmin = -0.2
            vmax = 2.0
            specs = dict(vmin=vmin, vmax=vmax)
            if i == 2:
                mvals = np.clip(mvals, vmin, vmax)
        m = ax.pcolormesh(
            mvals,
            cmap=cmap,
            discrete=False,
            **specs,
        )
        ax.format(
            grid=False,
            xticklabels=[],
            xticks=[],
            yticklabels=[],
            yticks=[],
        )
        ax.colorbar(m, loc="r", label=f"{i}")
    return fig
