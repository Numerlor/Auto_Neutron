# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.delegates import DoubleSpinBoxDelegate, SpinBoxDelegate


class MainWindowGUI(QtWidgets.QMainWindow):
    """Provide the main window GUI containing a table."""

    def __init__(self):
        super().__init__()
        self.table = QtWidgets.QTableWidget()
        self._double_spinbox_delegate = DoubleSpinBoxDelegate()
        self._spinbox_delegate = SpinBoxDelegate()
        self.set_central_widget(self.table)

        self._setup_table()

        self.change_action = QtGui.QAction("Edit", self)
        self.save_action = QtGui.QAction("Save route", self)
        self.copy_action = QtGui.QAction("Copy", self)
        self.new_route_action = QtGui.QAction("Start a new route", self)
        self.settings_action = QtGui.QAction("Settings", self)
        self.about_action = QtGui.QAction("About", self)

        self.context_menu_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        self.table.context_menu_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        self.customContextMenuRequested.connect(self._main_context)
        self.table.customContextMenuRequested.connect(self._table_context)

    def _setup_table(self) -> None:
        self.table.column_count = 4
        self.table.vertical_header().visible = False

        self.table.grid_style = QtCore.Qt.PenStyle.NoPen
        self.table.selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        self.table.edit_triggers = QtWidgets.QAbstractItemView.NoEditTriggers
        self.table.alternating_row_colors = True

        for column in range(4):
            self.table.set_horizontal_header_item(column, QtWidgets.QTableWidgetItem())

        horizontal_header = self.table.horizontal_header()
        horizontal_header.set_section_resize_mode(1, QtWidgets.QHeaderView.Stretch)
        horizontal_header.set_section_resize_mode(2, QtWidgets.QHeaderView.Stretch)
        horizontal_header.set_section_resize_mode(3, QtWidgets.QHeaderView.Fixed)
        horizontal_header.highlight_sections = False

        self.table.set_item_delegate_for_column(1, self._double_spinbox_delegate)
        self.table.set_item_delegate_for_column(2, self._double_spinbox_delegate)
        self.table.set_item_delegate_for_column(3, self._spinbox_delegate)

    def inactivate_before_index(self, index: int) -> None:
        """Make all the items before `index` grey, and after, the default color."""
        assert index < self.table.row_count, f"Index {index} out of range."
        for row in range(0, index):
            for column in range(0, self.table.column_count):
                self.table.item(row, column).set_foreground(QtGui.QColor(150, 150, 150))
        for row in range(index, self.table.row_count):
            for column in range(0, self.table.column_count):
                self.table.item(row, column).set_foreground(QtGui.QBrush())

    def _main_context(self, location: QtCore.QPoint) -> None:
        """Provide the context menu displayed on the window."""
        menu = QtWidgets.QMenu()
        menu.add_action(self.new_route_action)
        menu.add_separator()
        menu.add_action(self.save_action)
        menu.add_separator()
        menu.add_action(self.settings_action)
        menu.add_action(self.about_action)
        menu.exec(self.map_to_global(location))

    def _table_context(self, location: QtCore.QPoint) -> None:
        """Provide the context menu displayed on the table."""
        menu = QtWidgets.QMenu()
        menu.add_action(self.copy_action)
        menu.add_action(self.change_action)
        menu.add_separator()
        menu.add_action(self.save_action)
        menu.add_separator()
        menu.add_action(self.new_route_action)
        menu.add_action(self.settings_action)
        menu.add_action(self.about_action)
        menu.exec(self.table.viewport().map_to_global(location))

    def insert_row(self, data: list[t.Any]) -> None:
        """Create a new row and insert up to column count amount of items from data."""
        row_pos = self.table.row_count
        self.table.row_count = row_pos + 1
        for data_item, column in zip(data, range(0, self.table.column_count)):
            item = QtWidgets.QTableWidgetItem()
            item.set_data(QtCore.Qt.ItemDataRole.DisplayRole, data_item)
            item.set_text_alignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.set_item(row_pos, column, item)
