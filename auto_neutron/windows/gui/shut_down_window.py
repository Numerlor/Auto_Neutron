# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class ShutDownWindowGUI(QtWidgets.QDialog):
    """Base GUI for the shut down window that notifies the user of the game being shut down."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.info_label = QtWidgets.QLabel("Game shut down", self)
        font = QtGui.QFont()
        font.set_point_size(18)
        self.info_label.font = font

        self.journal_combo = QtWidgets.QComboBox(self)
        self.journal_combo.add_items(
            ["Last journal", "Second to last", "Third to last"]
        )
        self.journal_combo.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.new_journal_button = QtWidgets.QPushButton("New journal", self)
        self.new_journal_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.save_route_button = QtWidgets.QPushButton("Save route", self)
        self.save_route_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.quit_button = QtWidgets.QPushButton("Quit", self)
        self.quit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.add_widget(self.journal_combo)
        self.button_layout.add_widget(self.new_journal_button)
        self.button_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
            )
        )
        self.button_layout.add_widget(
            self.save_route_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.button_layout.add_widget(
            self.quit_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.add_widget(
            self.info_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        self.main_layout.add_layout(self.button_layout)

        self.show()
