# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from auto_neutron.constants import VERSION


class LicenseWindowGUI(QtWidgets.QDialog):
    """Window for license information."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(600, 500)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle("Auto_Neutron " + VERSION)

        self.about_qt_button = QtWidgets.QPushButton(self)
        self.about_qt_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self.text = QtWidgets.QTextBrowser(self)
        self.text.setOpenExternalLinks(True)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.text)

        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.addWidget(self.back_button)

        self.bottom_layout.addWidget(
            self.about_qt_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.main_layout.addLayout(self.bottom_layout)

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.text.clear()
        self.about_qt_button.setText(_("About Qt"))
        self.back_button.setText(_("Back"))
