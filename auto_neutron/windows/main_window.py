# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
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

    def copy_table_item_text(self) -> None:
        """Copy the text of the selected table item into the clipboard."""
        if (item := self.table.current_item()) is not None:
            QtWidgets.QApplication.instance().clipboard().set_text(item.text())

    def mass_insert(self, data: list[list[t.Any]]) -> None:
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
