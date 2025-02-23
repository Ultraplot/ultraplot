#!/usr/bin/env python3
"""
The "3D" axes class.
"""
from . import base, shared

try:
    from mpl_toolkits.mplot3d import Axes3D
except ImportError:
    Axes3D = object


class ThreeAxes(shared._SharedAxes, base.Axes, Axes3D):
    """
    Simple mix-in of `ultraplot.axes.Axes` with `~mpl_toolkits.mplot3d.axes3d.Axes3D`.

    Important
    ---------
    Note that this subclass does *not* implement the :class:`~ultraplot.axes.PlotAxes`
    plotting overrides. This axes subclass can be used by passing ``proj='3d'`` or
    ``proj='three'`` to axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and `~ultraplot.figure.Figure.subplots`.
    """

    # TODO: Figure out a way to have internal Axes3D calls to plotting commands
    # access the overrides rather than the originals? May be impossible.
    _name = "three"
    _name_aliases = ("3d",)

    def __init__(self, *args, **kwargs):
        import mpl_toolkits.mplot3d  # noqa: F401 verify package is available

        kwargs.setdefault("alpha", 0.0)
        super().__init__(*args, **kwargs)
