# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class MissingJournalWindowGUI(QtWidgets.QDialog):
    """Display window that forces the user to quit when the journal folder is missing."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setModal(True)

        self.info_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.info_label.setFont(font)

        self.quit_button = QtWidgets.QPushButton(self)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(
            self.info_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        self.main_layout.addWidget(
            self.quit_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.info_label.setText(_("Journal folder not found or missing files."))
        self.quit_button.setText(_("Quit"))
