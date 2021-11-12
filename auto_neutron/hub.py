# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.game_state import GameState, PlotterState
from auto_neutron.route_plots import AhkPlotter, CopyPlotter
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.windows.gui.license_window import LicenseWindow
from auto_neutron.windows.main_window import MainWindow
from auto_neutron.windows.new_route_window import NewRouteWindow
from auto_neutron.windows.settings_window import SettingsWindow

if t.TYPE_CHECKING:
    from auto_neutron.journal import Journal
    from auto_neutron.route_plots import RouteList
    from auto_neutron.utils.utils import ExceptionHandler


class Hub(QtCore.QObject):
    """Manage windows and communication between them and workers."""

    def __init__(self, exception_handler: ExceptionHandler):
        super().__init__()
        self.window = MainWindow()
        self.window.show()
        self.window.about_action.triggered.connect(partial(LicenseWindow, self.window))
        self.window.new_route_action.triggered.connect(self.new_route_window)
        self.window.settings_action.triggered.connect(self.display_settings)
        self.window.table.doubleClicked.connect(self.get_index_row)
        self.game_state = GameState()

        self.plotter_state = PlotterState(self.game_state)
        self.plotter_state.new_system_signal.connect(self.new_system_callback)

        self.apply_settings()

        self.edit_route_update_connection = ReconnectingSignal(
            self.window.table.itemChanged, self.update_route_from_edit
        )
        self.edit_route_update_connection.connect()

    def new_route_window(self) -> None:
        """Display the `NewRouteWindow` and connect its signals."""
        route_window = NewRouteWindow(self.window, self.game_state)
        route_window.route_created_signal.connect(self.new_route)

    def update_route_from_edit(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Edit the plotter's route with the new data in `table_item`."""
        self.plotter_state.route[table_item.row()][
            table_item.column()
        ] = table_item.data(QtCore.Qt.ItemDataRole.DisplayRole)

    def new_system_callback(self, _: t.Any, index: int) -> None:
        """Ensure we don't edit the route when inactivating rows."""
        with self.edit_route_update_connection.temporarily_disconnect():
            self.window.inactivate_before_index(index)

    def get_index_row(self, index: QtCore.QModelIndex) -> None:
        """Set the current route index to `index`'s row."""
        self.plotter_state.route_index = index.row()

    def new_route(self, journal: Journal, route: RouteList) -> None:
        """Create a new worker with `route` and populate the main table with it."""
        self.plotter_state.journal = journal
        self.plotter_state.create_worker_with_route(route)
        if self.plotter_state.plotter is None:
            if settings.General.copy_mode:
                self.plotter_state.plotter = CopyPlotter(start_system=route[0].system)
            else:
                self.plotter_state.plotter = AhkPlotter(start_system=route[0].system)
        with self.edit_route_update_connection.temporarily_disconnect():
            self.window.initialize_table(route)

    def apply_settings(self) -> None:
        """Update the appearance and plotter with new settings."""
        self.window.table.font = settings.Window.font
        set_theme()

        if self.plotter_state.plotter is not None:
            current_sys = self.plotter_state.route[self.plotter_state.route_index]
            if settings.General.copy_mode and not isinstance(
                self.plotter_state.plotter, CopyPlotter
            ):
                self.plotter_state.plotter = CopyPlotter(
                    start_system=current_sys.system
                )
            elif not settings.General.copy_mode and not isinstance(
                self.plotter_state.plotter, AhkPlotter
            ):
                self.plotter_state.plotter = AhkPlotter(start_system=current_sys.system)

    def display_settings(self) -> None:
        """Display the settings window and connect the applied signal to refresh appearance."""
        window = SettingsWindow(self.window)
        window.settings_applied.connect(self.apply_settings)


def set_theme() -> None:
    """Set the app's theme depending on the user's preferences."""
    app = QtWidgets.QApplication.instance()

    if settings.Window.dark_mode:
        p = QtGui.QPalette()
        p.set_color(QtGui.QPalette.Window, QtGui.QColor(35, 35, 35))
        p.set_color(QtGui.QPalette.WindowText, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        p.set_color(QtGui.QPalette.Text, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Button, QtGui.QColor(60, 60, 60))
        p.set_color(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
        p.set_color(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        p.set_color(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        p.set_color(QtGui.QPalette.PlaceholderText, QtGui.QColor(110, 110, 100))
        p.set_color(
            QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(0, 0, 0)
        )
        p.set_color(
            QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(110, 110, 100)
        )
    else:
        p = app.style().standard_palette()
    p.set_color(QtGui.QPalette.Highlight, QtGui.QColor(255, 255, 255, 0))
    p.set_color(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 123, 255))
    app.set_palette(p)
