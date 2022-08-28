# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.constants import VERSION


class LicenseWindowGUI(QtWidgets.QDialog):
    """Window for license information."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.set_fixed_size(600, 500)
        self.set_window_flag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.window_title = "Auto_Neutron " + VERSION

        self.about_qt_button = QtWidgets.QPushButton(self)
        self.about_qt_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.text = QtWidgets.QTextBrowser(self)
        self.text.open_external_links = True

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.add_widget(self.text)

        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.add_widget(self.back_button)

        self.bottom_layout.add_widget(
            self.about_qt_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.main_layout.add_layout(self.bottom_layout)

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.text.clear()
        self.about_qt_button.text = _("About Qt")
        self.back_button.text = _("Back")
