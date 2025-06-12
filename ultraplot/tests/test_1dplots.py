#!/usr/bin/env python3
"""
Test 1D plotting overrides.
"""
import numpy as np
import numpy.ma as ma
import pandas as pd

import ultraplot as uplt
import pytest


@pytest.mark.mpl_image_compare
def test_auto_reverse():
    """
    Test enabled and disabled auto reverse.
    """
    x = np.arange(10)[::-1]
    y = np.arange(10)
    z = np.random.rand(10, 10)
    fig, axs = uplt.subplots(ncols=2, nrows=3, share=0)
    # axs[0].format(xreverse=False)  # should fail
    axs[0].plot(x, y)
    axs[1].format(xlim=(0, 9))  # manual override
    axs[1].plot(x, y)
    axs[2].plotx(x, y)
    axs[3].format(ylim=(0, 9))  # manual override
    axs[3].plotx(x, y)
    axs[4].pcolor(x, y[::-1], z)
    axs[5].format(xlim=(0, 9), ylim=(0, 9))  # manual override!
    axs[5].pcolor(x, y[::-1], z)
    fig.format(suptitle="Auto-reverse test", collabels=["reverse", "fixed"])
    return fig


@pytest.mark.mpl_image_compare
def test_cmap_cycles():
    """
    Test sampling of multiple continuous colormaps.
    """
    cycle = uplt.Cycle(
        "Boreal",
        "Grays",
        "Fire",
        "Glacial",
        "yellow",
        left=[0.4] * 5,
        right=[0.6] * 5,
        samples=[3, 4, 5, 2, 1],
    )
    fig, ax = uplt.subplots()
    data = np.random.rand(10, len(cycle)).cumsum(axis=1)
    data = pd.DataFrame(data, columns=list("abcdefghijklmno"))
    ax.plot(data, cycle=cycle, linewidth=2, legend="b")
    return fig


@pytest.mark.mpl_image_compare
def test_column_iteration():
    """
    Test scatter column iteration.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].plot(np.random.rand(5, 5), np.random.rand(5, 5), lw=5)
    axs[1].scatter(
        np.random.rand(5, 5),
        np.random.rand(5, 5),
        np.random.rand(5, 5),
        np.random.rand(5, 5),
    )
    return fig


@pytest.mark.skip("TODO")
@pytest.mark.mpl_image_compare
def test_bar_stack():
    """
    Test bar and area stacking.
    """
    # TODO: Add test here


@pytest.mark.mpl_image_compare
def test_bar_width():
    """
    Test relative and absolute widths.
    """
    fig, axs = uplt.subplots(ncols=3)
    x = np.arange(10)
    y = np.random.rand(10, 2)
    for i, ax in enumerate(axs):
        ax.bar(x * (2 * i + 1), y, width=0.8, absolute_width=i == 1)
    return fig


@pytest.mark.mpl_image_compare
def test_bar_vectors():
    """
    Test vector arguments to bar plots.
    """
    facecolors = np.repeat(0.1, 3) * np.arange(1, 11)[:, None]
    fig, ax = uplt.subplots()
    ax.bar(
        np.arange(10),
        np.arange(1, 11),
        linewidth=3,
        edgecolor=[f"gray{i}" for i in range(9, -1, -1)],
        alpha=np.linspace(0.1, 1, 10),
        hatch=[None, "//"] * 5,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_boxplot_colors():
    """
    Test box colors and cycle colors.
    """
    fig = uplt.figure(share=False)
    ax = fig.subplot(221)
    box_data = np.random.uniform(-3, 3, size=(1000, 5))
    violin_data = np.random.normal(0, 1, size=(1000, 5))
    ax.box(box_data, fillcolor=["red", "blue", "green", "orange", "yellow"])
    ax = fig.subplot(222)
    ax.violin(
        violin_data,
        cycle=["gray1", "gray7"],
        hatches=[None, "//", None, None, "//"],
        means=True,
        barstds=2,
    )  # noqa: E501
    ax = fig.subplot(223)
    ax.boxh(box_data, cycle="pastel2")
    ax = fig.subplot(224)
    ax.violinh(violin_data, cycle="pastel1")
    return fig


@pytest.mark.mpl_image_compare
def test_boxplot_vectors():
    """
    Test vector property arguments.
    """
    coords = (0.5, 1, 2)
    counts = (10, 20, 100)
    labels = ["foo", "bar", "baz"]
    datas = []
    for count in counts:
        data = np.random.rand(count)
        datas.append(data)
    datas = np.array(datas, dtype=object)
    assert len(datas) == len(coords)
    fig, ax = uplt.subplot(refwidth=3)
    cycle = uplt.Cycle("538")
    ax.boxplot(
        coords,
        datas,
        lw=2,
        notch=False,
        whis=(10, 90),
        fillalpha=[0.5, 0.5, 1],
        cycle=cycle,
        hatch=[None, "//", "**"],
        boxlw=[2, 1, 1],
    )
    ax.format(xticklabels=labels)
    return fig


@pytest.mark.mpl_image_compare
def test_histogram_types():
    """
    Test the different histogram types using basic keywords.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=2, share=False)
    data = np.random.normal(size=(100, 5))
    data += np.arange(5)
    kws = ({"stack": 0}, {"stack": 1}, {"fill": 0}, {"fill": 1, "alpha": 0.5})
    for ax, kw in zip(axs, kws):
        ax.hist(data, ec="k", **kw)
    return fig


@pytest.mark.mpl_image_compare
def test_invalid_plot():
    """
    Test lines with missing or invalid values.
    """
    fig, axs = uplt.subplots(ncols=2)
    data = np.random.normal(size=(100, 5))
    for j in range(5):
        data[:, j] = np.sort(data[:, j])
        data[: 19 * (j + 1), j] = np.nan
        # data[:20, :] = np.nan
    data_masked = ma.masked_invalid(data)  # should be same result
    for ax, dat in zip(axs, (data, data_masked)):
        ax.plot(dat, means=True, shade=True)
    return fig


@pytest.mark.mpl_image_compare
def test_invalid_dist():
    """
    Test distributions with missing or invalid data.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=2)
    data = np.random.normal(size=(100, 5))
    for i in range(5):  # test uneven numbers of invalid values
        data[: 10 * (i + 1), :] = np.nan
    data_masked = ma.masked_invalid(data)  # should be same result
    for ax, dat in zip(axs[:2], (data, data_masked)):
        ax.violin(dat, means=True)
    for ax, dat in zip(axs[2:], (data, data_masked)):
        ax.box(dat, fill=True, means=True)
    return fig


@pytest.mark.mpl_image_compare
def test_pie_charts():
    """
    Test basic pie plots. No examples in user guide right now.
    """
    uplt.rc.inlineformat = "svg"
    labels = ["foo", "bar", "baz", "biff", "buzz"]
    array = np.arange(1, 6)
    data = pd.Series(array, index=labels)
    fig, ax = uplt.subplots(ncols=2)
    ax[0].pie(array, edgefix=True, labels=labels, ec="k", cycle="reds")
    ax[1].pie(data, ec="k", cycle="blues")
    return fig


@pytest.mark.mpl_image_compare
def test_parametric_labels():
    """
    Test passing strings as parametric 'color values'. This is likely
    a common use case.
    """
    uplt.rc.inlineformat = "svg"
    fig, ax = uplt.subplots()
    ax.parametric(
        np.random.rand(5),
        c=list("abcde"),
        lw=20,
        colorbar="b",
        cmap_kw={"left": 0.2},
    )
    return fig


@pytest.mark.mpl_image_compare
def test_parametric_colors():
    """
    Test color input arguments. Should be able to make monochromatic
    plots for case where we want `line` without sticky x/y edges.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=2)
    colors = (
        [(0, 1, 1), (0, 1, 0), (1, 0, 0), (0, 0, 1), (1, 1, 0)],
        ["b", "r", "g", "m", "c", "y"],
        "black",
        (0.5, 0.5, 0.5),
    )
    for ax, color in zip(axs, colors):
        ax.parametric(
            np.random.rand(5),
            np.random.rand(5),
            linewidth=2,
            label="label",
            color=color,
            colorbar="b",
            legend="b",
        )
    return fig


@pytest.mark.mpl_image_compare
def test_scatter_args():
    """
    Test diverse scatter keyword parsing and RGB scaling.
    """
    x, y = np.random.randn(50), np.random.randn(50)
    data = np.random.rand(50, 3)
    fig, axs = uplt.subplots(ncols=4, share=0)
    ax = axs[0]
    ax.scatter(x, y, s=80, fc="none", edgecolors="r")
    ax = axs[1]
    ax.scatter(data, c=data, cmap="reds")  # column iteration
    ax = axs[2]
    with pytest.warns(uplt.internals.UltraPlotWarning) as record:
        ax.scatter(data[:, 0], c=data, cmap="reds")  # actual colors
    assert len(record) == 1
    ax = axs[3]
    ax.scatter(data, mean=True, shadestd=1, barstd=0.5)  # distribution
    ax.format(xlim=(-0.1, 2.1))
    return fig


@pytest.mark.mpl_image_compare
def test_scatter_inbounds():
    """
    Test in-bounds scatter plots.
    """
    fig, axs = uplt.subplots(ncols=2, share=False)
    N = 100
    fig.format(xlim=(0, 20))
    for i, ax in enumerate(axs):
        c = ax.scatter(np.arange(N), np.arange(N), c=np.arange(N), inbounds=bool(i))
        ax.colorbar(c, loc="b")
    return fig


@pytest.mark.mpl_image_compare
def test_scatter_alpha():
    """
    Test behavior with multiple alpha values.
    """
    fig, ax = uplt.subplots()
    data = np.random.rand(10)
    alpha = np.linspace(0.1, 1, data.size)
    ax.scatter(data, alpha=alpha)
    ax.scatter(data + 1, c=np.arange(data.size), cmap="BuRd", alpha=alpha)
    ax.scatter(data + 2, color="k", alpha=alpha)
    ax.scatter(data + 3, color=[f"red{i}" for i in range(data.size)], alpha=alpha)
    return fig


@pytest.mark.mpl_image_compare
def test_scatter_cycle():
    """
    Test scatter property cycling.
    """
    fig, ax = uplt.subplots()
    cycle = uplt.Cycle(
        "538",
        marker=["X", "o", "s", "d"],
        sizes=[20, 100],
        edgecolors=["r", "k"],
    )
    ax.scatter(
        np.random.rand(10, 4),
        np.random.rand(10, 4),
        cycle=cycle,
        area_size=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_scatter_sizes():
    """
    Test marker size scaling.
    """
    # Compare setting size to input size
    size = 20
    with uplt.rc.context({"lines.markersize": size}):
        fig = uplt.figure()
        ax = fig.subplot(121, margin=0.15)
        for i in range(3):
            kw = {"absolute_size": i == 2}
            if i == 1:
                kw["smin"] = 0
                kw["smax"] = size**2  # should be same as relying on lines.markersize
            ax.scatter(np.arange(5), [0.25 * (1 + i)] * 5, size**2, **kw)
    # Test various size arguments
    ax = fig.subplot(122, margin=0.15)
    data = np.random.rand(5) * 500
    ax.scatter(
        np.arange(5),
        [0.25] * 5,
        c="blue7",
        sizes=[5, 10, 15, 20, 25],
        area_size=False,
        absolute_size=True,
    )
    ax.scatter(np.arange(5), [0.50] * 5, c="red7", sizes=data, absolute_size=True)
    ax.scatter(np.arange(5), [0.75] * 5, c="red7", sizes=data, absolute_size=False)
    for i, d in enumerate(data):
        ax.text(i, 0.5, format(d, ".0f"), va="center", ha="center")
    return fig


# Test introduced by issue #https://github.com/Ultraplot/ultraplot/issues/12#issuecomment-2576154882
# Check for concave triangulation related functions
from matplotlib import tri


@pytest.mark.mpl_image_compare
@pytest.mark.parametrize(
    "x, y, z, triangles, use_triangulation, use_datadict",
    [
        # Base data that's common to all test cases
        base_data := (
            np.array([0, 1, 0, 0, 1]),
            np.array([0, 0, 1, 2, 2]),
            np.array([0, 1, -1, 0, 2]),
            np.array([[0, 1, 2], [2, 3, 4]]),
            False,
            False,
        ),
        # Test without triangles
        (*base_data[:3], None, False, False),
        # Test with triangulation
        (*base_data[:4], True, False),
        (*base_data[:3], None, False, False),
        # Test using data dictionary
        (*base_data[:3], None, False, True),
    ],
)
def test_triplot_variants(x, y, z, triangles, use_triangulation, use_datadict):
    fig, ax = uplt.subplots(figsize=(4, 3))
    if use_datadict:
        df = {"x": x, "y": y, "z": z}

    if use_triangulation:
        # Use a Triangulation object
        triangulation = tri.Triangulation(x, y, triangles)
        ax.tricontourf(triangulation, z, levels=64, cmap="PuBu")
    elif use_datadict:
        ax.tricontourf("x", "y", "z", data=df)
        return fig
    else:
        # Use direct x, y, z inputs
        ax.tricontourf(x, y, z, triangles=triangles, levels=64, cmap="PuBu")

    if triangles is not None:
        ax.triplot(x, y, triangles, "ko-")  # Display cell edges
    else:
        if use_datadict:
            df = {"x": x, "y": y, "z": z}
            ax.triplot("x", "y", "ko-", data=df)
        else:
            ax.triplot(x, y, "ko-")  # Without specific triangles
    return fig


@pytest.mark.mpl_image_compare
def test_norm_not_modified():
    """
    Ensure that norm is correctly passed to pcolor and related functions.
    """
    # Create mock data and assign the colors to y
    # The norm should clip the data and not be modified
    x = np.arange(10)
    y = x**2
    c = y
    cmap = uplt.Colormap("viridis")
    norm = uplt.Norm("linear", 0, 10)
    fig, (left, right) = uplt.subplots(ncols=2, share=0)
    left.scatter(x, y, c=c, cmap=cmap, norm=norm)
    assert norm.vmin == 0
    assert norm.vmax == 10

    arr = np.random.rand(20, 40) * 1000
    xe = np.linspace(0, 1, num=40, endpoint=True)
    ye = np.linspace(0, 1, num=20, endpoint=True)

    norm = uplt.Norm("linear", vmin=0, vmax=1)
    right.pcolor(xe, ye, arr, cmap="viridis", norm=norm)
    assert norm.vmin == 0
    assert norm.vmax == 1
    return fig


@pytest.mark.mpl_image_compare
def test_line_plot_cyclers():
    # Sample data
    M, N = 50, 10
    data1 = (np.random.rand(M, N) - 0.48).cumsum(axis=1).cumsum(axis=0)
    data2 = (np.random.rand(M, N) - 0.48).cumsum(axis=1).cumsum(axis=0) * 1.5
    data1 += np.random.rand(M, N)
    data2 += np.random.rand(M, N)
    data1 *= 2

    cmaps = ("Blues", "Reds")
    cycle = uplt.Cycle(*cmaps)

    # Use property cycle for columns of 2D input data
    fig, ax = uplt.subplots(ncols=3, sharey=True)

    # Intention of subplots
    ax[0].set_title("Property cycle")
    ax[1].set_title("Joined cycle")
    ax[2].set_title("Separate cycles")

    ax[0].plot(
        data1 + data2,
        cycle="black",  # cycle from monochromatic colormap
        cycle_kw={"ls": ("-", "--", "-.", ":")},
    )

    # Plot all dat with both cyclers on
    ax[1].plot(
        (data1 + data2),
        cycle=cycle,
    )

    # Test cyclers separately
    cycle = uplt.Cycle(*cmaps)
    for idx in range(0, N):
        ax[2].plot(
            (data1[..., idx] + data2[..., idx]),
            cycle=cycle,
            cycle_kw={"N": N, "left": 0.3},
        )

    fig.format(xlabel="xlabel", ylabel="ylabel", suptitle="On-the-fly property cycles")
    return fig


@pytest.mark.mpl_image_compare
def test_heatmap_labels():
    """
    Heatmap function should show labels when asked
    """
    x = np.random.rand(10, 10)
    # Nans should not be shown
    x[0, 0] = np.nan
    x[0, -1] = np.nan
    x[-1, 0] = np.nan
    x[-1, -1] = np.nan
    x[4:6, 4:6] = np.nan

    fig, ax = uplt.subplots()
    ax.heatmap(x, labels=True)
    return fig


@pytest.mark.mpl_image_compare()
def test_networks():
    """
    Create a baseline network graph that tests
    a few features. It is not the prettiest graphs but highlights what the functions can do.
    """
    import networkx as nx

    graphs = [
        nx.karate_club_graph(),
        nx.florentine_families_graph(),
        nx.davis_southern_women_graph(),
        nx.les_miserables_graph(),
        nx.krackhardt_kite_graph(),
    ]
    facecolors = ["#CC7722", "#254441", "#43AA8B", "#EF3054", "#F7F7FF"]
    positions = [
        (0.05, 0.75),
        (0.75, 0.75),
        (0.05, 0.0),
        (0.75, 0.0),
    ]

    fig, ax = uplt.subplots()
    ax.graph(graphs[-1], node_kw=dict(node_size=300))
    ax.format(facecolor=facecolors[-1])
    ax.margins(0.75)
    ax.set_aspect("equal", "box")

    spines = [
        ["bottom", "right"],
        ["bottom", "left"],
        ["top", "right"],
        ["top", "left"],
    ]
    edge_alphas = [1, 0.75, 0.5, 0.25]

    layouts = ["arf", "spring", "circular", "random"]
    cmaps = ["acton", "viko", "roma", "blues"]
    for g, facecolor, pos, layout, spines, alpha, cmap in zip(
        graphs, facecolors, positions, layouts, spines, edge_alphas, cmaps
    ):
        node_color = uplt.colormaps.get_cmap(cmap)(np.linspace(0, 1, len(g)))
        inax = ax.inset_axes([*pos, 0.2, 0.2], zoom=0)
        inax.graph(
            g,
            layout=layout,
            edge_kw=dict(alpha=alpha),
            node_kw=dict(node_color=node_color),
        )
        xspine, yspine = spines
        inax[0]._toggle_spines(spines)
        inax.format(
            facecolor=facecolor,
        )
        for spine in inax.spines.values():
            spine.set_linewidth(3)

    return fig


def test_bar_alpha():
    """
    Verify that alphas are applied over the columns
    """
    # No img comp needed just internal testing
    import pandas as pd

    # When we make rows shorter than columns an issue appeared
    # where it was taking the x size rather than the number of bars (columns)
    data = np.random.rand(5, 5).cumsum(axis=0).cumsum(axis=1)[:, ::-1]
    data = pd.DataFrame(
        data,
        columns=pd.Index(np.arange(1, 6), name="column"),
        index=pd.Index(["a", "b", "c", "d", "e"], name="row idx"),
    )
    fig, ax = uplt.subplots()
    ax.bar(data)
    ax.bar(data, alphas=np.zeros(data.shape[1]))
    # We are going over columns so this should be ok
    ax.bar(data.iloc[:-1, :], alphas=np.zeros(data.shape[1]))
    with pytest.raises(ValueError):
        ax.bar(data, alphas=np.zeros(data.shape[0] - 1))

    # We should also be allowed to pass a singular number
    x = [0, 1]
    y = [2]
    ax.bar(x, y, alphas=[0.2])
    ax.bar(x, y, alphas=0.2)
    return fig


@pytest.mark.mpl_image_compare
def test_lollipop_graph():
    """
    Verify that lollipop graph is plotted correctly
    """
    # No img comp needed just internal testing
    import pandas as pd

    # When we make rows shorter than columns an issue appeared
    # where it was taking the x size rather than the number of bars (columns)
    data = np.random.rand(5, 5).cumsum(axis=0).cumsum(axis=1)[:, ::-1]
    data = pd.DataFrame(
        data,
        columns=pd.Index(np.arange(1, 6), name="column"),
        index=pd.Index(["a", "b", "c", "d", "e"], name="row idx"),
    )
    fig, ax = uplt.subplots(ncols=3, share=0)
    ax[0].lollipop(
        data,
        stemcolor="green",
        stemwidth=2,
        marker="d",
        edgecolor="k",
    )
    ax[1].lollipoph(data, linestyle="solid")
    x = [0, 1, 2]
    y = [0, 2, 3]
    ax[2].lollipop(x, y)
    return fig


@pytest.mark.mpl_image_compare
def test_bar_labels():
    """
    Simple bar test that rescales the limits if
    bar labels are added
    """
    categories = ["Apple", "Banana", "Orange", "Grape"]
    percentages = [25.3, 42.1, 18.7, 65.2]
    fig, ax = uplt.subplots(ncols=2, nrows=1, share=0)
    ax.format(abc=True, abcloc="ul")
    df = pd.DataFrame({"Percentages": percentages}, index=categories)
    ax[0].barh(y="Percentages", data=df, bar_labels=True)
    ax[1].bar(x="Percentages", data=df, bar_labels=True)
    return fig


@pytest.mark.mpl_image_compare
def test_beeswarm():
    """
    Test beeswarm plots with both traditional and feature value coloring.
    """

    # Create some sample data for beeswarm
    n_points = 40
    n_cats = 4
    categories = np.arange(n_cats)
    shape = (n_points, n_cats)

    levels = np.empty(shape)
    data = np.empty(shape)
    feature_values = np.zeros(shape)
    for cat in range(n_cats):
        levels[:, cat] = np.ones(n_points) * cat
        data[:, cat] = np.random.normal(cat * 1.5, 0.6, n_points)
        feature_values[:, cat] = np.random.randn(n_points)

    fig, (ax1, ax2, ax3) = uplt.subplots(
        ncols=3,
        share=0,
    )

    # Traditional series coloring
    ax1.beeswarm(
        data,
        levels=levels,
        ss=30,
        orientation="vertical",
        alpha=0.7,
    )
    ax1.format(
        title="Beeswarm Plot",
        xlabel="Category",
        ylabel="Value",
        xticks=categories,
        xticklabels=["Group A", "Group B", "Group C", "Group D"],
    )

    # # Feature value coloring
    ax2.beeswarm(
        data,
        levels,
        feature_values=feature_values,
        orientation="horizontal",
        ss=30,
        colorbar="ul",
        colorbar_kw=dict(
            title="Feature Score",
        ),
    )
    ax2.format(
        xlabel="Category",
        ylabel="Value",
        title="Feature Value Beeswarm",
        yticks=categories,
        yticklabels=["Group A", "Group B", "Group C", "Group D"],
    )
    ax3.beeswarm(data[:, 0], levels[:, 0])
    ax3.format(
        title="Singular Beeswarm",
    )
    return fig
