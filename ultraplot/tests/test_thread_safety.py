import ultraplot as uplt, threading, pytest, warnings


def modify_rc_in_context(prop: str, value=None):
    """
    Apply arbitrary rc parameters in a thread-safe manner.
    """
    with uplt.rc.context(fontsize=value):
        assert uplt.rc[prop] == value, f"Thread {id} failed to set rc params"


def modify_rc_on_thread(prop: str, value=None):
    id = threading.get_ident()  # set it to thread id
    uplt.rc[prop] = value
    assert uplt.rc[prop] == value, f"Thread {id} failed to set rc params {prop}={value}"


def _spawn_and_run_threads(func, n=10, **kwargs):
    options = kwargs.pop("options")
    workers = []
    exceptions = []

    def wrapped_func(**kw):
        try:
            func(**kw)
        except Exception as e:
            exceptions.append(e)

    for worker in range(n):
        kw = kwargs.copy()
        kw["value"] = options[worker % len(options)]
        w = threading.Thread(target=wrapped_func, kwargs=kw)
        workers.append(w)
        w.start()

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")  # catch all warnings
        for w in workers:
            w.join()

    if exceptions:
        raise RuntimeError(f"Thread raised exception: {exceptions[0]}") from exceptions[
            0
        ]

    if record:
        raise RuntimeError("Thread raised a warning")


def test_setting_within_context():
    """
    Test the thread safety of a context setting
    """
    # We spawn workers and these workers should try to set
    # an arbitrarry rc parameter. This should
    # be local to that context and not affect the main thread.
    prop, value = "font.size", uplt.rc["font.size"]
    options = list(range(10))
    _spawn_and_run_threads(modify_rc_in_context, prop=prop, options=options)
    assert uplt.rc[prop] == value


def test_setting_without_context():
    """
    Test the thread safety of a context setting
    """
    # We spawn workers and these workers should try to set
    # an arbitrarry rc parameter. This should
    # be local to that context and not affect the main thread.
    #
    # Test an ultraplot  parameter
    prop = "abc"
    value = uplt.rc[prop]
    options = "A. a. aa".split()
    _spawn_and_run_threads(modify_rc_on_thread, prop=prop, options=options)
    assert uplt.rc[prop] == value

    prop, value = "font.size", uplt.rc["font.size"]
    options = list(range(10))
    _spawn_and_run_threads(modify_rc_on_thread, prop=prop, options=options)
