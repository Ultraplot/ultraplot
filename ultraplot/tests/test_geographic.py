import ultraplot as uplt, numpy as np, warnings
import pytest
from unittest import mock


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
    # When set to None the latticks are not added.
    # No warnings should be raised.
    ax.format(lonticklen=None)
    assert len(recwarn) == 0
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
    uplt.close(fig)


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


def test_copy_locator_props():
    """
    When sharing axes the locator properties need
    to move as well.
    """

    fig, ax = uplt.subplots(ncols=2, proj="cyl", share=0)

    g1 = ax[0]._lonaxis
    g2 = ax[1]._lonaxis
    props = [
        "isDefault_majloc",
        "isDefault_minloc",
        "isDefault_majfmt",
    ]
    for prop in props:
        assert hasattr(g1, prop)
        assert hasattr(g2, prop)
        setattr(g1, prop, False)
        setattr(g2, prop, True)

    # The copy happens when the properties between g1 and g2 differ. Note this copies from g1 to g2.
    g1._copy_locator_properties(g2)
    for prop in props:
        assert getattr(g1, prop) == False
        assert getattr(g1, prop) == getattr(g2, prop)


def test_turn_off_tick_labels_basemap():
    """
    Check if we can toggle the labels off for GeoAxes
    with a basemap backend.
    """
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax.format(labels="both")
    locators = ax[0].gridlines_major

    def test_if_labels_are(is_on, locator):
        from matplotlib import text as mtext

        for loc, objects in locator.items():
            for object in objects:
                if isinstance(object, list) and len(objects) > 0:
                    object = object[0]
                if isinstance(object, mtext.Text):
                    assert object.get_visible() == is_on

    # Check if the labels are on
    for locator in locators:
        test_if_labels_are(is_on=True, locator=locator)

    # Turn off both the labels
    for locator in locators:
        ax[0]._turnoff_tick_labels(locator)

    # Check if  are off
    for locator in locators:
        test_if_labels_are(is_on=False, locator=locator)
    uplt.close(fig)


def test_get_gridliner_labels_cartopy():
    from itertools import product

    fig, ax = uplt.subplots(proj="cyl", backend="cartopy")
    ax.format(labels="both")
    bools = [True, False]

    for bottom, top, left, right in product(bools, bools, bools, bools):
        ax[0]._toggle_gridliner_labels(
            left=left,
            right=right,
            top=top,
            bottom=bottom,
        )
        fig.canvas.draw()  # need draw to retrieve the labels
        labels = ax[0]._get_gridliner_labels(
            bottom=bottom,
            top=top,
            left=left,
            right=right,
        )
        for dir, is_on in zip(
            "bottom top left right".split(), [bottom, top, left, right]
        ):
            if is_on:
                assert len(labels.get(dir, [])) > 0
            else:
                assert len(labels.get(dir, [])) == 0
    uplt.close(fig)


def test_sharing_levels():
    """
    We can share limits or labels.
    We check if we can do both for the GeoAxes.
    """
    # We can share labels, limits, scale or all
    # For labels we share the axis labels but nothing else
    # Limits shares both labels and ticks
    # Scale (= True) will also share the scale
    # All does all the ticks across all plots
    # (not necessarily on same line)
    #
    # Succinctly this means that for
    # - share = 0: no sharing takes place, each
    # axis have their tick labels and data limits are their
    # own
    # - share = 1: x and y labels are shared but nothing else
    # - share = 2: ticks are shared  but still are shown
    # - share = 3: ticks are shared and turned of for the ticks
    # facing towards the "inside"
    # - share = 4: ticks are shared, and the data limits are the same

    x = np.array([0, 10])
    y = np.array([0, 10])
    sharing_levels = [0, 1, 2, 3, 4]
    lonlim = latlim = np.array((-10, 10))

    def assert_views_are_sharing(ax):
        # We are testing a 2x2 grid here
        match ax.number - 1:
            # Note ax.number is idx + 1
            case 0:
                targets = [1, 2]
                sharing_x = [False, True]
                sharing_y = [True, False]
            case 1:
                targets = [0, 3]
                sharing_x = [False, True]
                sharing_y = [True, False]
            case 2:
                targets = [0, 3]
                sharing_x = [True, False]
                sharing_y = [False, True]
            case 3:
                targets = [1, 2]
                sharing_x = [True, False]
                sharing_y = [False, True]
        lonview = ax._lonaxis.get_view_interval()
        latview = ax._lataxis.get_view_interval()
        for target, share_x, share_y in zip(targets, sharing_x, sharing_y):
            other = ax.figure.axes[target]
            target_lon = other._lonaxis.get_view_interval()
            target_lat = other._lataxis.get_view_interval()

            l1 = np.linalg.norm(
                np.asarray(lonview) - np.asarray(target_lon),
            )
            l2 = np.linalg.norm(
                np.asarray(latview) - np.asarray(target_lat),
            )
            level = ax.figure._get_sharing_level()
            if level <= 1:
                share_x = share_y = False
            assert np.allclose(l1, 0) == share_x
            assert np.allclose(l2, 0) == share_y

    for level in sharing_levels:
        fig, ax = uplt.subplots(ncols=2, nrows=2, proj="cyl", share=level)
        ax.format(labels="both")
        for axi in ax:
            axi.format(
                lonlim=lonlim * axi.number,
                latlim=latlim * axi.number,
            )
        fig.canvas.draw()
        for idx, axi in enumerate(ax):
            axi.plot(x * (idx + 1), y * (idx + 1))

        fig.canvas.draw()  # need this to update the labels
        # All the labels should be on
        for axi in ax:
            side_labels = axi._get_gridliner_labels(
                left=True,
                right=True,
                top=True,
                bottom=True,
            )
            s = 0
            for dir, labels in side_labels.items():
                s += any([label.get_visible() for label in labels])

            assert_views_are_sharing(axi)
            # When we share the labels but not the limits,
            # we expect all ticks to be on
            if level < 3:
                assert s == 4
            else:
                assert s == 2
        uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_cartesian_and_geo():
    """
    Test that axis sharing does not prevent
    running Cartesian based plot functions
    """

    fig, ax = uplt.subplots(
        ncols=2,
        proj="cyl",
        share=True,
    )
    original_toggler = ax[0]._toggle_gridliner_labels
    with mock.patch.object(
        ax[0],
        "_toggle_gridliner_labels",
        autospec=True,
        side_effect=original_toggler,
    ) as mocked:
        # Make small range to speed up plotting
        ax.format(land=True, lonlim=(-10, 10), latlim=(-10, 10))
        ax[0].pcolormesh(np.random.rand(10, 10))
        ax[1].scatter(*np.random.rand(2, 100))
        ax[0]._apply_axis_sharing()
        assert mocked.call_count == 1
    return fig


def test_check_tricontourf():
    """
    Ensure that tricontour functions are getting
    the transform for GeoAxes.
    """
    import cartopy.crs as ccrs

    lon0 = 90
    lon = np.linspace(-180, 180, 10)
    lat = np.linspace(-90, 90, 10)
    lon2d, lat2d = np.meshgrid(lon, lat)

    data = np.sin(3 * np.radians(lat2d)) * np.cos(2 * np.radians(lon2d))
    # Place a box with constant values in order to have a visual reference
    mask_box = (lon2d >= 0) & (lon2d <= 20) & (lat2d >= 0) & (lat2d <= 20)
    data[mask_box] = 1.5

    lon, lat, data = map(np.ravel, (lon2d, lat2d, data))

    fig, ax = uplt.subplots(proj="cyl", proj_kw={"lon0": lon0})
    original_func = ax[0]._call_native
    with mock.patch.object(
        ax[0],
        "_call_native",
        autospec=True,
        side_effect=original_func,
    ) as mocked:
        for func in "tricontour tricontourf".split():
            getattr(ax[0], func)(lon, lat, data)
        assert "transform" in mocked.call_args.kwargs
        assert isinstance(mocked.call_args.kwargs["transform"], ccrs.PlateCarree)
    uplt.close(fig)
