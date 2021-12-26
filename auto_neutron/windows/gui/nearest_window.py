# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class NearestWindowGUI(QtWidgets.QDialog):
    """
    Provide a GUI for the Spansh nearest API.

    Users can directly interact with the search, to_destination and to_source buttons.
    """

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.io_grid_layout = QtWidgets.QGridLayout()

        self.system_name_label = QtWidgets.QLabel("System name", self)
        self.system_name_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.system_name_result_label = QtWidgets.QLabel(self)
        self.system_name_result_label.text_interaction_flags = (
            QtCore.Qt.TextSelectableByMouse
        )
        self.system_name_result_label.cursor = QtCore.Qt.CursorShape.IBeamCursor

        self.distance_label = QtWidgets.QLabel("Distance", self)
        self.distance_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.distance_result_label = QtWidgets.QLabel(self)

        self.x_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.x_label = QtWidgets.QLabel("X", self)
        self.x_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.x_result_label = QtWidgets.QLabel(self)

        self.y_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.y_label = QtWidgets.QLabel("Y", self)
        self.y_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.y_result_label = QtWidgets.QLabel(self)

        self.z_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.z_label = QtWidgets.QLabel("Z", self)
        self.z_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.z_result_label = QtWidgets.QLabel(self)

        for spinbox in (self.x_spinbox, self.y_spinbox, self.z_spinbox):
            spinbox.minimum = -100000
            spinbox.maximum = 100000
            spinbox.button_symbols = QtWidgets.QAbstractSpinBox.NoButtons
            spinbox.size_policy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )

        self.from_location_button = QtWidgets.QPushButton("From location", self)
        self.from_location_button.tool_tip = (
            "Copy coordinates from the current location"
        )

        self.from_target_button = QtWidgets.QPushButton("From target", self)
        self.from_target_button.tool_tip = (
            "Copy approximate coordinates from the current target"
        )

        self.copy_to_source_button = QtWidgets.QPushButton("To source", self)
        self.copy_to_source_button.tool_tip = (
            "Copy searched system name to the source input"
        )

        self.copy_to_destination_button = QtWidgets.QPushButton("To destination", self)
        self.copy_to_source_button.tool_tip = (
            "Copy searched system name to the destination input"
        )

        self.search_button = QtWidgets.QPushButton("Search", self)

        self.io_grid_layout.add_widget(self.system_name_label, 0, 0)
        self.io_grid_layout.add_widget(self.system_name_result_label, 0, 2)

        self.io_grid_layout.add_widget(self.distance_label, 1, 0)
        self.io_grid_layout.add_widget(self.distance_result_label, 1, 2)

        self.io_grid_layout.add_widget(self.x_spinbox, 2, 0)
        self.io_grid_layout.add_widget(self.x_label, 2, 1)
        self.io_grid_layout.add_widget(self.x_result_label, 2, 2)

        self.io_grid_layout.add_widget(self.y_spinbox, 3, 0)
        self.io_grid_layout.add_widget(self.y_label, 3, 1)
        self.io_grid_layout.add_widget(self.y_result_label, 3, 2)

        self.io_grid_layout.add_widget(self.z_spinbox, 4, 0)
        self.io_grid_layout.add_widget(self.z_label, 4, 1)
        self.io_grid_layout.add_widget(self.z_result_label, 4, 2)

        self.io_grid_layout.add_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            ),
            5,
            0,
        )

        self.button_layout = QtWidgets.QHBoxLayout()
        self.from_buttons_layout = QtWidgets.QVBoxLayout()

        self.from_buttons_layout.add_widget(self.from_location_button)
        self.from_buttons_layout.add_widget(self.from_target_button)

        self.to_buttons_layout = QtWidgets.QVBoxLayout()

        self.to_buttons_layout.add_widget(self.copy_to_source_button)
        self.to_buttons_layout.add_widget(self.copy_to_destination_button)

        self.button_layout.add_layout(self.from_buttons_layout)
        self.button_layout.add_layout(self.to_buttons_layout)
        self.button_layout.add_widget(
            self.search_button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom
        )
        self.main_layout.add_layout(self.io_grid_layout)
        self.main_layout.add_layout(self.button_layout)

        for button in self.find_children(QtWidgets.QPushButton):
            button.auto_default = False

        self.show()
