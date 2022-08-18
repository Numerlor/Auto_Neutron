# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from .delegates import CheckBoxDelegate, DoubleSpinBoxDelegate, SpinBoxDelegate

if t.TYPE_CHECKING:
    import collections.abc


class MainWindowGUI(QtWidgets.QMainWindow):
    """Provide the main window GUI containing a table."""

    def __init__(self):
        super().__init__()
        self.table = QtWidgets.QTableWidget(self)
        self._double_spinbox_delegate = DoubleSpinBoxDelegate()
        self._spinbox_delegate = SpinBoxDelegate()
        self._checkbox_delegate = CheckBoxDelegate()
        self.set_central_widget(self.table)

        self._setup_table()

        self.change_action = QtGui.QAction(self)
        self.save_action = QtGui.QAction(self)
        self.copy_action = QtGui.QAction(self)
        self.new_route_action = QtGui.QAction(self)
        self.settings_action = QtGui.QAction(self)
        self.about_action = QtGui.QAction(self)

        self.context_menu_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        self.table.context_menu_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        self.customContextMenuRequested.connect(self._main_context)
        self.table.customContextMenuRequested.connect(self._table_context)

    def _setup_table(self) -> None:
        self.table.vertical_header().visible = False

        self.table.grid_style = QtCore.Qt.PenStyle.NoPen
        self.table.selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        self.table.edit_triggers = QtWidgets.QAbstractItemView.NoEditTriggers
        self.table.alternating_row_colors = True
        self.table.horizontal_scroll_bar_policy = (
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        palette = QtGui.QPalette()
        palette.set_color(QtGui.QPalette.Highlight, QtGui.QColor(255, 255, 255, 0))
        palette.set_color(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 123, 255))
        self.table.palette = palette

    def inactivate_before_index(self, index: int) -> None:
        """Make all the items before `index` grey, and after, the default color."""
        assert index <= self.table.row_count, f"Index {index} out of range."
        grey_color = QtGui.QColor(150, 150, 150)
        for row in range(0, index):
            for column in range(0, self.table.column_count):
                self.table.item(row, column).set_foreground(grey_color)
        default_brush = QtGui.QBrush()
        for row in range(index, self.table.row_count):
            for column in range(0, self.table.column_count):
                self.table.item(row, column).set_foreground(default_brush)

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

    def insert_row(self, data: collections.abc.Iterable[t.Any]) -> None:
        """Create a new row and insert up to column count amount of items from data."""
        row_pos = self.table.row_count
        self.table.row_count = row_pos + 1
        for data_item, column in zip(data, range(0, self.table.column_count)):
            item = QtWidgets.QTableWidgetItem()
            item.set_data(QtCore.Qt.ItemDataRole.DisplayRole, data_item)
            item.set_text_alignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.set_item(row_pos, column, item)

    def scroll_to_index(self, index: int) -> None:
        """Scroll the table to position the row with `index` at the top."""
        self.table.scroll_to_item(
            self.table.item(index, 0), QtWidgets.QAbstractItemView.PositionAtTop
        )

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._set_header_text()
        self.change_action.text = _("Edit")
        self.save_action.text = _("Save route")
        self.copy_action.text = _("Copy")
        self.new_route_action.text = _("Start a new route")
        self.settings_action.text = _("Settings")
        self.about_action.text = _("About")

    def _set_header_text(self) -> None:
        """Set header text on existing headers."""
        if (header := self.table.horizontal_header_item(0)) is not None:
            header.set_text(_("System name"))
        if (header := self.table.horizontal_header_item(1)) is not None:
            header.set_text(_("Distance"))
        if (header := self.table.horizontal_header_item(2)) is not None:
            header.set_text(_("Remaining"))
