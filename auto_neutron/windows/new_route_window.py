# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import contextlib
import csv
import json
import logging
import typing as t
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron import settings
from auto_neutron.constants import (
    JOURNAL_PATH,
    ROUTE_FILE_NAME,
    SPANSH_API_URL,
    get_config_dir,
)
from auto_neutron.hub import GameState
from auto_neutron.journal import Journal
from auto_neutron.route_plots import (
    ExactPlotRow,
    NeutronPlotRow,
    spansh_exact_callback,
    spansh_neutron_callback,
)
from auto_neutron.ship import Ship
from auto_neutron.utils.network import make_network_request
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.utils.utils import create_request_delay_iterator
from auto_neutron.workers import GameWorker

from .gui.new_route_window import NewRouteWindowGUI
from .nearest_window import NearestWindow

if t.TYPE_CHECKING:
    from auto_neutron.game_state import Location
    from auto_neutron.route_plots import RouteList
log = logging.getLogger(__name__)


class NewRouteWindow(NewRouteWindowGUI):
    """The UI for plotting a new route, from CSV, Spansh plotters, or the last saved route."""

    route_created_signal = QtCore.Signal(Journal, list, int)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.game_state: GameState = None  # type: ignore
        self.selected_journal: Journal = None  # type: ignore
        self._journal_worker: GameWorker = None  # type: ignore

        # region spansh tabs init
        self.spansh_neutron_tab.nearest_button.pressed.connect(
            self._display_nearest_window
        )
        self.spansh_exact_tab.nearest_button.pressed.connect(
            self._display_nearest_window
        )

        # Disable submit plot buttons and set them to be enabled when their respective from/to fields are filled
        self.spansh_neutron_tab.submit_button.enabled = False
        self.spansh_exact_tab.submit_button.enabled = False

        self.spansh_neutron_tab.source_edit.textChanged.connect(
            self._set_neutron_submit
        )
        self.spansh_neutron_tab.target_edit.textChanged.connect(
            self._set_neutron_submit
        )

        self.spansh_exact_tab.source_edit.textChanged.connect(self._set_exact_submit)
        self.spansh_exact_tab.target_edit.textChanged.connect(self._set_exact_submit)
        self.spansh_exact_tab.use_clipboard_checkbox.stateChanged.connect(
            self._set_exact_submit
        )

        self.spansh_neutron_tab.range_spin.value = 50  # default to 80% efficiency
        self.spansh_neutron_tab.efficiency_spin.value = 80  # default to 80% efficiency

        self.spansh_neutron_tab.cargo_slider.valueChanged.connect(
            self._recalculate_range
        )
        self.spansh_neutron_tab.submit_button.pressed.connect(self._submit_neutron)
        self.spansh_exact_tab.submit_button.pressed.connect(self._submit_exact)

        # endregion

        # region csv tab init
        self.csv_tab.path_popup_button.pressed.connect(self._path_select_popup)
        self.csv_tab.submit_button.pressed.connect(self._csv_submit)
        if settings.Paths.csv is not None:
            self.csv_tab.path_edit.text = str(settings.Paths.csv)
        # endregion

        self.last_route_tab.submit_button.pressed.connect(self._last_route_submit)

        self.combo_signals = (
            ReconnectingSignal(
                self.csv_tab.journal_combo.currentIndexChanged,
                self._sync_journal_combos,
            ),
            ReconnectingSignal(
                self.spansh_neutron_tab.journal_combo.currentIndexChanged,
                self._sync_journal_combos,
            ),
            ReconnectingSignal(
                self.spansh_exact_tab.journal_combo.currentIndexChanged,
                self._sync_journal_combos,
            ),
            ReconnectingSignal(
                self.last_route_tab.journal_combo.currentIndexChanged,
                self._sync_journal_combos,
            ),
        )
        for signal in self.combo_signals:
            signal.connect()

        self.tab_widget.currentChanged.connect(self._display_saved_route)
        self._route_displayed = False
        self._loaded_route: t.Optional[list[NeutronPlotRow]] = None
        self.retranslate()
        self._change_journal(0)

    # region spansh plotters
    def _submit_neutron(self) -> None:
        """Submit a neutron plotter request to spansh."""
        log.info("Submitting neutron job.")
        make_network_request(
            SPANSH_API_URL + "/route",
            params={
                "efficiency": self.spansh_neutron_tab.efficiency_spin.value,
                "range": self.spansh_neutron_tab.range_spin.value,
                "from": self.spansh_neutron_tab.source_edit.text,
                "to": self.spansh_neutron_tab.target_edit.text,
            },
            finished_callback=partial(
                spansh_neutron_callback,
                error_callback=self._spansh_error_callback,
                delay_iterator=create_request_delay_iterator(),
                result_callback=partial(
                    self.emit_and_close, self.selected_journal, route_index=1
                ),
            ),
        )
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.BusyCursor)

    def _submit_exact(self) -> None:
        """Submit an exact plotter request to spansh."""
        log.info("Submitting exact job.")
        if self.spansh_exact_tab.use_clipboard_checkbox.checked:
            ship = Ship.from_coriolis(
                json.loads(QtWidgets.QApplication.instance().clipboard().text())
            )
        else:
            ship = self.game_state.ship

        make_network_request(
            SPANSH_API_URL + "/generic/route",
            params={
                "source": self.spansh_exact_tab.source_edit.text,
                "destination": self.spansh_exact_tab.target_edit.text,
                "is_supercharged": int(
                    self.spansh_exact_tab.is_supercharged_checkbox.checked
                ),
                "use_supercharge": int(
                    self.spansh_exact_tab.supercarge_checkbox.checked
                ),
                "use_injections": int(
                    self.spansh_exact_tab.fsd_injections_checkbox.checked
                ),
                "exclude_secondary": int(
                    self.spansh_exact_tab.exclude_secondary_checkbox.checked
                ),
                "fuel_power": ship.fsd.size_const,
                "fuel_multiplier": ship.fsd.rating_const / 1000,
                "optimal_mass": ship.fsd.optimal_mass,
                "base_mass": ship.unladen_mass + ship.reserve_size,
                "tank_size": ship.tank_size,
                "internal_tank_size": ship.reserve_size,
                "max_fuel_per_jump": ship.fsd.max_fuel_usage,
                "range_boost": ship.jump_range_boost,
                "cargo": self.spansh_exact_tab.cargo_slider.value,
            },
            finished_callback=partial(
                spansh_exact_callback,
                error_callback=self._spansh_error_callback,
                delay_iterator=create_request_delay_iterator(),
                result_callback=partial(
                    self.emit_and_close, self.selected_journal, route_index=1
                ),
            ),
        )
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.BusyCursor)

    def _set_widget_values(
        self, location: Location, ship: Ship, current_cargo: int
    ) -> None:
        """Update the UI with values from `location`, `ship` and `current_cargo`."""
        if (
            not self.spansh_neutron_tab.source_edit.modified
            or not self.spansh_neutron_tab.source_edit.text
        ):
            self.spansh_neutron_tab.source_edit.text = location.name
        if (
            not self.spansh_exact_tab.source_edit.modified
            or not self.spansh_exact_tab.source_edit.text
        ):
            self.spansh_exact_tab.source_edit.text = location.name

        self.spansh_neutron_tab.cargo_slider.maximum = ship.max_cargo
        self.spansh_neutron_tab.cargo_slider.value = current_cargo

        self.spansh_exact_tab.cargo_slider.value = current_cargo

        self.spansh_neutron_tab.range_spin.value = ship.jump_range(
            cargo_mass=current_cargo
        )

    def _recalculate_range(self, cargo_mass: int) -> None:
        """Recalculate jump range with the new cargo_mass."""
        if self.game_state.ship.initialized:  # Ship may not be available yet
            self.spansh_neutron_tab.range_spin.value = self.game_state.ship.jump_range(
                cargo_mass=cargo_mass
            )

    def _set_neutron_submit(self) -> None:
        """Enable the neutron submit button if both inputs are filled, disable otherwise."""
        self.spansh_neutron_tab.submit_button.enabled = bool(
            self.spansh_neutron_tab.source_edit.text
            and self.spansh_neutron_tab.target_edit.text
            and not self.game_state.shut_down
        )

    def _set_exact_submit(self) -> None:
        """Enable the exact submit button if both inputs are filled, disable otherwise."""
        self.spansh_exact_tab.submit_button.enabled = bool(
            self.spansh_exact_tab.source_edit.text
            and self.spansh_exact_tab.target_edit.text
            and not self.game_state.shut_down
            and (
                self.game_state.ship.initialized
                or self.spansh_exact_tab.use_clipboard_checkbox.checked
            )
        )

    def _display_nearest_window(self) -> None:
        """Display the nearest system finder window and link its signals."""
        log.info("Displaying nearest window.")
        window = NearestWindow(self, self.game_state.location, self.status_bar)
        window.copy_to_source_button.pressed.connect(
            partial(
                self._set_line_edits_from_nearest,
                self.spansh_neutron_tab.source_edit,
                self.spansh_exact_tab.source_edit,
                window=window,
            )
        )
        window.copy_to_source_button.pressed.connect(
            partial(setattr, self.spansh_neutron_tab.source_edit, "modified", True)
        )

        window.copy_to_destination_button.pressed.connect(
            partial(
                self._set_line_edits_from_nearest,
                self.spansh_neutron_tab.target_edit,
                self.spansh_exact_tab.target_edit,
                window=window,
            )
        )
        window.copy_to_destination_button.pressed.connect(
            partial(setattr, self.spansh_neutron_tab.source_edit, "modified", True)
        )
        window.from_target_button.pressed.connect(
            lambda: window.set_input_values_from_location(self.game_state.last_target)
        )
        window.from_location_button.pressed.connect(
            lambda: window.set_input_values_from_location(self.game_state.location)
        )
        window.show()

    def _set_line_edits_from_nearest(
        self, *line_edits: QtWidgets.QLineEdit, window: NearestWindow
    ) -> None:
        """Update the line edits with `system_name_result_label` contents from `window`."""
        for line_edit in line_edits:
            line_edit.text = window.system_name_result_label.text

    def _spansh_error_callback(self, error_message: str) -> None:
        """Reset the cursor shape and display `error_message` in the status bar."""
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.status_bar.show_message(error_message, 10_000)

    # endregion

    # region csv

    def _path_select_popup(self) -> None:
        """Ask the user for a path and write it to the CSV text edit."""
        if settings.Paths.csv is not None:
            start_path = str(settings.Paths.csv.parent)
        else:
            start_path = ""
        path, __ = QtWidgets.QFileDialog.get_open_file_name(
            self, _("Select CSV file"), start_path, _("CSV (*.csv);;All types (*.*)")
        )
        if path:
            self.csv_tab.path_edit.text = str(Path(path))

    def _csv_submit(self) -> None:
        """Parse a CSV file of Spansh rows and emit the route created signal."""
        log.info("Submitting CSV route.")
        path = Path(self.csv_tab.path_edit.text)
        route = self._route_from_csv(path)
        if route is not None:
            self.emit_and_close(
                self.selected_journal,
                route,
                route_index=1,
            )
        log.info(f"Set saved csv {path=}")
        settings.Paths.csv = path

    def _route_from_csv(self, path: Path) -> t.Optional[RouteList]:
        try:
            with path.open(encoding="utf8") as csv_file:
                reader = csv.reader(csv_file, strict=True)
                header = next(reader)
                if len(header) == 5:
                    row_type = NeutronPlotRow
                elif len(header) == 7:
                    row_type = ExactPlotRow
                else:
                    self.status_bar.show_message(_("Invalid CSV file."), 5_000)
                    return
                log.info(f"Parsing csv file of type {row_type.__name__} at {path}.")
                return [row_type.from_csv_row(row) for row in reader]
        except FileNotFoundError:
            self.status_bar.show_message(_("CSV file doesn't exist."), 5_000)
        except csv.Error as error:
            self.status_bar.show_message(_("Invalid CSV file: ") + str(error), 5_000)
        except IndexError:
            self.status_bar.show_message(_("Truncated data in CSV file."), 5_000)
        except ValueError:
            self.status_bar.show_message(_("Invalid data in CSV file."), 5_000)
        except OSError:
            self.status_bar.show_message(_("Invalid path."), 5_000)

    # endregion

    # region last_route
    def _display_saved_route(self, index: int) -> None:
        """Display saved route info if user switched to that tab for the first time."""
        if not self._route_displayed and index == 3:
            self._loaded_route = self._route_from_csv(
                get_config_dir() / ROUTE_FILE_NAME
            )
            self._update_saved_route_text()

    def _last_route_submit(self) -> None:
        log.info("Submitting last route.")
        if self._loaded_route is not None:
            self.emit_and_close(
                self.selected_journal,
                self._loaded_route,
                route_index=settings.General.last_route_index,
            )

    # endregion

    def _sync_journal_combos(self, index: int) -> None:
        """Assign all journal combo boxes to display the item at `index`."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self.combo_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            self.csv_tab.journal_combo.current_index = index
            self.spansh_neutron_tab.journal_combo.current_index = index
            self.spansh_exact_tab.journal_combo.current_index = index
            self.last_route_tab.journal_combo.current_index = index
        self._change_journal(index)

    def _change_journal(self, index: int) -> None:
        """Change the current journal and update the UI with its data, or display an error if shut down."""
        journals = sorted(
            JOURNAL_PATH.glob("Journal.*.log"),
            key=lambda path: path.stat().st_ctime,
            reverse=True,
        )
        journal_path = journals[min(index, len(journals) - 1)]
        log.info(f"Changing selected journal to {journal_path}.")
        journal = Journal(journal_path)
        (
            loadout,
            location,
            last_target,
            cargo_mass,
            shut_down,
        ) = journal.get_static_state()

        self.game_state = GameState(
            Ship(), shut_down, location, last_target, cargo_mass
        )
        self.selected_journal = journal
        if shut_down:
            self.status_bar.show_message(
                _("Selected journal ended with a shut down event."), 10_000
            )
            self.csv_tab.submit_button.enabled = False
            self._set_neutron_submit()
            self._set_exact_submit()
            self.last_route_tab.submit_button.enabled = False
            self._journal_worker = None
            return

        self.selected_journal.shut_down_sig.connect(self._set_neutron_submit)
        self.selected_journal.shut_down_sig.connect(self._set_exact_submit)
        self.game_state.connect_journal(journal)
        if self._journal_worker is not None:
            self._journal_worker.stop()
        self._journal_worker = GameWorker(self, [], journal)
        self._journal_worker.start()

        if loadout is not None and location is not None and cargo_mass is not None:
            self.game_state.ship.update_from_loadout(loadout)
            self._set_widget_values(location, self.game_state.ship, cargo_mass)

        self.status_bar.clear_message()
        self.csv_tab.submit_button.enabled = True
        self._set_neutron_submit()
        self._set_exact_submit()
        self.last_route_tab.submit_button.enabled = True

    def emit_and_close(
        self, journal: Journal, route: RouteList, route_index: int
    ) -> None:
        """Emit a new route and close the window."""
        self.route_created_signal.emit(journal, route, route_index)
        self.close()

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self.combo_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            super().retranslate()
            self._update_saved_route_text()

    def _update_saved_route_text(self) -> None:
        """Update the saved route information from the currently loaded route."""
        if self._loaded_route is not None:
            # NOTE: Source system
            self.last_route_tab.source_label.text = _("Source: {}").format(
                self._loaded_route[0].system
            )
            self.last_route_tab.location_label.text = _("Saved location: {}").format(
                self._loaded_route[settings.General.last_route_index].system
            )
            # NOTE: destination system
            self.last_route_tab.destination_label.text = _("Destination: {}").format(
                self._loaded_route[-1].system
            )
