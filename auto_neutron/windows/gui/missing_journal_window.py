# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class MissingJournalWindowGUI(QtWidgets.QDialog):
    """Display window that forces the user to quit when the journal folder is missing."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.set_modal(True)

        self.info_label = QtWidgets.QLabel(
            "Journal folder not found or missing files.", self
        )
        font = QtGui.QFont()
        font.set_point_size(18)
        self.info_label.font = font

        self.quit_button = QtWidgets.QPushButton("Quit", self)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.add_widget(
            self.info_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        self.main_layout.add_widget(
            self.quit_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.set_window_flag(QtCore.Qt.WindowCloseButtonHint, False)
        self.show()
