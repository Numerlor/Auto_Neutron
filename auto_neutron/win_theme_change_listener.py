# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor


from __future__ import annotations

import collections.abc
import ctypes.wintypes
import typing as t
import winreg
from types import TracebackType

from PySide6 import QtCore
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.utils.utils import get_application

if t.TYPE_CHECKING:
    from shiboken6 import VoidPtr

_WM_SETTINGCHANGE = 0x1A
_REGISTRY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"


class _EventFilter(QtCore.QAbstractNativeEventFilter):
    """Filter native events and call the callback mapped to that message type."""

    def __init__(
        self,
        callbacks: dict[int, collections.abc.Callable[[ctypes.wintypes.MSG], t.Any]],
    ):
        super().__init__()
        self._callbacks = callbacks

    def native_event_filter(self, event_type: bytes, message_ptr: VoidPtr) -> bool:
        """Call the callback with the MSG object."""
        msg = ctypes.wintypes.MSG.from_address(int(message_ptr))
        callback = self._callbacks.get(msg.message)
        if callback is not None:
            callback(msg)

        return False


class WinThemeChangeListener(QtCore.QObject):
    """
    Listen for Windows app theme mode changes, and emit `theme_changed` on changes.

    The `theme_changed` signal is passed an argument indicating whether the OS dark mode is active.
    """

    theme_changed = QtCore.Signal(bool)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._change_timer = QtCore.QTimer(parent)
        self._change_timer.single_shot_ = True
        self._change_timer.interval = 500
        self._change_timer.timeout.connect(self._emit_if_changed)
        self._registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH)
        self._dark_theme = self._os_dark_theme()
        self._event_filter = _EventFilter(
            {_WM_SETTINGCHANGE: self._start_timer_on_setting_change}
        )

    @property
    def dark_theme(self) -> bool:
        """Is the OS app dark theme enabled."""
        return self._dark_theme

    def _start_timer_on_setting_change(self, msg: ctypes.wintypes.MSG) -> None:
        """Schedule `_emit_if_changed` to be run."""
        # We're starting the method indirectly through the timer to avoid hitting the registry needlessly,
        # as Windows emits around a dozen `ImmersiveColorSet` messages when the theme is changed.
        if ctypes.cast(msg.lParam, ctypes.wintypes.LPWSTR).value == "ImmersiveColorSet":
            self._change_timer.start()

    @QtCore.Slot()
    def _emit_if_changed(self) -> None:
        """Emit the `theme_changed` signal if the theme changed from the current value."""
        use_dark_theme = self._os_dark_theme()
        if use_dark_theme != self.dark_theme:
            self._dark_theme = use_dark_theme
            self.theme_changed.emit(self.dark_theme)

    def _os_dark_theme(self) -> bool:
        """Check if the OS is using a dark theme for apps."""
        use_light_theme, _ = winreg.QueryValueEx(
            self._registry_key, "AppsUseLightTheme"
        )
        return not use_light_theme

    def __enter__(self):
        """Make this object a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType | None,
    ):
        """Close the key when exiting."""
        self._registry_key.Close()
        return False


def create_listener(
    parent: QtCore.QObject | None = None,
) -> WinThemeChangeListener:
    """Create a `WinThemeChangeListener` and register it with the app."""
    listener = WinThemeChangeListener(parent)
    get_application().install_native_event_filter(listener._event_filter)
    return listener
