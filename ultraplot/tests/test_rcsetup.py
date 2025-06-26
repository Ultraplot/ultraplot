import ultraplot as uplt, pytest


def test_rc_repr():
    """
    Test representation for internal consistency
    """
    default = uplt.internals.rcsetup._rc_ultraplot_default

    tmp = uplt.internals.rcsetup._RcParams(
        data=default, validate=uplt.internals.rcsetup._rc_ultraplot_validate
    )
    s = uplt.rc.rc_ultraplot.__repr__()
    ss = uplt.rc.rc_ultraplot.__repr__()
    assert s == ss


def test_rc_init_invalid_key():
    # If we add a key that does not exist, a key error is raised on init
    default = uplt.internals.rcsetup._rc_ultraplot_default.copy()
    default["doesnotexist"] = "test"
    with pytest.raises(KeyError):
        uplt.internals.rcsetup._RcParams(data=default)


def test_tight_layout_warnings():
    """
    Tight layout is disabled in ultraplot as we provide our own layout engine. Setting these values should raise a warning.
    """
    with pytest.warns(uplt.warnings.UltraPlotWarning) as record:
        fig, ax = uplt.subplots(tight_layout=True)
        uplt.close(fig)
        fig, ax = uplt.subplots(constrained_layout=True)
        uplt.close(fig)
    # need to check why the number of errors are much larger
    # than 2
    assert (
        len(record) >= 2
    ), f"Expected two warnings for tight layout settings, got {len(record)}"
