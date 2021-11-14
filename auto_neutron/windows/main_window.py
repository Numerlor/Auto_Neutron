# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import atexit
import collections.abc
import dataclasses
import typing as t

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.route_plots import ExactPlotRow, NeutronPlotRow, RouteList
from auto_neutron.utils.signal import ReconnectingSignal

from .gui.main_window import MainWindowGUI


class MainWindow(MainWindowGUI):
    """Wrap the GUI and add functional behaviour to it."""

    def __init__(self):
        super().__init__()
        self.change_action.triggered.connect(
            lambda: self.table.edit_item(self.table.current_item())
        )
        self.copy_action.triggered.connect(self.copy_table_item_text)
        self.resize_connection = ReconnectingSignal(
            self.table.itemChanged,
            self.manage_item_changed,
        )
        self.resize_connection.connect()

        self._current_route_type: t.Optional[
            t.Union[type[ExactPlotRow], type[NeutronPlotRow]]
        ] = None

        atexit.register(self.save_window)
        self.restore_window()

    def copy_table_item_text(self) -> None:
        """Copy the text of the selected table item into the clipboard."""
        if (item := self.table.current_item()) is not None:
            QtWidgets.QApplication.instance().clipboard().set_text(item.text())

    def mass_insert(
        self, data: collections.abc.Iterable[collections.abc.Iterable[t.Any]]
    ) -> None:
        """
        Insert a large amount of rows.

        The `self.conn` itemChanged signal is temporarily disconnected to accommodate this.
        """
        with self.resize_connection.temporarily_disconnect():
            for row in data:
                self.insert_row(row)
            self.table.resize_column_to_contents(0)
            self.table.resize_rows_to_contents()

    def initialize_table(self, route: RouteList) -> None:
        """Clear the table and insert plot rows from `RouteList` into it with appropriate columns."""
        self.table.clear()
        self.table.row_count = 0
        self._current_route_type = type(route[0])

        self._create_base_headers()

        self.mass_insert(dataclasses.astuple(row) for row in route)

        if self._current_route_type is ExactPlotRow:
            self.table.set_item_delegate_for_column(3, self._checkbox_delegate)
            self.table.horizontal_header_item(3).set_text("Scoopable")
            self.table.horizontal_header_item(4).set_text("Neutron")

            self.table.resize_column_to_contents(3)
            self.table.resize_column_to_contents(4)

        elif self._current_route_type is NeutronPlotRow:
            self.table.column_count = 4  # reset column count to 4 to hide last col
            self.table.set_item_delegate_for_column(3, self._spinbox_delegate)
            self.table.horizontal_header_item(3).set_text("Jumps")
            self.table.resize_column_to_contents(3)

    def set_current_row(self, index: int) -> None:
        """Change the item colours before `index` to appear inactive and update the remaining systems/jump."""
        with self.resize_connection.temporarily_disconnect():
            super().inactivate_before_index(index)
            self.update_remaining_count(index)
        top_item = self.table.item_at(QtCore.QPoint(1, 1))
        if settings.Window.autoscroll and top_item.row() == index - 1:
            self.table.scroll_to_item(
                self.table.item(index, 0), QtWidgets.QAbstractItemView.PositionAtTop
            )

    def update_remaining_count(self, index: int) -> None:
        """
        Update the count of remaining jumps in the header.

        For exact plot routes the count is displayed next to the system name header,
        for neutron plot routes it's in the jump header.
        """
        with self.resize_connection.temporarily_disconnect():
            if self._current_route_type is ExactPlotRow:
                self.table.horizontal_header_item(0).set_text(
                    f"System name ({index+1}/{self.table.row_count})"
                )
            else:
                total_jumps = sum(
                    self.table.item(row, 3).data(QtCore.Qt.ItemDataRole.DisplayRole)
                    for row in range(self.table.row_count)
                )
                remaining_jumps = sum(
                    self.table.item(row, 3).data(QtCore.Qt.ItemDataRole.DisplayRole)
                    for row in range(index, self.table.row_count)
                )
                self.table.horizontal_header_item(3).set_text(
                    f"Jumps {remaining_jumps}/{total_jumps}"
                )
        self.table.resize_column_to_contents(0)
        self.table.resize_column_to_contents(3)

    def manage_item_changed(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Update the column sizes and information when an item is changed."""
        if table_item.column() == 0:
            self.table.resize_column_to_contents(0)
        elif self._current_route_type is NeutronPlotRow and table_item.column() == 3:
            self.update_remaining_count(table_item.row())

    def restore_window(self) -> None:
        """Restore the size and position from the settings."""
        self.restore_geometry(settings.Window.geometry)

    def save_window(self) -> None:
        """Save size and position to settings."""
        settings.Window.geometry = self.save_geometry()
