# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import dataclasses
import typing as t

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.route import ExactPlotRow, NeutronPlotRow, Route
from auto_neutron.utils.signal import ReconnectingSignal

from .gui.main_window import MainWindowGUI

if t.TYPE_CHECKING:
    import collections.abc


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

        self._route: Route | None = None

        self.restore_window()
        self.retranslate()

        self._current_row_index = 0

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

    def initialize_table(self, route: Route) -> None:
        """Clear the table and insert plot rows from `Route` into it with appropriate columns."""
        self._route = route

        self.table.clear()
        self.table.row_count = 0

        self._create_base_headers()
        self._set_header_text()
        self.mass_insert(dataclasses.astuple(row) for row in route.entries)

        if route.row_type is ExactPlotRow:
            self.table.set_item_delegate_for_column(3, self._checkbox_delegate)
            self.table.resize_column_to_contents(3)
            self.table.resize_column_to_contents(4)

        elif route.row_type is NeutronPlotRow:
            self.table.column_count = 4  # reset column count to 4 to hide last col
            self.table.set_item_delegate_for_column(3, self._spinbox_delegate)
            self.table.resize_column_to_contents(3)

    def set_current_row(self, index: int) -> None:
        """Change the item colours before `index` to appear inactive and update the remaining systems/jump."""
        with self.resize_connection.temporarily_disconnect():
            super().inactivate_before_index(index)
            self.update_remaining_count()
        top_item = self.table.item_at(QtCore.QPoint(1, 1))
        if settings.Window.autoscroll and top_item.row() == self._current_row_index:
            self.scroll_to_index(index)

        self._current_row_index = index

    def update_remaining_count(self) -> None:
        """
        Update the count of remaining jumps in the header.

        For exact plot routes the count is displayed next to the system name header,
        for neutron plot routes it's in the jump header.
        """
        with self.resize_connection.temporarily_disconnect():
            if self._route.row_type is ExactPlotRow:
                self.table.horizontal_header_item(0).set_text(
                    # NOTE: made jumps/ total
                    _("System name ({}/{})").format(
                        self._route.remaining_jumps, self._route.total_jumps
                    )
                )
            else:
                self.table.horizontal_header_item(3).set_text(
                    # NOTE: made jumps/ total
                    _("Jumps {}/{}").format(
                        self._route.remaining_jumps, self._route.total_jumps
                    )
                )
        self.table.resize_column_to_contents(3)

    def manage_item_changed(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Update the column sizes and information when an item is changed."""
        if table_item.column() == 0:
            self.table.resize_column_to_contents(0)
        elif self._route.row_type is NeutronPlotRow and table_item.column() == 3:
            self.update_remaining_count()

    def restore_window(self) -> None:
        """Restore the size and position from the settings."""
        self.restore_geometry(settings.Window.geometry)

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self._set_header_text()
        if self._route is not None:
            self.update_remaining_count()

    def _set_header_text(self) -> None:
        """Set the text for the headers."""
        super()._set_header_text()
        if self._route is not None and self._route.row_type is ExactPlotRow:
            if (header := self.table.horizontal_header_item(3)) is not None:
                header.set_text(_("Scoopable"))
            if (header := self.table.horizontal_header_item(4)) is not None:
                header.set_text(_("Neutron"))
        else:
            if (header := self.table.horizontal_header_item(3)) is not None:
                header.set_text(_("Jumps"))
