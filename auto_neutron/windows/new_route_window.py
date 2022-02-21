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
    from auto_neutron.route_plots import RouteList
log = logging.getLogger(__name__)


class NewRouteWindow(NewRouteWindowGUI):
    """The UI for plotting a new route, from CSV, Spansh plotters, or the last saved route."""

    route_created_signal = QtCore.Signal(Journal, list, int)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.selected_journal: Journal | None = None
        self._journals = dict[Path, Journal]()
        self._journal_worker: GameWorker | None = None
        self._status_hide_timer = QtCore.QTimer(self)
        self._status_hide_timer.single_shot_ = True
        self._status_hide_timer.timeout.connect(self._reset_status_text)
        self._status_has_hover = False
        self._status_scheduled_reset = False
        self._setup_status_widget()

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

        self.spansh_neutron_tab.range_spin.value = 50
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
        self._loaded_route: list[NeutronPlotRow] | None = None
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
            try:
                ship = Ship.from_coriolis(
                    json.loads(QtWidgets.QApplication.instance().clipboard().text())
                )
            except (json.JSONDecodeError, KeyError):
                self._show_status_message(_("Invalid ship data in clipboard."), 5_000)
                return
        else:
            ship = self.selected_journal.ship

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

    def _set_widget_values(self) -> None:
        """Update the UI with values from the game state."""
        if (
            not self.spansh_neutron_tab.source_edit.modified
            or not self.spansh_neutron_tab.source_edit.text
        ):
            self.spansh_neutron_tab.source_edit.text = (
                self.selected_journal.location.name
            )
        if (
            not self.spansh_exact_tab.source_edit.modified
            or not self.spansh_exact_tab.source_edit.text
        ):
            self.spansh_exact_tab.source_edit.text = self.selected_journal.location.name

        if self.selected_journal.last_target is not None:
            if (
                not self.spansh_neutron_tab.target_edit.modified
                or not self.spansh_neutron_tab.target_edit.text
            ):
                self.spansh_neutron_tab.target_edit.text = (
                    self.selected_journal.last_target.name
                )
            if (
                not self.spansh_exact_tab.target_edit.modified
                or not self.spansh_exact_tab.target_edit.text
            ):
                self.spansh_exact_tab.target_edit.text = (
                    self.selected_journal.last_target.name
                )

        self.spansh_neutron_tab.cargo_slider.maximum = (
            self.selected_journal.ship.max_cargo
        )
        self.spansh_neutron_tab.cargo_slider.value = self.selected_journal.cargo

        self.spansh_exact_tab.cargo_slider.value = self.selected_journal.cargo

        self.spansh_neutron_tab.range_spin.value = (
            self.selected_journal.ship.jump_range(
                cargo_mass=self.selected_journal.cargo
            )
        )

    def _recalculate_range(self, cargo_mass: int | None = None) -> None:
        """Recalculate jump range with the new cargo_mass."""
        if cargo_mass is None:
            cargo_mass = self.selected_journal.cargo
        if self.selected_journal.ship.initialized:  # Ship may not be available yet
            self.spansh_neutron_tab.range_spin.value = (
                self.selected_journal.ship.jump_range(cargo_mass=cargo_mass)
            )

    def _set_neutron_submit(self) -> None:
        """Enable the neutron submit button if both inputs are filled, disable otherwise."""
        self.spansh_neutron_tab.submit_button.enabled = bool(
            self.spansh_neutron_tab.source_edit.text
            and self.spansh_neutron_tab.target_edit.text
            and not self.selected_journal.shut_down
        )

    def _set_exact_submit(self) -> None:
        """Enable the exact submit button if both inputs are filled, disable otherwise."""
        self.spansh_exact_tab.submit_button.enabled = bool(
            self.spansh_exact_tab.source_edit.text
            and self.spansh_exact_tab.target_edit.text
            and not self.selected_journal.shut_down
            and (
                self.selected_journal.ship.initialized
                or self.spansh_exact_tab.use_clipboard_checkbox.checked
            )
        )

    def _display_nearest_window(self) -> None:
        """Display the nearest system finder window and link its signals."""
        log.info("Displaying nearest window.")
        window = NearestWindow(self, self.selected_journal.location, self.status_bar)
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
            lambda: window.set_input_values_from_location(
                self.selected_journal.last_target
            )
        )
        window.from_location_button.pressed.connect(
            lambda: window.set_input_values_from_location(
                self.selected_journal.location
            )
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
        self._show_status_message(error_message, 10_000)

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

    def _route_from_csv(self, path: Path) -> RouteList | None:
        try:
            with path.open(encoding="utf8") as csv_file:
                reader = csv.reader(csv_file, strict=True)
                header = next(reader)
                if len(header) == 5:
                    row_type = NeutronPlotRow
                elif len(header) == 7:
                    row_type = ExactPlotRow
                else:
                    self._show_status_message(_("Invalid CSV file."), 5_000)
                    return
                log.info(f"Parsing csv file of type {row_type.__name__} at {path}.")
                return [row_type.from_csv_row(row) for row in reader]
        except FileNotFoundError:
            self._show_status_message(_("CSV file doesn't exist."), 5_000)
        except csv.Error as error:
            self._show_status_message(_("Invalid CSV file: ") + str(error), 5_000)
        except IndexError:
            self._show_status_message(_("Truncated data in CSV file."), 5_000)
        except ValueError:
            self._show_status_message(_("Invalid data in CSV file."), 5_000)
        except OSError:
            self._show_status_message(_("Invalid path."), 5_000)

    # endregion

    # region last_route
    def _display_saved_route(self, index: int) -> None:
        """Display saved route info if user switched to that tab for the first time."""
        if not self._route_displayed and index == 3:
            self._loaded_route = self._route_from_csv(
                get_config_dir() / ROUTE_FILE_NAME
            )
            self._update_saved_route_text()
            self._route_displayed = True

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
        journal = self._get_journal(journal_path)

        self.selected_journal = journal
        if journal.shut_down:
            self._show_status_message(
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

        self.selected_journal.loadout_sig.connect(lambda: self._recalculate_range())
        self.selected_journal.loadout_sig.connect(self._set_widget_values)
        self.selected_journal.system_sig.connect(self._set_widget_values)
        self.selected_journal.target_signal.connect(self._set_widget_values)

        if self._journal_worker is not None:
            self._journal_worker.stop()
        self._journal_worker = GameWorker(self, [], journal)
        self._journal_worker.start()

        if (
            journal.ship.initialized
            and journal.location is not None
            and journal.cargo is not None
        ):
            self._set_widget_values()

        self.status_widget.text = ""
        self.csv_tab.submit_button.enabled = True
        self._set_neutron_submit()
        self._set_exact_submit()
        self.last_route_tab.submit_button.enabled = True

    def _get_journal(self, path: Path) -> Journal:
        """Get the journal object form `path`, if the journal was opened before, get the changed object and parse it."""
        try:
            journal = self._journals[path]
        except KeyError:
            journal = self._journals[path] = Journal(path)
        journal.parse()
        return journal

    def emit_and_close(
        self, journal: Journal, route: RouteList, route_index: int
    ) -> None:
        """Emit a new route and close the window."""
        self.route_created_signal.emit(journal, route, route_index)
        self.close()

    def _show_status_message(self, message: str, timeout: int = 0) -> None:
        """
        Show `message` in the status widget.

        If `timeout` is provided and non-zero, the text is hidden in `timeout` ms.
        """
        self._status_hide_timer.stop()
        if timeout:
            self._status_hide_timer.interval = timeout
            self._status_hide_timer.start()

        self.status_widget.text = message

    def _setup_status_widget(self) -> None:
        """Patch the status widget's methods to intercept hover events."""
        original_enter_event = self.status_widget.enter_event

        def patched_enter_event(event: QtGui.QEnterEvent) -> None:
            """Set the status hover attribute."""
            original_enter_event(event)
            self._status_has_hover = True

        self.status_widget.enter_event = patched_enter_event

        original_leave_event = self.status_widget.leave_event

        def patched_leave_event(event: QtCore.QEvent) -> None:
            """Reset text if the user leaves and the text was supposed to be hidden during that."""
            original_leave_event(event)
            self._status_has_hover = False
            if self._status_scheduled_reset:
                self.status_widget.text = ""
                self._status_scheduled_reset = False

        self.status_widget.leave_event = patched_leave_event

    def _reset_status_text(self) -> None:
        """Reset the status text, or set the scheduled attribute if the status widget is currently hovered."""
        if not self._status_has_hover:
            self.status_widget.text = ""
        else:
            self._status_scheduled_reset = True

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
