# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class VersionDownloadConfirmDialogGUI(QtWidgets.QDialog):
    """GUI for a window that prompts the user to download or skip a new release."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._button_layout = QtWidgets.QHBoxLayout()

        self._text_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(18)
        self._text_label.font = font

        self._changelog_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(10)
        self._changelog_label.font = font

        self._changelog_browser = QtWidgets.QTextBrowser(self)

        self._download_button = QtWidgets.QPushButton(self)
        self._download_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self._skip_button = QtWidgets.QPushButton(self)
        self._skip_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self._button_layout.add_widget(self._skip_button)
        self._button_layout.add_widget(self._download_button)

        self._main_layout.add_widget(self._text_label)
        self._main_layout.add_widget(self._changelog_label)
        self._main_layout.add_widget(self._changelog_browser)
        self._main_layout.add_layout(self._button_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._changelog_label.text = _("Changelog")
        self._download_button.text = _("Download")
        self._skip_button.text = _("Skip")
