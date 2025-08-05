#!/usr/bin/env python3
"""
Test subplot layout.
"""
import numpy as np, ultraplot as uplt, pytest


@pytest.mark.mpl_image_compare
def test_align_labels():
    """
    Test spanning and aligned labels.
    """
    fig, axs = uplt.subplots(
        [[2, 1, 4], [2, 3, 5]], refnum=2, refwidth=1.5, align=1, span=0
    )
    fig.format(xlabel="xlabel", ylabel="ylabel", abc="A.", abcloc="ul")
    axs[0].format(ylim=(10000, 20000))
    axs[-1].panel_axes("bottom", share=False)
    return fig


@pytest.mark.mpl_image_compare
def test_share_all_basic():
    """
    Test sharing level all.
    """
    # Simple example
    N = 10
    fig, axs = uplt.subplots(nrows=1, ncols=2, refwidth=1.5, share="all")
    axs[0].plot(np.arange(N) * 1e2, np.arange(N) * 1e4)
    # Complex example
    fig, axs = uplt.subplots(nrows=2, ncols=2, refwidth=1.5, share="all")
    axs[0].panel("b")
    pax = axs[0].panel("r")
    pax.format(ylabel="label")
    axs[0].plot(np.arange(N) * 1e2, np.arange(N) * 1e4)
    return fig


@pytest.mark.mpl_image_compare
def test_span_labels():
    """
    Rigorous tests of spanning and aligned labels feature.
    """
    fig, axs = uplt.subplots([[1, 2, 4], [1, 3, 5]], refwidth=1.5, share=0, span=1)
    fig.format(xlabel="xlabel", ylabel="ylabel", abc="A.", abcloc="ul")
    axs[1].format()  # xlabel='xlabel')
    axs[2].format()
    return fig


@pytest.mark.mpl_image_compare
def test_title_deflection():
    """
    Test the deflection of titles above and below panels.
    """
    fig, ax = uplt.subplots()
    # ax.format(abc='A.', title='Title', titleloc='left', titlepad=30)
    tax = ax.panel_axes("top")
    ax.format(titleabove=False)  # redirects to bottom
    ax.format(abc="A.", title="Title", titleloc="left", titlepad=50)
    ax.format(xlabel="xlabel", ylabel="ylabel", ylabelpad=50)
    tax.format(title="Fear Me", title_kw={"size": "x-large"})
    tax.format(ultitle="Inner", titlebbox=True, title_kw={"size": "med-large"})
    return fig


@pytest.mark.mpl_image_compare
def test_complex_ticks():
    """
    Normally title offset with these different tick arrangements is tricky
    but `_update_title_position` accounts for edge cases.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].format(
        xtickloc="both",
        xticklabelloc="top",
        xlabelloc="top",
        title="title",
        xlabel="xlabel",
        suptitle="Test",
    )
    axs[1].format(
        xtickloc="both",
        xticklabelloc="top",
        # xlabelloc='top',
        xlabel="xlabel",
        title="title",
        suptitle="Test",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_both_ticklabels():
    """
    Test both tick labels.
    """
    fig, ax = uplt.subplots()  # when both, have weird bug
    ax.format(xticklabelloc="both", title="title", suptitle="Test")
    fig, ax = uplt.subplots()  # when *just top*, bug disappears
    ax.format(xtickloc="top", xticklabelloc="top", title="title", suptitle="Test")
    fig, ax = uplt.subplots()  # not sure here
    ax.format(xtickloc="both", xticklabelloc="neither", suptitle="Test")
    fig, ax = uplt.subplots()  # doesn't seem to change the title offset though
    ax.format(xtickloc="top", xticklabelloc="neither", suptitle="Test")
    return fig


def test_gridspec_copies():
    """
    Test whether gridspec copies work.
    """
    fig1, ax = uplt.subplots(ncols=2)
    gs = fig1.gridspec.copy(left=5, wspace=0, right=5)
    fig2 = uplt.figure()
    fig2.add_subplots(gs)
    fig = uplt.figure()
    with pytest.raises(ValueError):
        fig.add_subplots(gs)  # should raise error


@pytest.mark.mpl_image_compare
def test_aligned_outer_guides():
    """
    Test alignment adjustment.
    """
    fig, ax = uplt.subplot()
    h1 = ax.plot(np.arange(5), label="foo")
    h2 = ax.plot(np.arange(5) + 1, label="bar")
    h3 = ax.plot(np.arange(5) + 2, label="baz")
    ax.legend(h1, loc="bottom", align="left")
    ax.legend(h2, loc="bottom", align="right")
    ax.legend(h3, loc="b", align="c")
    ax.colorbar("magma", loc="right", align="top", shrink=0.4)  # same as length
    ax.colorbar("magma", loc="right", align="bottom", shrink=0.4)
    ax.colorbar("magma", loc="left", align="top", length=0.6)  # should offset
    ax.colorbar("magma", loc="left", align="bottom", length=0.6)
    ax.legend(h1, loc="top", align="right", pad="4pt", frame=False)
    ax.format(title="Very long title", titlepad=6, titleloc="left")
    return fig


@pytest.mark.parametrize(
    "test_case,refwidth,kwargs,setup_func,ref",
    [
        (
            "simple",
            1.5,
            {"ncols": 2},
            None,
            None,
        ),
        (
            "funky_layout",
            1.5,
            {"array": [[1, 1, 2, 2], [0, 3, 3, 0]]},
            lambda fig, axs: (
                axs[1].panel_axes("left"),
                axs.format(xlocator=0.2, ylocator=0.2),
            ),
            3,
        ),
        (
            "with_panels",
            2.0,
            {"array": [[1, 1, 2], [3, 4, 5], [3, 4, 6]], "hratios": (2, 1, 1)},
            lambda fig, axs: (
                axs[2].panel_axes("right", width=0.5),
                axs[0].panel_axes("bottom", width=0.5),
                axs[3].panel_axes("left", width=0.5),
            ),
            None,
        ),
    ],
)
@pytest.mark.mpl_image_compare
def test_reference_aspect(test_case, refwidth, kwargs, setup_func, ref):
    """
    Rigorous test of reference aspect ratio accuracy.
    """
    # Add ref and refwidth to kwargs
    subplot_kwargs = kwargs.copy()
    subplot_kwargs["refwidth"] = refwidth
    if ref is not None:
        subplot_kwargs["ref"] = ref

    # Create subplots
    fig, axs = uplt.subplots(**subplot_kwargs)

    # Run setup function if provided
    if setup_func is not None:
        setup_func(fig, axs)

    # Apply auto layout
    fig.auto_layout()
    # Assert reference width accuracy
    assert np.isclose(refwidth, axs[fig._refnum - 1]._get_size_inches()[0])
    return fig


@pytest.mark.mpl_image_compare
@pytest.mark.parametrize("share", ["limits", "labels"])
def test_axis_sharing(share):
    fig, ax = uplt.subplots(ncols=2, nrows=2, share=share, span=False)
    labels = ["A", "B", "C", "D"]
    for idx, axi in enumerate(ax):
        axi.scatter(idx, idx)
        axi.set_xlabel(labels[idx])
        axi.set_ylabel(labels[idx])

    # TODO: the labels are handled in a funky way. The plot looks fine but
    # the label are not "shared" that is the labels still exist but they
    # are not visible and instead there are new labels created. Need to
    # figure this out.
    # test left hand side
    if share != "labels":
        assert all([i == j for i, j in zip(ax[0].get_xlim(), ax[2].get_xlim())])
        assert all([i == j for i, j in zip(ax[0].get_ylim(), ax[1].get_ylim())])
        assert all([i == j for i, j in zip(ax[1].get_xlim(), ax[3].get_xlim())])
    elif share == "labels":
        ax.draw(
            fig.canvas.get_renderer()
        )  # forcing a draw to ensure the labels are shared
        # columns shares x label; top row should be empty
        assert ax[0].xaxis.get_label().get_visible() == False
        assert ax[1].xaxis.get_label().get_visible() == False

        assert ax[2].xaxis.get_label().get_visible() == True
        assert ax[2].get_xlabel() == "A"
        assert ax[3].xaxis.get_label().get_visible() == True
        assert ax[3].get_xlabel() == "B"

        # rows share ylabel
        assert ax[3].yaxis.get_label().get_visible() == False
        assert ax[1].yaxis.get_label().get_visible() == False

        assert ax[0].yaxis.get_label().get_visible() == True
        assert ax[2].yaxis.get_label().get_visible() == True
        assert ax[0].get_ylabel() == "B"
        assert ax[2].get_ylabel() == "D"

    return fig


@pytest.mark.parametrize(
    "layout",
    [
        [[1, 2], [3, 4]],  # simple 2x2
        [[1, 6, 2], [0, 3, 0], [4, 0, 5]],  # complex 3x3 with independent plots
        [[0, 0, 1, 1, 0, 0], [0, 2, 2, 3, 3, 0]],  # 1 spanning 2 different plot
        [
            [0, 2, 2, 3, 3, 0],
            [0, 0, 1, 1, 0, 0],
        ],  # horizontal inverse of the previous
        [
            [0, 2, 2, 0, 3, 3, 0],
            [0, 0, 1, 1, 1, 0, 0],
        ],  # horizontal inverse of the previous
    ],
)
@pytest.mark.mpl_image_compare
def test_label_sharing_top_right(layout):
    fig, ax = uplt.subplots(layout)
    ax.format(
        xticklabelloc="t",
        yticklabelloc="r",
        xlabel="xlabel",
        ylabel="ylabel",
        title="Test Title",
    )
    fig.canvas.draw()  # force redraw tick labels
    uplt.show(block=1)
    for axi in ax:
        assert axi._is_ticklabel_on("labelleft") == False
        assert axi._is_ticklabel_on("labelbottom") == False

    for side, axs in fig._get_border_axes().items():
        for axi in axs:
            if side == "top":
                assert axi._is_ticklabel_on("labeltop") == True
            if side == "right":
                assert axi._is_ticklabel_on("labelright") == True
    return fig


@pytest.mark.parametrize("layout", [[[1, 2], [3, 4]]])
@pytest.mark.mpl_image_compare
def test_panel_sharing_top_right(layout):
    fig, ax = uplt.subplots(layout)
    for dir in "left right top bottom".split():
        pax = ax[0].panel(dir)
    fig.canvas.draw()  # force redraw tick labels
    for dir, paxs in ax[0]._panel_dict.items():
        # Since we are sharing some of the ticks
        # should be hidden depending on where the panel is
        # in the grid
        for pax in paxs:
            match dir:
                case "left":
                    assert pax._is_ticklabel_on("labelleft")
                    assert pax._is_ticklabel_on("labelbottom")
                case "top":
                    assert pax._is_ticklabel_on("labeltop") == False
                    assert pax._is_ticklabel_on("labelbottom") == False
                    assert pax._is_ticklabel_on("labelleft")
                case "right":
                    print(pax._is_ticklabel_on("labelright"))
                    assert pax._is_ticklabel_on("labelright") == False
                    assert pax._is_ticklabel_on("labelbottom")
                case "bottom":
                    assert pax._is_ticklabel_on("labelleft")
                    assert pax._is_ticklabel_on("labelbottom") == False

        # The sharing axis is not showing any ticks
        assert ax[0]._is_ticklabel_on(dir) == False
    return fig
