# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import atexit
import logging
import typing as t
from functools import partial

import babel
from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

import auto_neutron.locale
from auto_neutron import Theme, settings
from auto_neutron.constants import JOURNAL_PATH, ROUTE_FILE_NAME, get_config_dir
from auto_neutron.dark_theme import set_theme
from auto_neutron.fuel_warn import FuelWarn
from auto_neutron.game_state import PlotterState
from auto_neutron.plotters import AhkPlotter, CopyPlotter
from auto_neutron.route import Route
from auto_neutron.self_updater import Updater
from auto_neutron.settings import delay_sync
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.windows import (
    ErrorWindow,
    LicenseWindow,
    MainWindow,
    MissingJournalWindow,
    NewRouteWindow,
    SettingsWindow,
    ShutDownWindow,
)
from auto_neutron.workers import StatusWorker

if t.TYPE_CHECKING:
    from auto_neutron.journal import Journal
    from auto_neutron.utils.utils import ExceptionHandler
    from auto_neutron.win_theme_change_listener import WinThemeChangeListener

log = logging.getLogger(__name__)


class Hub(QtCore.QObject):
    """Manage windows and communication between them and workers."""

    def __init__(
        self,
        exception_handler: ExceptionHandler,
        theme_listener: WinThemeChangeListener,
    ):
        super().__init__()
        self.window = MainWindow()
        self.error_window = ErrorWindow(self.window)
        self.error_window.save_button.pressed.connect(self.save_route)
        Updater(self.window).check_update()

        exception_handler.triggered.connect(self.error_window.show)
        exception_handler.set_parent(self)

        self._theme_listener = theme_listener
        self._theme_listener.theme_changed.connect(self.set_theme_from_os)
        self._theme_listener.set_parent(self)

        self.window.show()

        self.window.about_action.triggered.connect(self.display_license_window)
        self.window.new_route_action.triggered.connect(self.new_route_window)
        self.window.settings_action.triggered.connect(self.display_settings)
        self.window.save_action.triggered.connect(self.save_route)
        self.window.table.doubleClicked.connect(self.get_index_row)

        self.plotter_state = PlotterState(self)
        self.plotter_state.new_system_signal.connect(self.new_system_callback)
        self.plotter_state.route_end_signal.connect(
            partial(self.new_system_callback, None)
        )
        self.plotter_state.shut_down_signal.connect(self.display_shut_down_window)

        self.apply_settings()

        self.edit_route_update_connection = ReconnectingSignal(
            self.window.table.itemChanged, self.update_route_from_edit
        )
        self.edit_route_update_connection.connect()

        if (
            not JOURNAL_PATH.exists()
            or not list(JOURNAL_PATH.glob("Journal.*.log"))
            or not (JOURNAL_PATH / "Status.json").exists()
        ):
            # If the journal folder is missing, force the user to quit
            MissingJournalWindow(self.window).show()
            return

        self.fuel_warner = FuelWarn(self, self.window)
        self.warn_worker = StatusWorker(self)
        self.warn_worker.status_signal.connect(self.fuel_warner.warn)

        self.new_route_window()

        atexit.register(self.save_on_exit)

    def new_route_window(self) -> None:
        """Display the `NewRouteWindow` and connect its signals."""
        logging.info("Displaying new route window.")
        route_window = NewRouteWindow(self.window)
        route_window.route_created_signal.connect(self.new_route)
        route_window.show()

    def update_route_from_edit(self, table_item: QtWidgets.QTableWidgetItem) -> None:
        """Edit the plotter's route with the new data in `table_item`."""
        log.debug(
            f"Updating info from edited item at x={table_item.row()} y={table_item.column()}."
        )
        self.plotter_state.route.entries[table_item.row()][
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
        log.debug("Setting route index after user interaction.")
        self.plotter_state.route_index = index.row()

    def new_route(
        self, journal: Journal, route: Route = None, route_index: int = None
    ) -> None:
        """Create a new worker with `route`, populate the main table with it, and set the route index."""
        if route is None:
            logging.debug("Using current plotter route.")
            route = self.plotter_state.route
        if route_index is None:
            logging.debug("Using current plotter index.")
            route_index = self.plotter_state.route_index

        if route_index >= len(route.entries):
            route_index = len(route.entries) - 1

        logging.debug(f"Creating a new route with {route_index=}.")
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
        self.window.scroll_to_index(route_index)
        if journal.location is not None:  # may not have a location yet
            self.plotter_state.tail_worker.emit_next_system(journal.location)
        self.warn_worker.start()
        self.fuel_warner.set_journal(journal)

    def apply_settings(self) -> None:
        """Update the appearance and plotter with new settings."""
        log.debug("Refreshing settings.")
        self.window.table.font = settings.Window.font
        if settings.Window.dark_mode is Theme.OS_THEME:
            dark = self._theme_listener.dark_theme
        else:
            dark = settings.Window.dark_mode is Theme.DARK_THEME
        set_theme(dark)

        if self.plotter_state.plotter is not None:
            current_sys = self.plotter_state.route.current_system
            if settings.General.copy_mode and not isinstance(
                self.plotter_state.plotter, CopyPlotter
            ):
                self.plotter_state.plotter = CopyPlotter(start_system=current_sys)
            elif not settings.General.copy_mode and not isinstance(
                self.plotter_state.plotter, AhkPlotter
            ):
                self.plotter_state.plotter = AhkPlotter(start_system=current_sys)
            else:
                self.plotter_state.plotter.refresh_settings()

        new_locale = babel.Locale.parse(settings.General.locale)
        if new_locale != auto_neutron.locale.get_active_locale():
            auto_neutron.locale.set_active_locale(new_locale)
            app = QtWidgets.QApplication.instance()
            app.post_event(app, QtCore.QEvent(QtCore.QEvent.LanguageChange))

    def display_settings(self) -> None:
        """Display the settings window and connect the applied signal to refresh appearance."""
        log.info("Displaying settings window.")
        window = SettingsWindow(self.window)
        window.settings_applied.connect(self.apply_settings)
        window.show()

    def display_shut_down_window(self) -> None:
        """Display the shut down window and connect it to create a new route and save the current one."""
        log.info("Displaying shut down window.")
        window = ShutDownWindow(self.window)
        window.new_journal_signal.connect(self.new_route)
        window.save_route_button.pressed.connect(self.save_route)
        window.show()

    def display_license_window(self) -> None:
        """Display the license window."""
        log.info("Displaying license window.")
        window = LicenseWindow(self.window)
        window.show()

    def set_theme_from_os(self, dark: bool) -> None:
        """Set the current theme to the OS' theme, if the theme setting is set to follow the OS."""
        if settings.Window.dark_mode is Theme.OS_THEME:
            set_theme(dark)

    def save_on_exit(self) -> None:
        """Save necessary settings when exiting."""
        with delay_sync():
            settings.Window.geometry = self.window.save_geometry()
            if settings.General.save_on_quit:
                self.save_route()

    def save_route(self) -> None:
        """If route auto saving is enabled, or force is True, save the route to the config directory."""
        if self.plotter_state.route is not None:
            log.info("Saving route.")
            self.plotter_state.route.to_csv_file(get_config_dir() / ROUTE_FILE_NAME)
            settings.General.last_route_index = self.plotter_state.route_index
