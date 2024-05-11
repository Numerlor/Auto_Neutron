# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class ErrorWindowGUI(QtWidgets.QDialog):
    """Display basic information to informate user on how to report bug after an error has occurred."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.info_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.set_point_size(15)
        self.info_label.font = font

        self.text_browser = QtWidgets.QTextBrowser(self)
        self.text_browser.open_external_links = True

        self.button_layout = QtWidgets.QHBoxLayout()
        self.quit_button = QtWidgets.QPushButton(self)
        self.send_log = QtWidgets.QPushButton(self)
        self.save_button = QtWidgets.QPushButton(self)
        self.quit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.send_log.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.save_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )

        self.button_layout.add_widget(self.save_button)
        self.button_layout.add_widget(self.send_log)
        self.button_layout.add_widget(self.quit_button)

        self.main_layout.add_widget(self.info_label)
        self.main_layout.add_widget(self.text_browser)
        self.main_layout.add_layout(self.button_layout)
        self.set_modal(True)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.info_label.text = _("An unexpected error has occurred")
        self.quit_button.text = _("Quit")
        self.send_log.text = _("Send session log")
        self.save_button.text = _("Save route")
