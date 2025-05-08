#!/usr/bin/env python3
"""
Test projection features.
"""
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np, warnings
import ultraplot as uplt
import pytest


@pytest.mark.mpl_image_compare
def test_aspect_ratios():
    """
    Test aspect ratio adjustments.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].format(aspect=1.5)
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "cyl"), aspect=2)
    axs[0].set_aspect(1)
    return fig


if uplt.internals._version_mpl <= "3.2":

    @pytest.mark.mpl_image_compare
    def test_basemap_labels():
        """
        Add basemap labels.
        """
        fig, axs = uplt.subplots(ncols=2, proj="robin", refwidth=3, basemap=True)
        axs.format(coast=True, labels="rt")
        return fig


@pytest.mark.mpl_image_compare
def test_cartopy_labels():
    """
    Add cartopy labels.
    """
    fig, axs = uplt.subplots(ncols=2, proj="robin", refwidth=3)
    axs.format(coast=True, labels=True)
    axs[0].format(inlinelabels=True)
    axs[1].format(rotatelabels=True)
    return fig


@pytest.mark.mpl_image_compare
def test_cartopy_contours():
    """
    Test bug with cartopy contours. Sometimes results in global coverage
    with single color sometimes not.
    """
    N = 10
    fig = plt.figure(figsize=(5, 2.5))
    ax = fig.add_subplot(projection=ccrs.Mollweide())
    ax.coastlines()
    x = np.linspace(-180, 180, N)
    y = np.linspace(-90, 90, N)
    z = np.random.rand(N, N) * 10 - 5
    m = ax.contourf(
        x,
        y,
        z,
        transform=ccrs.PlateCarree(),
        cmap="RdBu_r",
        vmin=-5,
        vmax=5,
    )
    fig.colorbar(m, ax=ax)
    fig = uplt.figure()
    ax = fig.add_subplot(projection=uplt.Mollweide(), extent="auto")
    ax.coastlines()
    N = 10
    m = ax.contourf(
        np.linspace(0, 180, N),
        np.linspace(0, 90, N)[1::2],
        np.random.rand(N // 2, N) * 10 + 5,
        cmap="BuRd",
        transform=uplt.PlateCarree(),
        edgefix=False,
    )
    fig.colorbar(m, ax=ax)
    return fig


@pytest.mark.mpl_image_compare
def test_cartopy_manual():
    """
    Test alternative workflow without classes.
    """
    fig = uplt.figure()
    proj = uplt.Proj("npstere")
    # fig.add_axes([0.1, 0.1, 0.9, 0.9], proj='geo', map_projection=proj)
    fig.add_subplot(111, proj="geo", land=True, map_projection=proj)
    return fig


@pytest.mark.mpl_image_compare
def test_three_axes():
    """
    Test basic 3D axes here.
    """
    uplt.rc["tick.minor"] = False
    fig, ax = uplt.subplots(proj="3d", outerpad=3)
    return fig


@pytest.mark.mpl_image_compare
def test_projection_dicts():
    """
    Test projection dictionaries.
    """
    fig = uplt.figure(refnum=1)
    a = [[1, 0], [1, 4], [2, 4], [2, 4], [3, 4], [3, 0]]
    fig.subplots(a, proj={1: "cyl", 2: "cart", 3: "cart", 4: "cart"})
    return fig


@pytest.mark.mpl_image_compare
def test_polar_projections():
    """
    Rigorously test polar features here.
    """
    fig, ax = uplt.subplots(proj="polar")
    ax.format(
        rlabelpos=45,
        thetadir=-1,
        thetalines=90,
        thetalim=(0, 270),
        theta0="N",
        r0=0,
        rlim=(0.5, 1),
        rlines=0.25,
    )
    return fig


def test_sharing_axes():
    """
    Test sharing axes for GeoAxes
    """

    with warnings.catch_warnings(record=True) as record:
        # For rectilinear plots all axes can be shared
        fig, ax = uplt.subplots(ncols=3, nrows=3, share="all", proj="cyl")
        ax.format(
            land=True,
            lonlim=(-10, 10),  # make small to plot quicker
            latlim=(-10, 10),
        )
        lims = [ax[0].get_xlim(), ax[0].get_ylim()]
        for axi in ax[1:]:
            test_lims = [axi.get_xlim(), axi.get_ylim()]
            for this, other in zip(lims, test_lims):
                L = np.linalg.norm(np.array(this) - np.array(other))
                assert np.allclose(L, 0)
    # Should not emit any warnings
    assert len(record) == 0


def test_sharing_axes_different_projections():
    """
    Test sharing axes for GeoAxes
    """

    projs = ("cyl", "merc", "merc")
    with pytest.warns(uplt.internals.UltraPlotWarning) as record:
        fig, ax = uplt.subplots(ncols=1, nrows=3, share="all", proj=projs)
    assert len(record) == 1  # should only warn once
    ax.format(
        land=True,
        lonlim=(-10, 10),  # make small to plot quicker
        latlim=(-10, 10),
    )
    lims = [ax[0].get_xlim(), ax[0].get_ylim()]
    for axi in ax[1:]:
        assert axi._sharex is None
        assert axi._sharey is None
        test_lims = [axi.get_xlim(), axi.get_ylim()]
        for this, other in zip(lims, test_lims):
            L = np.linalg.norm(np.array(this) - np.array(other))
            assert not np.allclose(L, 0)
