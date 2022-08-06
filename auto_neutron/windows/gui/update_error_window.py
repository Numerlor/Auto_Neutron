# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class UpdateErrorWindowGUI(QtWidgets.QDialog):
    """The base GUI for a window that shows simple error information to the user."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._button_layout = QtWidgets.QHBoxLayout()

        self._text_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(10)
        self._text_label.font = font

        self._error_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(10)
        self._error_label.font = font
        self._error_label.word_wrap = True

        self._close_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(10)
        self._close_label.font = font

        self._main_layout.add_widget(self._text_label)
        self._main_layout.add_widget(self._error_label)
        self._main_layout.add_widget(self._close_label)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._text_label.text = _(
            "An error has occurred while handling the new release:"
        )
        self._close_label.text = _("Close this window to retry or continue.")
