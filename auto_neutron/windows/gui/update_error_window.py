# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class UpdateErrorWindowGUI(QtWidgets.QDialog):
    """The base GUI for a window that shows simple error information to the user."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._button_layout = QtWidgets.QHBoxLayout()

        self._text_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self._text_label.setFont(font)

        self._error_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self._error_label.setFont(font)
        self._error_label.setWordWrap(True)

        self._close_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self._close_label.setFont(font)

        self._main_layout.addWidget(self._text_label)
        self._main_layout.addWidget(self._error_label)
        self._main_layout.addWidget(self._close_label)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._text_label.setText(
            _("An error has occurred while handling the new release:")
        )
        self._close_label.setText(_("Close this window to retry or continue."))
