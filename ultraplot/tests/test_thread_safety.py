import ultraplot as uplt, threading, pytest, warnings
import time, random


def modify_rc_on_thread(prop: str, value=None, with_context=True):
    """
    Apply arbitrary rc parameters in a thread-safe manner.
    """
    time.sleep(random.uniform(0, 0.001))
    if with_context:
        with uplt.rc.context(**{prop: value}):
            assert uplt.rc[prop] == value, f"Thread {id} failed to set rc params"
    else:
        uplt.rc[prop] = value
        assert uplt.rc[prop] == value, f"Thread {id} failed to set rc params"


def _spawn_and_run_threads(func, n=100, **kwargs):
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
        raise RuntimeError(
            f"Thread raised exception: {exceptions[0]} with {kwargs=}"
        ) from exceptions[0]

    if record:
        raise RuntimeError("Thread raised a warning")


@pytest.mark.parametrize("with_context", [True, False])
@pytest.mark.parametrize(
    "prop, options",
    [
        ("font.size", list(range(10))),
        ("abc", "A. a. aa aaa aaaa.".split()),
    ],
)
def test_setting_rc(prop, options, with_context):
    """
    Test the thread safety of a context setting
    """
    value = uplt.rc[prop]
    _spawn_and_run_threads(
        modify_rc_on_thread,
        prop=prop,
        options=options,
        with_context=with_context,
    )
    assert (
        uplt.rc[prop] == value
    ), f"Failed to reset {value=} after threads finished, {uplt.rc[prop]=}."
