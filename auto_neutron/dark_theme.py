# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import functools

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class _ThemeSelector:
    """Allow changing the app's theme through the `set_theme` method."""

    # The palettes are cached because of a bug where reapplying the same dark palette but as a new QPalette instance
    # caused the app's style to revert back to the default instead of being unchanged.

    def __init__(self):
        self.is_dark = False

    def set_theme(self, is_dark: bool) -> None:
        """Set the app's theme depending on `is_dark`."""
        if is_dark:
            self._app.set_palette(self._dark_palette)
        else:
            self._app.set_palette(self._light_palette)
        self.is_dark = is_dark

    @functools.cached_property
    def _dark_palette(self) -> QtGui.QPalette:
        """Create a dark themed palette."""
        p = QtGui.QPalette()
        p.set_color(QtGui.QPalette.Window, QtGui.QColor(35, 35, 35))
        p.set_color(QtGui.QPalette.WindowText, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        p.set_color(QtGui.QPalette.Text, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Button, QtGui.QColor(60, 60, 60))
        p.set_color(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
        p.set_color(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        p.set_color(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        p.set_color(QtGui.QPalette.PlaceholderText, QtGui.QColor(110, 110, 100))
        p.set_color(QtGui.QPalette.Link, QtGui.QColor(0, 123, 255))
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Light,
            QtGui.QColor(0, 0, 0),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Text,
            QtGui.QColor(110, 110, 100),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.WindowText,
            QtGui.QColor(110, 110, 100),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.ButtonText,
            QtGui.QColor(110, 110, 100),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Button,
            QtGui.QColor(50, 50, 50),
        )

        return p

    @functools.cached_property
    def _light_palette(self) -> QtGui.QPalette:
        """Create a light themed palette."""
        p = self._app.style().standard_palette()
        p.set_color(QtGui.QPalette.Link, QtGui.QColor(0, 123, 255))
        return p

    @functools.cached_property
    def _app(self) -> QtWidgets.QApplication:
        """Get the application's instance."""
        return QtWidgets.QApplication.instance()


selector = _ThemeSelector()
set_theme = selector.set_theme


def is_dark() -> bool:
    """Return True if the app is using the dark theme, False otherwise."""
    return selector.is_dark
