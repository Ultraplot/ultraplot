import ultraplot as uplt, numpy as np, warnings
import pytest


@pytest.mark.mpl_image_compare
def test_geographic_single_projection():
    fig = uplt.figure(refwidth=3)
    axs = fig.subplots(nrows=2, proj="robin", proj_kw={"lon_0": 180})
    axs.format(
        suptitle="Figure with single projection",
        land=True,
        latlines=30,
        lonlines=60,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_geographic_multiple_projections():
    fig = uplt.figure()
    # Add projections
    gs = uplt.GridSpec(ncols=2, nrows=3, hratios=(1, 1, 1.4))
    for i, proj in enumerate(("cyl", "hammer", "npstere")):
        ax1 = fig.subplot(gs[i, 0], proj=proj, basemap=True)  # basemap
        ax2 = fig.subplot(gs[i, 1], proj=proj)  # cartopy

    # Format projections
    fig.format(
        land=True,
        suptitle="Figure with several projections",
        toplabels=("Basemap projections", "Cartopy projections"),
        toplabelweight="normal",
        latlines=30,
        lonlines=60,
        lonlabels="b",
        latlabels="r",  # or lonlabels=True, labels=True, etc.
    )
    fig.subplotgrid[-2:].format(
        latlines=20, lonlines=30
    )  # dense gridlines for polar plots
    uplt.rc.reset()
    return fig


@pytest.mark.mpl_image_compare
def test_drawing_in_projection_without_globe():
    # Fake data with unusual longitude seam location and without coverage over poles
    offset = -40
    lon = uplt.arange(offset, 360 + offset - 1, 60)
    lat = uplt.arange(-60, 60 + 1, 30)
    data = np.random.rand(len(lat), len(lon))

    globe = False
    string = "with" if globe else "without"
    gs = uplt.GridSpec(nrows=2, ncols=2)
    fig = uplt.figure(refwidth=2.5)
    for i, ss in enumerate(gs):
        ax = fig.subplot(ss, proj="kav7", basemap=(i % 2))
        cmap = ("sunset", "sunrise")[i % 2]
        if i > 1:
            ax.pcolor(lon, lat, data, cmap=cmap, globe=globe, extend="both")
        else:
            m = ax.contourf(lon, lat, data, cmap=cmap, globe=globe, extend="both")
            fig.colorbar(m, loc="b", span=i + 1, label="values", extendsize="1.7em")
    fig.format(
        suptitle=f"Geophysical data {string} global coverage",
        toplabels=("Cartopy example", "Basemap example"),
        leftlabels=("Filled contours", "Grid boxes"),
        toplabelweight="normal",
        leftlabelweight="normal",
        coast=True,
        lonlines=90,
        abc="A.",
        abcloc="ul",
        abcborder=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_drawing_in_projection_with_globe():
    # Fake data with unusual longitude seam location and without coverage over poles
    offset = -40
    lon = uplt.arange(offset, 360 + offset - 1, 60)
    lat = uplt.arange(-60, 60 + 1, 30)
    data = np.random.rand(len(lat), len(lon))

    globe = True
    string = "with" if globe else "without"
    gs = uplt.GridSpec(nrows=2, ncols=2)
    fig = uplt.figure(refwidth=2.5)
    for i, ss in enumerate(gs):
        ax = fig.subplot(ss, proj="kav7", basemap=(i % 2))
        cmap = ("sunset", "sunrise")[i % 2]
        if i > 1:
            ax.pcolor(lon, lat, data, cmap=cmap, globe=globe, extend="both")
        else:
            m = ax.contourf(lon, lat, data, cmap=cmap, globe=globe, extend="both")
            fig.colorbar(m, loc="b", span=i + 1, label="values", extendsize="1.7em")
    fig.format(
        suptitle=f"Geophysical data {string} global coverage",
        toplabels=("Cartopy example", "Basemap example"),
        leftlabels=("Filled contours", "Grid boxes"),
        toplabelweight="normal",
        leftlabelweight="normal",
        coast=True,
        lonlines=90,
        abc="A.",
        abcloc="ul",
        abcborder=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_geoticks():

    lonlim = (-140, 60)
    latlim = (-10, 50)
    basemap_projection = uplt.Proj(
        "cyl",
        lonlim=lonlim,
        latlim=latlim,
        backend="basemap",
    )
    fig, ax = uplt.subplots(
        ncols=3,
        proj=(
            "cyl",  # cartopy
            "cyl",  # cartopy
            basemap_projection,  # basemap
        ),
        share=0,
    )
    settings = dict(land=True, labels=True, lonlines=20, latlines=20)
    # Shows sensible "default"; uses cartopy backend to show the grid lines with ticks
    ax[0].format(
        lonlim=lonlim,
        latlim=latlim,
        **settings,
    )

    # Add lateral ticks only
    ax[1].format(
        latticklen=True,
        gridminor=True,
        lonlim=lonlim,
        latlim=latlim,
        **settings,
    )

    ax[2].format(
        latticklen=5.0,
        lonticklen=2.0,
        grid=False,
        gridminor=False,
        **settings,
    )
    return fig


def test_geoticks_input_handling(recwarn):
    fig, ax = uplt.subplots(proj="aeqd")
    # Should warn that about non-rectilinear projection.
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        ax.format(lonticklen=True)
    ax.format(lonticklen=None)
    assert len(recwarn) == 0
    # When set to None the latticks are not added.
    # No warnings should be raised.
    # Can parse a string
    ax.format(lonticklen="1em")


@pytest.mark.parametrize(
    ("layout", "lonlabels", "latlabels"),
    [
        ([1, 2], "tb", "lr"),
        ([1, 2], "r", "t"),
        ([[1, 2, 3], [4, 5, 3]], "t", "lr"),
    ],
)
@pytest.mark.mpl_image_compare
def test_geoticks_shared(layout, lonlabels, latlabels):
    fig, ax = uplt.subplots(layout, proj="cyl", share="all")
    ax.format(
        latlim=(0, 10),  # smaller rangers are quicker
        lonlim=(0, 10),
        lonlines=10,
        latlines=10,
        land=True,  # enable land
        labels=True,  # enable tick labels
        latticklen=True,  # show ticks
        lonticklen=True,  # show ticks
        grid=True,
        gridminor=False,
        lonlabels=lonlabels,
        latlabels=latlabels,
    )
    return fig


def test_geoticks_shared_non_rectilinear():
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        fig, ax = uplt.subplots(ncols=2, proj="aeqd", share="all")
        ax.format(
            land=True,
            labels=True,
            lonlabels="all",
            latlabels="all",
        )
        fig.canvas.draw()  # draw is necessary to invoke the warning
    return fig


def test_lon0_shifts():
    """
    Check if a shift with lon0 actually shifts the
    view port labels and ticks
    """
    # Note for small enough shifts, e.g. +- 10 we are
    # still showing zero due to the formatting logic
    fig, ax = uplt.subplots(proj="cyl", proj_kw=dict(lon_0=90))
    ax.format(land=True, labels=True)
    locator = ax[0]._lonaxis.get_major_locator()
    formatter = ax[0]._lonaxis.get_major_formatter()
    locs = locator()
    half = len(locs) // 2
    if len(locs) % 2:
        half += 1
    formatted_ticks = np.array([formatter(x) for x in locs])
    for loc, format in zip(locs, formatted_ticks):
        # Get normalized coordinates
        loc = (loc + 180) % 360 - 180
        # Check if the labels are matching the location
        # abs is taken due to north-west
        str_loc = str(abs(int(loc)))
        n = len(str_loc)
        assert str_loc == format[:n]
    assert locs[0] != 0  # we should not be a 0 anymore
    return fig


def test_sharing_cartopy():

    def are_labels_on(ax, which=["top", "bottom", "right", "left"]) -> tuple[bool]:
        gl = ax.gridlines_major

        on = [False, False, False, False]
        for idx, labeler in enumerate(which):
            if getattr(gl, f"{labeler}_labels"):
                on[idx] = True
        return on

    n = 3
    settings = dict(land=True, ocean=True, labels="both")
    fig, ax = uplt.subplots(ncols=n, nrows=n, share="all", proj="cyl")
    ax.format(**settings)
    fig.canvas.draw()  # need a draw to trigger ax.draw for  sharing

    expectations = (
        [True, False, False, True],
        [True, False, False, False],
        [True, False, True, False],
        [False, False, False, True],
        [False, False, False, False],
        [False, False, True, False],
        [False, True, False, True],
        [False, True, False, False],
        [False, True, True, False],
    )
    for axi in ax:
        state = are_labels_on(axi)
        expectation = expectations[axi.number - 1]
        for i, j in zip(state, expectation):
            assert i == j

    layout = [
        [1, 2, 0],
        [1, 2, 5],
        [3, 4, 5],
        [3, 4, 0],
    ]

    fig, ax = uplt.subplots(layout, share="all", proj="cyl")
    ax.format(**settings)
    fig.canvas.draw()  # need a draw to trigger ax.draw for  sharing

    expectations = (
        [True, False, False, True],  # top left
        [True, False, True, False],  # top right
        [False, True, False, True],  # bottom left
        [False, True, True, False],  # bottom right
        [True, True, True, False],  # right plot (5)
    )
    for axi in ax:
        state = are_labels_on(axi)
        expectation = expectations[axi.number - 1]
        assert all([i == j for i, j in zip(state, expectation)])
    return fig


def test_toggle_gridliner_labels():
    """
    Test whether we can toggle the labels on or off
    """
    # Cartopy backend
    fig, ax = uplt.subplots(proj="cyl", backend="cartopy")
    ax[0]._toggle_gridliner_labels(left=False, bottom=False)
    gl = ax[0].gridlines_major

    assert gl.left_labels == False
    assert gl.right_labels == False
    assert gl.top_labels == False
    assert gl.bottom_labels == False
    ax[0]._toggle_gridliner_labels(top=True)
    assert gl.top_labels == True
    uplt.close(fig)

    # Basemap backend
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax.format(land=True, labels="both")  # need this otherwise no labels are printed
    ax[0]._toggle_gridliner_labels(left=False, bottom=False, right=False, top=False)
    gl = ax[0].gridlines_major

    # All label are off
    for gli in gl:
        for _, (line, labels) in gli.items():
            for label in labels:
                assert label.get_visible() == False

    # Should be off
    ax[0]._toggle_gridliner_labels(top=True)
    # Gridliner labels are not added for the top (and I guess right for GeoAxes).
    # Need to figure out how this is set in matplotlib
    dir_labels = ax[0]._get_gridliner_labels(
        left=True, right=True, top=True, bottom=True
    )
    for dir, labels in dir_labels.items():
        expectation = False
        if dir in "top":
            expectation = True
        for label in labels:
            assert label.get_visible() == expectation
    uplt.close(fig)


def test_sharing_geo_limits():
    """
    Test that we can share limits on GeoAxes
    """
    fig, ax = uplt.subplots(
        ncols=2,
        proj="cyl",
        share=False,
    )
    expectation = dict(
        lonlim=(-10, 10),
        latlim=(-13, 15),
    )
    ax.format(land=True)
    ax[0].format(**expectation)

    before_lon = ax[1]._lonaxis.get_view_interval()
    before_lat = ax[1]._lataxis.get_view_interval()

    # Need to set this otherwise will be skipped
    fig._sharey = 3
    ax[0]._sharey_setup(ax[1])  # manually call setup
    ax[0]._sharey_limits(ax[1])  # manually call sharing limits
    # Limits should now be shored for lat but not for lon
    after_lat = ax[1]._lataxis.get_view_interval()

    # We are sharing y which is the latitude axis
    assert all([np.allclose(i, j) for i, j in zip(expectation["latlim"], after_lat)])
    # We are not sharing longitude yet
    assert all(
        [
            not np.allclose(i, j)
            for i, j in zip(expectation["lonlim"], ax[1]._lonaxis.get_view_interval())
        ]
    )

    ax[0]._sharex_setup(ax[1])
    ax[0]._sharex_limits(ax[1])
    after_lon = ax[1]._lonaxis.get_view_interval()

    assert all([not np.allclose(i, j) for i, j in zip(before_lon, after_lon)])
    assert all([np.allclose(i, j) for i, j in zip(after_lon, expectation["lonlim"])])
    uplt.close(fig)
