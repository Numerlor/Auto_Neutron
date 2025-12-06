# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

from PySide6 import QtCore, QtGui, QtWidgets

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
        self.setCentralWidget(self.table)

        self._setup_table()

        self.change_action = QtGui.QAction(self)
        self.save_action = QtGui.QAction(self)
        self.copy_action = QtGui.QAction(self)
        self.new_route_action = QtGui.QAction(self)
        self.settings_action = QtGui.QAction(self)
        self.about_action = QtGui.QAction(self)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._main_context)
        self.table.customContextMenuRequested.connect(self._table_context)

    def _setup_table(self) -> None:
        self.table.verticalHeader().setVisible(False)

        self.table.setGridStyle(QtCore.Qt.PenStyle.NoPen)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        palette = QtGui.QPalette()
        palette.setColor(
            QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(255, 255, 255, 0)
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(0, 123, 255)
        )
        self.table.setPalette(palette)

    def inactivate_before_index(self, index: int) -> None:
        """Make all the items before `index` grey, and after, the default color."""
        assert index <= self.table.rowCount(), f"Index {index} out of range."
        grey_color = QtGui.QColor(150, 150, 150)
        for row in range(0, index):
            for column in range(0, self.table.columnCount()):
                self.table.item(row, column).setForeground(grey_color)
        default_brush = QtGui.QBrush()
        for row in range(index, self.table.rowCount()):
            for column in range(0, self.table.columnCount()):
                self.table.item(row, column).setForeground(default_brush)

    @QtCore.Slot(QtCore.QPoint)
    def _main_context(self, location: QtCore.QPoint) -> None:
        """Provide the context menu displayed on the window."""
        menu = QtWidgets.QMenu()
        menu.addAction(self.new_route_action)
        menu.addSeparator()
        menu.addAction(self.save_action)
        menu.addSeparator()
        menu.addAction(self.settings_action)
        menu.addAction(self.about_action)
        menu.exec(self.mapToGlobal(location))

    @QtCore.Slot(QtCore.QPoint)
    def _table_context(self, location: QtCore.QPoint) -> None:
        """Provide the context menu displayed on the table."""
        menu = QtWidgets.QMenu()
        menu.addAction(self.copy_action)
        menu.addAction(self.change_action)
        menu.addSeparator()
        menu.addAction(self.save_action)
        menu.addSeparator()
        menu.addAction(self.new_route_action)
        menu.addAction(self.settings_action)
        menu.addAction(self.about_action)
        menu.exec(self.table.viewport().mapToGlobal(location))

    def insert_row(self, data: collections.abc.Iterable[t.Any]) -> None:
        """Create a new row and insert up to column count amount of items from data."""
        row_pos = self.table.rowCount()
        self.table.setRowCount(row_pos + 1)
        for data_item, column in zip(data, range(0, self.table.columnCount())):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.DisplayRole, data_item)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_pos, column, item)

    def scroll_to_index(self, index: int) -> None:
        """Scroll the table to position the row with `index` at the top."""
        self.table.scrollToItem(
            self.table.item(index, 0),
            QtWidgets.QAbstractItemView.ScrollHint.PositionAtTop,
        )

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._set_header_text()
        self.change_action.setText(_("Edit"))
        self.save_action.setText(_("Save route"))
        self.copy_action.setText(_("Copy"))
        self.new_route_action.setText(_("Start a new route"))
        self.settings_action.setText(_("Settings"))
        self.about_action.setText(_("About"))

    def _set_header_text(self) -> None:
        """Set header text on existing headers."""
        if (header := self.table.horizontalHeaderItem(0)) is not None:
            header.setText(_("System name"))
        if (header := self.table.horizontalHeaderItem(1)) is not None:
            header.setText(_("Distance"))
        if (header := self.table.horizontalHeaderItem(2)) is not None:
            header.setText(_("Remaining"))
