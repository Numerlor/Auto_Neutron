# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
import dataclasses
import typing as t

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.route_plots import ExactPlotRow, NeutronPlotRow, RouteList
from auto_neutron.utils.utils import partial_no_external

from .gui.main_window import MainWindowGUI


class MainWindow(MainWindowGUI):
    """Wrap the GUI and add functional behaviour to it."""

    def __init__(self):
        super().__init__()
        self.change_action.triggered.connect(
            lambda: self.table.edit_item(self.table.current_item())
        )
        self.copy_action.triggered.connect(self.copy_table_item_text)
        self.conn = self.table.itemChanged.connect(
            partial_no_external(self.table.resize_column_to_contents, 0)
        )
        self._current_route_type: t.Optional[
            t.Union[type[ExactPlotRow], type[NeutronPlotRow]]
        ] = None

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
        self.disconnect(self.conn)
        for row in data:
            self.insert_row(row)
        self.table.resize_column_to_contents(0)
        self.table.resize_rows_to_contents()
        self.conn = self.table.itemChanged.connect(
            partial_no_external(self.table.resize_column_to_contents, 0)
        )

    def initialize_table(self, route: RouteList) -> None:
        """Clear the table and insert plot rows from `RouteList` into it with appropriate columns."""
        self.table.clear_contents()
        self._current_route_type = type(route[0])

        if self._current_route_type is ExactPlotRow:
            self.table.set_item_delegate_for_column(3, self._checkbox_delegate)
            self.table.resize_column_to_contents(3)
            self.table.resize_column_to_contents(4)
            self.table.column_count = 5

        elif self._current_route_type is NeutronPlotRow:
            self.table.set_item_delegate_for_column(3, self._spinbox_delegate)
            self.table.column_count = 4
            self.table.resize_column_to_contents(4)

        self._create_base_headers()
        self.mass_insert(dataclasses.astuple(row) for row in route)

        if self._current_route_type is ExactPlotRow:
            self.table.horizontal_header_item(3).set_text("Scoopable")
            self.table.horizontal_header_item(4).set_text("Neutron")

            self.table.resize_column_to_contents(3)
            self.table.resize_column_to_contents(4)

        elif self._current_route_type is NeutronPlotRow:
            self.table.horizontal_header_item(3).set_text("Jumps")
            self.table.resize_column_to_contents(3)
