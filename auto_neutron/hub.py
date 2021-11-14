# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import atexit
import csv
import typing as t
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.constants import ROUTE_FILE_NAME, get_config_dir
from auto_neutron.game_state import GameState, PlotterState
from auto_neutron.route_plots import AhkPlotter, CopyPlotter, NeutronPlotRow
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.windows.error_window import ErrorWindow
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
        self.error_window = ErrorWindow(self.window)
        exception_handler.triggered.connect(self.error_window.show)
        self.window.show()

        self.window.about_action.triggered.connect(partial(LicenseWindow, self.window))
        self.window.new_route_action.triggered.connect(self.new_route_window)
        self.window.settings_action.triggered.connect(self.display_settings)
        self.window.save_action.triggered.connect(self.save_route)
        self.window.table.doubleClicked.connect(self.get_index_row)
        self.game_state = GameState()

        self.plotter_state = PlotterState(self.game_state)
        self.plotter_state.new_system_signal.connect(self.new_system_callback)

        self.apply_settings()

        self.edit_route_update_connection = ReconnectingSignal(
            self.window.table.itemChanged, self.update_route_from_edit
        )
        self.edit_route_update_connection.connect()

        atexit.register(self.save_route)

    def new_route_window(self) -> None:
        """Display the `NewRouteWindow` and connect its signals."""
        route_window = NewRouteWindow(self.window, self.game_state)
        route_window.route_created_signal.connect(self.new_route)

    def update_route_from_edit(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Edit the plotter's route with the new data in `table_item`."""
        self.plotter_state.route[table_item.row()][
            table_item.column()
        ] = table_item.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if table_item.row() == self.plotter_state.route_index:
            self.plotter_state.route_index = self.plotter_state.route_index

    def new_system_callback(self, _: t.Any, index: int) -> None:
        """Ensure we don't edit the route when inactivating rows."""
        with self.edit_route_update_connection.temporarily_disconnect():
            self.window.set_current_row(index)

    def get_index_row(self, index: QtCore.QModelIndex) -> None:
        """Set the current route index to `index`'s row."""
        self.plotter_state.route_index = index.row()

    def new_route(self, journal: Journal, route: RouteList, route_index: int) -> None:
        """Create a new worker with `route`, populate the main table with it, and set the route index."""
        self.plotter_state.journal = journal
        self.plotter_state.create_worker_with_route(route)
        if self.plotter_state.plotter is None:
            if settings.General.copy_mode:
                self.plotter_state.plotter = CopyPlotter()
            else:
                self.plotter_state.plotter = AhkPlotter()
        with self.edit_route_update_connection.temporarily_disconnect():
            self.window.initialize_table(route)
        self.plotter_state.route_index = route_index

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

    def save_route(self) -> None:
        """If route auto saving is enabled, save the route to the config directory."""
        if settings.General.save_on_quit and self.plotter_state.route is not None:
            with open(
                get_config_dir() / ROUTE_FILE_NAME, "w", encoding="utf8", newline=""
            ) as out_file:
                route_type = type(self.plotter_state.route[0])
                writer = csv.writer(out_file, quoting=csv.QUOTE_ALL)
                if route_type is NeutronPlotRow:
                    writer.writerow(
                        [
                            "System Name",
                            "Distance To Arrival",
                            "Distance Remaining",
                            "Neutron Star",
                            "Jumps",
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            "System Name",
                            "Distance",
                            "Distance Remaining",
                            "Fuel Left",
                            "Fuel Used",
                            "Refuel",
                            "Neutron Star",
                        ]
                    )
                writer.writerows(row.to_csv() for row in self.plotter_state.route)

            settings.General.last_route_index = self.plotter_state.route_index


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
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Light,
            QtGui.QColor(0, 0, 0),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Text,
            QtGui.QColor(110, 110, 100),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.ButtonText,
            QtGui.QColor(110, 110, 100),
        )
        p.set_color(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Button,
            QtGui.QColor(50, 50, 50),
        )
    else:
        p = app.style().standard_palette()

    app.set_palette(p)
