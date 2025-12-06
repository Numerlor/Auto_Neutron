# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import collections.abc
import typing as t
from functools import partial

from PySide6 import QtWidgets

_WindowT = t.TypeVar("_WindowT", bound=QtWidgets.QWidget)


def create_or_activate_window(
    window_type: type[_WindowT],
    namespace: collections.abc.Hashable,
    *args: object,
    _window_cache: dict[
        tuple[type[QtWidgets.QWidget], collections.abc.Hashable], QtWidgets.QWidget
    ] = {},  # noqa: B006 used as persistent cache.
    **kwargs: object,
) -> _WindowT | None:
    """
    Create window of `window_type`, or bring it to the top if a window in the namespace is already opened.

    If an existing window is brought to the top, return None, otherwise return the new window.
    """
    try:
        existing_window = _window_cache[(window_type, namespace)]
    except KeyError:
        new_window = window_type(*args, **kwargs)
        window_key = (window_type, namespace)
        _window_cache[window_key] = new_window
        new_window.destroyed.connect(partial(_window_cache.pop, window_key))
        return new_window
    else:
        existing_window.activateWindow()
        existing_window.raise_()
