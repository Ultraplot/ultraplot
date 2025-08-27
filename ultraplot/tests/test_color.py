import ultraplot as uplt, numpy as np, pytest


@pytest.mark.mpl_image_compare
def test_vcenter_values(rng):
    """
    Test that vcenter values are correctly set in colorbars.
    """
    mvals = rng.normal(size=(32, 32))
    cmap = "spectral"
    vmin, vmax = -0.2, 2.0

    titles = ["No vmin/vmax", "With vmin/vmax", "Clipped with vmin/vmax"]
    fig, axs = uplt.subplots(ncols=3, share=0)
    for i, (ax, title) in enumerate(zip(axs, titles)):
        # Configure plot-specific settings
        specs = {"vmin": vmin, "vmax": vmax} if i > 0 else {}
        clipped_mvals = np.clip(mvals, vmin, vmax) if i == 2 else mvals

        m = ax.pcolormesh(
            clipped_mvals,
            cmap=cmap,
            discrete=False,
            **specs,
        )
        if i >= 1:
            assert np.isclose(m.norm.vcenter, (vmin + vmax) / 2)
            assert np.isclose(m.norm.vmax, vmax)
            assert np.isclose(m.norm.vmin, vmin)
        # Format the axes
        ax.format(
            grid=False,
            xticklabels=[],
            xticks=[],
            yticklabels=[],
            yticks=[],
            title=title,
        )
        ax.colorbar(m, loc="r", label=f"{i}")
    return fig
