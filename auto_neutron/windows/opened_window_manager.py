# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import collections.abc
import typing as t

import shiboken6
from PySide6 import QtCore, QtWidgets

_WindowT = t.TypeVar("_WindowT", bound=QtWidgets.QWidget)


class _OpenedWindowManager(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self._window_cache = dict[
            tuple[type[QtWidgets.QWidget], collections.abc.Hashable], QtWidgets.QWidget
        ]()
        self._window_to_cache_entry = dict[
            int, tuple[type[QtWidgets.QWidget], collections.abc.Hashable]
        ]()

    def create_or_activate_window(
        self,
        window_type: type[_WindowT],
        namespace: collections.abc.Hashable,
        *args: object,
        **kwargs: object,
    ) -> _WindowT | None:
        """
        Create window of `window_type`, or bring it to the top if a window in the namespace is already opened.

        If an existing window is brought to the top, return None, otherwise return the new window.
        """
        try:
            existing_window = self._window_cache[(window_type, namespace)]
        except KeyError:
            new_window = window_type(*args, **kwargs)
            new_window.install_event_filter(self)
            self._window_cache[(window_type, namespace)] = new_window
            cpp_address = shiboken6.getCppPointer(new_window)[0]
            self._window_to_cache_entry[cpp_address] = (window_type, namespace)
            return new_window
        else:
            existing_window.activate_window()
            existing_window.raise_()

    def event_filter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Delete windows from caches if they're closed."""
        if event.type() is QtCore.QEvent.Destroy:
            watched_addr = shiboken6.getCppPointer(watched)[0]
            del self._window_cache[self._window_to_cache_entry[watched_addr]]
            del self._window_to_cache_entry[watched_addr]
        return False


_opened_window_manager = _OpenedWindowManager()
create_or_activate_window = _opened_window_manager.create_or_activate_window
