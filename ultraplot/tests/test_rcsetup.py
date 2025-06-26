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
