# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class VersionDownloadConfirmDialogGUI(QtWidgets.QDialog):
    """GUI for a window that prompts the user to download or skip a new release."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._button_layout = QtWidgets.QHBoxLayout()

        self._text_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(18)
        self._text_label.setFont(font)

        self._changelog_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self._changelog_label.setFont(font)

        self._changelog_browser = QtWidgets.QTextBrowser(self)

        self._download_button = QtWidgets.QPushButton(self)
        self._download_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self._skip_button = QtWidgets.QPushButton(self)
        self._skip_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )
        self._button_layout.addWidget(self._skip_button)
        self._button_layout.addWidget(self._download_button)

        self._main_layout.addWidget(self._text_label)
        self._main_layout.addWidget(self._changelog_label)
        self._main_layout.addWidget(self._changelog_browser)
        self._main_layout.addLayout(self._button_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._changelog_label.setText(_("Changelog"))
        self._download_button.setText(_("Download"))
        self._skip_button.setText(_("Skip"))
