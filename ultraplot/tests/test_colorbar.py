#!/usr/bin/env python3
"""
Test colorbars.
"""
import numpy as np
import pytest
import ultraplot as uplt


@pytest.mark.mpl_image_compare
def test_outer_align():
    """
    Test various align options.
    """
    fig, ax = uplt.subplots()
    ax.plot(np.empty((0, 4)), labels=list("abcd"))
    ax.legend(loc="bottom", align="right", ncol=2)
    ax.legend(loc="left", align="bottom", ncol=1)
    ax.colorbar("magma", loc="r", align="top", shrink=0.5, label="label", extend="both")
    ax.colorbar(
        "magma",
        loc="top",
        ticklen=0,
        tickloc="bottom",
        align="left",
        shrink=0.5,
        label="Title",
        extend="both",
        labelloc="top",
        labelweight="bold",
    )
    ax.colorbar("magma", loc="right", extend="both", label="test extensions")
    fig.suptitle("Align demo")
    return fig


@pytest.mark.mpl_image_compare
def test_colorbar_ticks():
    """
    Test ticks modification.
    """
    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.colorbar("magma", loc="bottom", ticklen=10, linewidth=3, tickminor=True)
    ax = axs[1]
    ax.colorbar(
        "magma", loc="bottom", ticklen=10, linewidth=3, tickwidth=1.5, tickminor=True
    )
    return fig


@pytest.mark.mpl_image_compare
def test_discrete_ticks():
    """
    Test `DiscreteLocator`.
    """
    levels = uplt.arange(0, 2, 0.1)
    data = np.random.rand(5, 5) * 2
    fig, axs = uplt.subplots(share=False, ncols=2, nrows=2, refwidth=2)
    for i, ax in enumerate(axs):
        cmd = ax.contourf if i // 2 == 0 else ax.pcolormesh
        m = cmd(data, levels=levels, extend="both")
        ax.colorbar(m, loc="t" if i // 2 == 0 else "b")
        ax.colorbar(m, loc="l" if i % 2 == 0 else "r")
    return fig


@pytest.mark.mpl_image_compare
def test_discrete_vs_fixed():
    """
    Test `DiscreteLocator` for numeric on-the-fly
    mappable ticks and `FixedLocator` otherwise.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=3, refwidth=1.3, share=False)
    axs[0].plot(np.random.rand(10, 5), labels=list("xyzpq"), colorbar="b")  # fixed
    axs[1].plot(np.random.rand(10, 5), labels=np.arange(5), colorbar="b")  # discrete
    axs[2].contourf(
        np.random.rand(10, 10),
        colorbar="b",
        colorbar_kw={"ticklabels": list("xyzpq")},  # fixed
    )
    axs[3].contourf(np.random.rand(10, 10), colorbar="b")  # discrete
    axs[4].pcolormesh(
        np.random.rand(10, 10) * 20, colorbar="b", levels=[0, 2, 4, 6, 8, 10, 15, 20]
    )  # fixed
    axs[5].pcolormesh(
        np.random.rand(10, 10) * 20, colorbar="b", levels=uplt.arange(0, 20, 2)
    )  # discrete
    return fig


@pytest.mark.mpl_image_compare
def test_uneven_levels():
    """
    Test even and uneven levels with discrete cmap. Ensure minor ticks are disabled.
    """
    N = 20
    data = np.cumsum(np.random.rand(N, N), axis=1) * 12
    colors = [
        "white",
        "indigo1",
        "indigo3",
        "indigo5",
        "indigo7",
        "indigo9",
        "yellow1",
        "yellow3",
        "yellow5",
        "yellow7",
        "yellow9",
        "violet1",
        "violet3",
    ]
    levels_even = uplt.arange(1, 12, 1)
    levels_uneven = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 3.75, 4.5, 6.0, 7.5, 9.0, 12.0]
    fig, axs = uplt.subplots(ncols=2, refwidth=3.0)
    axs[0].pcolor(
        data, levels=levels_uneven, colors=colors, colorbar="r", extend="both"
    )
    axs[1].pcolor(data, levels=levels_even, colors=colors, colorbar="r", extend="both")
    return fig


@pytest.mark.mpl_image_compare
def test_on_the_fly_mappable():
    """
    Test on-the-fly mappable generation.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=3, space=3)
    axs.format(aspect=0.5)
    axs[0].colorbar("magma", vmin=None, vmax=100, values=[0, 1, 2, 3, 4], loc="bottom")
    axs[1].colorbar("magma", vmin=None, vmax=100, loc="bottom")
    axs[2].colorbar("colorblind", vmin=None, vmax=None, values=[0, 1, 2], loc="bottom")
    axs[3].colorbar("colorblind", vmin=None, vmax=None, loc="bottom")
    axs[4].colorbar(["r", "b", "g", "k", "w"], values=[0, 1, 2], loc="b")
    axs[5].colorbar(["r", "b", "g", "k", "w"], loc="bottom")

    # Passing labels to plot function.
    fig, ax = uplt.subplots()
    ax.scatter(np.random.rand(10, 4), labels=["foo", "bar", "baz", "xyz"], colorbar="b")

    # Passing string value lists. This helps complete the analogy with legend 'labels'.
    fig, ax = uplt.subplots()
    hs = ax.line(np.random.rand(20, 5))
    ax.colorbar(hs, loc="b", values=["abc", "def", "ghi", "pqr", "xyz"])
    return fig


@pytest.mark.mpl_image_compare
def test_inset_colorbars():
    """
    Test basic functionality.
    """
    # Simple example
    fig, ax = uplt.subplots()
    ax.colorbar("magma", loc="ul")

    # Colorbars from lines
    fig = uplt.figure(share=False, refwidth=2)
    ax = fig.subplot(121)
    data = 1 + (np.random.rand(12, 10) - 0.45).cumsum(axis=0)
    cycle = uplt.Cycle("algae")
    hs = ax.line(
        data,
        lw=4,
        cycle=cycle,
        colorbar="lr",
        colorbar_kw={"length": "8em", "label": "line colorbar"},
    )
    ax.colorbar(hs, loc="t", values=np.arange(0, 10), label="line colorbar", ticks=2)

    # Colorbars from a mappable
    ax = fig.subplot(122)
    m = ax.contourf(data.T, extend="both", cmap="algae", levels=uplt.arange(0, 3, 0.5))
    fig.colorbar(
        m,
        loc="r",
        length=1,  # length is relative
        label="interior ticks",
        tickloc="left",
    )
    ax.colorbar(
        m,
        loc="ul",
        length=6,  # length is em widths
        label="inset colorbar",
        tickminor=True,
        alpha=0.5,
    )
    fig.format(
        suptitle="Colorbar formatting demo",
        xlabel="xlabel",
        ylabel="ylabel",
        titleabove=False,
    )
    return fig


@pytest.mark.skip("not sure what this does")
@pytest.mark.mpl_image_compare
def test_segmented_norm_center():
    """
    Test various align options.
    """
    fig, ax = uplt.subplots()
    cmap = uplt.Colormap("NegPos", cut=0.1)
    data = np.random.rand(10, 10) * 10 - 2
    levels = [-4, -3, -2, -1, 0, 1, 2, 4, 8, 16, 32, 64, 128]
    norm = uplt.SegmentedNorm(levels, vcenter=0, fair=1)
    ax.pcolormesh(data, levels=levels, norm=norm, cmap=cmap, colorbar="b")
    return fig


@pytest.mark.mpl_image_compare
def test_segmented_norm_ticks():
    """
    Ensure segmented norm ticks show up in center when `values` are passed.
    """
    fig, ax = uplt.subplots()
    data = np.random.rand(10, 10) * 10
    values = (1, 5, 5.5, 6, 10)
    ax.contourf(
        data,
        values=values,
        colorbar="ll",
        colorbar_kw={"tickminor": True, "minorlocator": np.arange(-20, 20, 0.5)},
    )
    return fig


@pytest.mark.mpl_image_compare
def test_reversed_levels():
    """
    Test negative levels with a discrete norm and segmented norm.
    """
    fig, axs = uplt.subplots(ncols=4, nrows=2, refwidth=1.8)
    data = np.random.rand(20, 20).cumsum(axis=0)
    i = 0
    for stride in (1, -1):
        for key in ("levels", "values"):
            for levels in (
                np.arange(0, 15, 1),  # with Normalizer
                [0, 1, 2, 5, 10, 15],  # with LinearSegmentedNorm
            ):
                ax = axs[i]
                kw = {key: levels[::stride]}
                ax.pcolormesh(data, colorbar="b", **kw)
                i += 1
    return fig


@pytest.mark.mpl_image_compare
def test_minor_override():
    """Test minor ticks override."""
    # Setting a custom minor tick should override the settings. Here we set the ticks to 1 and the minorticks to half that. We then check that the minor ticks are set correctly
    data = np.random.rand(10, 10)
    left, right, minor, n = 0, 1, 0.05, 11
    levels = np.linspace(left, right, n)
    fig, ax = uplt.subplots()
    m = ax.pcolormesh(data, colorbar="b", levels=levels)
    cax = ax.colorbar(m, minorticks=minor)
    assert np.allclose(
        cax.minorlocator.tick_values(left, right),
        np.linspace(left - minor, right + minor, n * 2 + 1),
    )
    return fig


@pytest.mark.mpl_image_compare
def test_draw_edges():
    data = np.random.rand(10, 10)
    fig, ax = uplt.subplots(ncols=2)
    for axi, drawedges in zip(ax, [True, False]):
        h = axi.pcolor(data, discrete=True)
        axi.colorbar(h, drawedges=drawedges)
        axi.set_title(f"{drawedges=}")
    return fig


def test_label_placement_colorbar():
    """
    Ensure that all potential combinations of colorbar
    label placement is possible.
    """
    data = np.random.rand(10, 10)
    fig, ax = uplt.subplots()
    h = ax.imshow(data)
    locs = "top bottom left right".split()
    for loc, labelloc in zip(locs, locs):
        ax.colorbar(h, loc=loc, labelloc=labelloc)
