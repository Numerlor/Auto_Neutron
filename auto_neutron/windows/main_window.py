# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import dataclasses
import time
import typing as t

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.utils.signal import ReconnectingSignal

from ..utils.utils import get_application
from .gui.main_window import MainWindowGUI
from .route_table_header import RouteTableHeader, header_from_row_type

if t.TYPE_CHECKING:
    import collections.abc

    from auto_neutron.route import Route


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

        self.table.vertical_scroll_bar().install_event_filter(self)
        self._last_scroll_time = float("-inf")

        self._route: Route | None = None
        self._header_type: RouteTableHeader | None = None

        self.restore_window()
        self.retranslate()

        self._current_row_index = 0

    @QtCore.Slot()
    def copy_table_item_text(self) -> None:
        """Copy the text of the selected table item into the clipboard."""
        if (item := self.table.current_item()) is not None:
            get_application().clipboard().set_text(item.text())

    def mass_insert(
        self, data: collections.abc.Iterable[collections.abc.Iterable[t.Any]]
    ) -> None:
        """Insert a rows from `data`, then resize columns and rows to contents."""
        with self.resize_connection.temporarily_disconnect():
            for row in data:
                self.insert_row(row)
        self.table.resize_columns_to_contents()
        self.table.resize_rows_to_contents()

    def initialize_table(self, route: Route) -> None:
        """Clear the table and insert plot rows from `Route` into it with appropriate columns."""
        self._route = route

        self.table.clear()
        self.table.row_count = 0

        self._header_type = header = header_from_row_type(route.row_type)(self.table)
        header.initialize_headers()
        header.retranslate_headers()

        self.mass_insert(dataclasses.astuple(row) for row in route.entries)
        self.update_remaining_count()

    def set_current_row(self, index: int) -> None:
        """Change the item colours before `index` to appear inactive and update the remaining systems/jump."""
        with self.resize_connection.temporarily_disconnect():
            super().inactivate_before_index(index)
            self.update_remaining_count()

        if settings.Window.autoscroll and time.monotonic() - self._last_scroll_time > 1:
            self.scroll_to_index(index)

        self._current_row_index = index

    def update_remaining_count(self) -> None:
        """
        Update the count of remaining jumps in the header.

        For exact plot routes the count is displayed next to the system name header,
        for neutron plot routes it's in the jump header.
        """
        with self.resize_connection.temporarily_disconnect():
            self._header_type.set_jumps(
                remaining=self._route.remaining_jumps, total=self._route.total_jumps
            )
            self._header_type.format_jump_header()

    @QtCore.Slot(QtWidgets.QTableWidgetItem)
    def manage_item_changed(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Update the column sizes and information when an item is changed."""
        self._header_type.item_changed(table_item)

    def restore_window(self) -> None:
        """Restore the size and position from the settings."""
        self.restore_geometry(settings.Window.geometry)

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslate()

    def event_filter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Set the last scrolled time on table scroll events."""
        if (
            watched is self.table.vertical_scroll_bar()
            and event.__class__ is QtGui.QWheelEvent
        ):
            self._last_scroll_time = time.monotonic()
        return False

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        if self._header_type is not None:
            self._header_type.retranslate_headers()
