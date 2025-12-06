# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtGui, QtWidgets


class ErrorWindowGUI(QtWidgets.QDialog):
    """Display basic information to informate user on how to report bug after an error has occurred."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.info_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.info_label.setFont(font)

        self.text_browser = QtWidgets.QTextBrowser(self)
        self.text_browser.setOpenExternalLinks(True)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.quit_button = QtWidgets.QPushButton(self)
        self.send_log = QtWidgets.QPushButton(self)
        self.save_button = QtWidgets.QPushButton(self)
        self.quit_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )
        self.send_log.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )
        self.save_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.send_log)
        self.button_layout.addWidget(self.quit_button)

        self.main_layout.addWidget(self.info_label)
        self.main_layout.addWidget(self.text_browser)
        self.main_layout.addLayout(self.button_layout)
        self.setModal(True)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.info_label.setText(_("An unexpected error has occurred"))
        self.quit_button.setText(_("Quit"))
        self.send_log.setText(_("Send session log"))
        self.save_button.setText(_("Save route"))
