import ultraplot as uplt, threading


def modify_rc():
    """
    Apply arbitrary rc parameters in a thread-safe manner.
    """
    id = threading.get_ident()  # set it to thread id
    with uplt.rc.context(fontsize=id):
        assert uplt.rc["font.size"] == id, f"Thread {id} failed to set rc params"


def test_setting_props_on_threads():
    """
    Test the thread safety of a context setting
    """
    # We spawn workers and these workers should try to set
    # an arbitrarry rc parameter. This should
    # be local to that context and not affect the main thread.
    fontsize = uplt.rc["font.size"]
    workers = []
    for worker in range(10):
        w = threading.Thread(target=modify_rc)
        workers.append(w)
        w.start()
    for w in workers:
        w.join()
    assert uplt.rc["font.size"] == fontsize
