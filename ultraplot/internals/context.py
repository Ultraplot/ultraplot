#!/usr/bin/env python3
"""
Utilities for manging context.
"""
import threading
from . import ic  # noqa: F401


class _empty_context(object):
    """
    A dummy context manager.
    """

    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):  # noqa: U100
        pass


class _state_context(object):
    """
    Temporarily modify attribute(s) for an arbitrary object.
    """

    _lock = (
        threading.RLock()
    )  # class-wide reentrant lock (or use instance-wide if needed)

    def __init__(self, obj, **kwargs):
        self._obj = obj
        self._attrs_new = kwargs
        self._attrs_prev = {
            key: getattr(obj, key) for key in kwargs if hasattr(obj, key)
        }

    def __enter__(self):
        self._lock.acquire()
        for key, value in self._attrs_new.items():
            setattr(self._obj, key, value)

    def __exit__(self, *args):
        for key in self._attrs_new.keys():
            if key in self._attrs_prev:
                setattr(self._obj, key, self._attrs_prev[key])
            else:
                delattr(self._obj, key)
        self._lock.release()
