# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import collections.abc
import csv
import json
import logging
import typing as t
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.constants import ROUTE_FILE_NAME, SPANSH_API_URL, get_config_dir
from auto_neutron.game_state import Location
from auto_neutron.journal import Journal
from auto_neutron.route import ExactRoute, NeutronRoute, RoadToRichesRoute, Route
from auto_neutron.ship import Ship
from auto_neutron.spansh_request_manager import SpanshRequestManager
from auto_neutron.utils.utils import create_request_delay_iterator
from auto_neutron.windows import NearestWindow
from auto_neutron.windows.gui.new_route_window import (
    CSVTabGUI,
    ExactTabGUI,
    LastTabGUI,
    NeutronTabGUI,
    RoadToRichesTabGUI,
    SpanshTabGUIBase,
    TabGUIBase,
)
from auto_neutron.windows.opened_window_manager import create_or_activate_window

log = logging.getLogger(__name__)

StatusCallback = (
    collections.abc.Callable[[str, int], t.Any] | collections.abc.Callable[[str], t.Any]
)


class TabBase(TabGUIBase):
    """Tab base that implements basic behaviour of tabs."""

    result_signal = QtCore.Signal(Route)

    def __init__(
        self,
        *args: object,
        status_callback: StatusCallback,
        **kwargs: object,
    ):
        super().__init__()
        self._journal: Journal | None = None
        self._journal_shutdown_connection: QtCore.QMetaObject.Connection | None = None
        self._status_callback = status_callback
        self.submit_button.pressed.connect(self._get_route)

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        """
        Set the submit_button to be enabled/disabled depending on whether the user can submit a plot.

        By default checks for a selected journal.
        """
        self.submit_button.enabled = (
            self._journal is not None and not self._journal.shut_down
        )

    @QtCore.Slot()
    def _get_route(self) -> None:
        """Get the route for the main table, should emit `result_signal` with the route after it's called."""
        raise NotImplementedError  # QObject's metaclass is problematic so can't use abc.

    def set_journal(self, journal: Journal | None) -> None:
        """Set the tracked journal to `journal`."""
        if self._journal_shutdown_connection is not None:
            self._journal.disconnect(self._journal_shutdown_connection)
        self._journal_shutdown_connection = journal.shut_down_sig.connect(
            self._set_submit_sensitive
        )

        self._journal = journal
        self._set_submit_sensitive()

    def emit_route_with_index(self, route: Route, index: int = 1) -> None:
        """Set `route`'s index to `index` and emit `result_signal` with it."""
        route.index = index
        self.result_signal.emit(route)


class CSVTab(TabBase, CSVTabGUI):  # noqa: D101
    def __init__(
        self,
        *,
        status_callback: StatusCallback,
    ):
        super().__init__(status_callback=status_callback)
        self.path_popup_button.pressed.connect(self._path_select_popup)
        self.path_edit.textChanged.connect(self._set_submit_sensitive)

        if settings.Paths.csv is not None:
            self.path_edit.text = str(settings.Paths.csv)

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        self.submit_button.enabled = (
            self._journal is not None
            and not self._journal.shut_down
            and bool(self.path_edit.text)
        )

    @QtCore.Slot()
    def _get_route(self) -> None:
        """Parse a CSV file of Spansh rows and emit the route created signal."""
        log.info("Submitting CSV route.")
        path = Path(self.path_edit.text)
        route = self._route_from_csv(path)
        if route is not None:
            self.emit_route_with_index(route)
        log.info(f"Set saved csv {path=}")
        settings.Paths.csv = path

    def _route_from_csv(self, path: Path) -> Route | None:
        """
        Get the route from the csv file at `Path`.

        If the file is invalid display an error message through the status callback.
        """
        try:
            return Route.from_csv_file(path)

        except FileNotFoundError:
            self._status_callback(_("CSV file doesn't exist."), 5_000)
        except csv.Error as error:
            self._status_callback(_("Invalid CSV file: ") + str(error), 5_000)
        except IndexError:
            self._status_callback(_("Truncated data in CSV file."), 5_000)
        except ValueError:
            self._status_callback(_("Invalid data in CSV file."), 5_000)
        except OSError:
            self._status_callback(_("Invalid path."), 5_000)
        except Exception as e:
            self._status_callback(_("Invalid CSV file."), 5_000)
            log.info("CSV parsing failed with", exc_info=e)

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
            self.path_edit.text = str(Path(path))


class LastRouteTab(TabBase, LastTabGUI):  # noqa: D101
    def __init__(
        self,
        *,
        status_callback: StatusCallback,
    ):
        super().__init__(status_callback=status_callback)
        self._loaded_route: Route | None = None

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        self.submit_button.enabled = (
            self._journal is not None
            and not self._journal.shut_down
            and bool(self._loaded_route)
        )

    @QtCore.Slot()
    def _get_route(self) -> None:
        log.info("Submitting last route.")
        if self._loaded_route is not None:
            self.emit_route_with_index(
                self._loaded_route, settings.General.last_route_index
            )

    def _update_saved_route_text(self) -> None:
        """Update the saved route information from the currently loaded route."""
        if self._loaded_route is not None:
            # NOTE: Source system
            self.source_label.text = _("Source: {}").format(
                self._loaded_route.entries[0].system
            )
            self.location_label.text = _("Saved location: {}").format(
                self._loaded_route.entries[settings.General.last_route_index].system
            )
            # NOTE: destination system
            self.destination_label.text = _("Destination: {}").format(
                self._loaded_route.entries[-1].system
            )

    def show_event(self, event: QtGui.QShowEvent) -> None:
        """Try to get the saved route on the first show, or until valid."""
        if not self._loaded_route:
            try:
                self._loaded_route = Route.from_csv_file(
                    get_config_dir() / ROUTE_FILE_NAME,
                )
            except Exception:
                self._status_callback(_("No saved route found."), 5_000)
            self._update_saved_route_text()
            self._set_submit_sensitive()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self._update_saved_route_text()


class SpanshTabBase(TabBase, SpanshTabGUIBase):
    """
    Base class for tabs that interface with Spansh.

    endpoint and route_type must be specified by the subclass:
        endpoint is used for the Spansh api
        route_type is used to decode the api response and create a route

    GUI elements are updated from journal after it's set by the caller.
    """

    endpoint: t.ClassVar[str] = None  # type: ignore
    route_type: t.ClassVar[type[Route]] = None  # type: ignore

    started_plotting = QtCore.Signal()
    plotting_error = QtCore.Signal()

    def __init__(
        self,
        *,
        status_callback: StatusCallback,
    ):
        super().__init__(status_callback=status_callback)
        self._request_manager: SpanshRequestManager | None = None
        self._connections = list[QtCore.QMetaObject.Connection]()
        self.nearest_button.pressed.connect(self._display_nearest_window)
        self.source_edit.textChanged.connect(self._set_submit_sensitive)
        self.target_edit.textChanged.connect(self._set_submit_sensitive)

    def set_journal(self, journal: Journal | None) -> None:
        """
        Set the journal to `journal` and update all GUI elements with its values.

        The journal is then followed for any further changes.
        """
        if self._journal is not None:
            for connection in self._connections:
                self._journal.disconnect(connection)
            self._connections.clear()
        if journal is not None:
            self._connections.extend(
                (
                    journal.loadout_sig.connect(self._update_from_loadout),
                    journal.system_sig.connect(self._update_from_location),
                    journal.target_signal.connect(self._update_from_target),
                    journal.cargo_signal.connect(self._update_from_cargo),
                )
            )

            if journal.ship is not None:
                self._update_from_loadout(journal.ship)

            if journal.location is not None:
                self._update_from_location(journal.location)

            if journal.last_target is not None:
                self._update_from_target(journal.last_target)

            if journal.cargo is not None:
                self._update_from_cargo(journal.cargo)

        super().set_journal(journal)

    def set_request_manager(self, manager: SpanshRequestManager) -> None:
        """Set the request manager to `manager`."""
        self._request_manager = manager

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        """Set submit to be active when both source and target are filled, and a journal is selected."""
        self.submit_button.enabled = bool(
            self.source_edit.text
            and self.target_edit.text
            and self._journal is not None
            and not self._journal.shut_down
        )

    def _request_params(self) -> dict[str, t.Any] | None:
        """Get the params to send with the request."""
        raise NotImplementedError

    @QtCore.Slot()
    def _get_route(self) -> None:
        """Submit a Spansh job to `self.endpoint` and decode it with `self.route_type`."""
        assert (
            self._request_manager is not None
        ), "Request manager must be set before a request is made."
        log.info(f"Submitting Spansh job to {self.endpoint} for {self.route_type=}.")
        params = self._request_params()
        if params is None:
            return

        self._request_manager.make_request(
            f"{SPANSH_API_URL}/{self.endpoint}",
            params=params,
            finished_callback=partial(
                self._request_manager.route_decode_callback,
                error_callback=self._spansh_error_callback,
                delay_iterator=create_request_delay_iterator(),
                result_callback=self.emit_route_with_index,
                route_type=self.route_type,
            ),
        )
        self.started_plotting.emit()

    @QtCore.Slot()
    def _display_nearest_window(self) -> None:
        """Display the nearest system finder window and link its signals."""
        log.info("Displaying nearest window.")
        window = create_or_activate_window(
            NearestWindow,
            self.__class__.__name__,
            self,
            None if self._journal is None else self._journal.location,
            self._status_callback,
        )
        if window is None:
            return

        def set_modified(widget: QtWidgets.QLineEdit, *args) -> None:
            widget.modified = True

        window.copy_source.connect(partial(setattr, self.source_edit, "text"))
        window.copy_source.connect(partial(set_modified, self.source_edit))

        window.copy_destination.connect(partial(setattr, self.target_edit, "text"))
        window.copy_destination.connect(partial(set_modified, self.target_edit))

        @QtCore.Slot()
        def set_input_from_target() -> None:
            if self._journal is not None:
                window.set_input_values_from_location(self._journal.last_target)

        @QtCore.Slot()
        def set_input_from_location() -> None:
            if self._journal is not None:
                window.set_input_values_from_location(self._journal.location)

        window.from_target_button.pressed.connect(set_input_from_target)
        window.from_location_button.pressed.connect(set_input_from_location)
        window.show()

    def _spansh_error_callback(self, error_message: str) -> None:
        """Display `error_message` in the status bar."""
        self._status_callback(error_message, 10_000)
        self.plotting_error.emit()

    @QtCore.Slot()
    def _update_from_loadout(self, ship: Ship) -> None:
        """Update widget values for a new ship loadout."""
        self.cargo_slider.maximum = ship.max_cargo

    @QtCore.Slot()
    def _update_from_location(self, new_location: Location) -> None:
        """Update widget values for a new location."""
        if not self.source_edit.modified or not self.source_edit.text:
            self.source_edit.text = new_location.name

    @QtCore.Slot()
    def _update_from_target(self, new_target: Location) -> None:
        """Update widget values for a new target."""
        if not self.target_edit.modified or not self.target_edit.text:
            self.target_edit.text = new_target.name

    @QtCore.Slot()
    def _update_from_cargo(self, new_cargo: int) -> None:
        """Update widget values for a new location."""
        self.cargo_slider.value = new_cargo


class NeutronTab(SpanshTabBase, NeutronTabGUI):  # noqa: D101
    endpoint = "route"
    route_type = NeutronRoute

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.range_spin.value = 50
        self.efficiency_spin.value = 80

        self.cargo_slider.valueChanged.connect(self._range_from_cargo)

    @QtCore.Slot()
    def _update_from_loadout(self, ship: Ship) -> None:
        """Update range for changed cargo."""
        super()._update_from_loadout(ship)
        range_ = _get_range(journal=self._journal, ship=ship)
        if range_ is not None:
            self.range_spin.value = range_

    @QtCore.Slot()
    def _range_from_cargo(self, cargo: int) -> None:
        range_ = _get_range(journal=self._journal, cargo_mass=cargo)
        if range_ is not None:
            self.range_spin.value = range_

    def _request_params(self) -> dict[str, t.Any]:
        return {
            "efficiency": self.efficiency_spin.value,
            "range": self.range_spin.value,
            "from": self.source_edit.text,
            "to": self.target_edit.text,
        }


class ExactTab(SpanshTabBase, ExactTabGUI):  # noqa: D101
    endpoint = "generic/route"
    route_type = ExactRoute

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.use_clipboard_checkbox.stateChanged.connect(self._set_submit_sensitive)

    def _request_params(self) -> dict[str, t.Any] | None:
        if self.use_clipboard_checkbox.checked:
            try:
                ship = Ship.from_coriolis(
                    json.loads(QtWidgets.QApplication.instance().clipboard().text())
                )
            except (json.JSONDecodeError, KeyError):
                self._status_callback(_("Invalid ship data in clipboard."), 5_000)
                return
        else:
            ship = self._journal.ship
        return {
            "source": self.source_edit.text,
            "destination": self.target_edit.text,
            "is_supercharged": int(self.is_supercharged_checkbox.checked),
            "use_supercharge": int(self.supercarge_checkbox.checked),
            "use_injections": int(self.fsd_injections_checkbox.checked),
            "exclude_secondary": int(self.exclude_secondary_checkbox.checked),
            "fuel_power": ship.fsd.size_const,
            "fuel_multiplier": ship.fsd.rating_const / 1000,
            "optimal_mass": ship.fsd.optimal_mass,
            "base_mass": ship.unladen_mass + ship.reserve_size,
            "tank_size": ship.tank_size,
            "internal_tank_size": ship.reserve_size,
            "max_fuel_per_jump": ship.fsd.max_fuel_usage,
            "range_boost": ship.jump_range_boost,
            "cargo": self.cargo_slider.value,
        }

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        self.submit_button.enabled = bool(
            self.source_edit.text
            and self.target_edit.text
            and self._journal is not None
            and not self._journal.shut_down
            and (self._journal.ship is not None or self.use_clipboard_checkbox.checked)
        )

    @QtCore.Slot()
    def _update_from_cargo(self, new_cargo: int) -> None:
        """Don't update cargo maximum."""


class RoadToRichesTab(SpanshTabBase, RoadToRichesTabGUI):  # noqa: D101
    endpoint = "riches/route"
    route_type = RoadToRichesRoute

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.target_edit.textChanged.connect(self._disable_loop_on_target)
        self.cargo_slider.valueChanged.connect(self._range_from_cargo)

    def _request_params(self) -> dict[str, t.Any] | None:
        return {
            "radius": self.radius_spinbox.value,
            "range": self.range_spinbox.value,
            "from": self.source_edit.text,
            "to": self.target_edit.text,
            "max_results": self.max_systems_spinbox.value,
            "max_distance": self.max_distance_slider.value,
            "min_value": self.minimum_scan_slider.value,
            "use_mapping_value": self.use_mapping_value_checkbox.checked,
            "loop": self.loop_checkbox.checked,
        }

    @QtCore.Slot()
    def _update_from_loadout(self, ship: Ship) -> None:
        """Update range for changed cargo."""
        super()._update_from_loadout(ship)
        range_ = _get_range(journal=self._journal, ship=ship)
        if range_ is not None:
            self.range_spinbox.value = range_

    @QtCore.Slot()
    def _range_from_cargo(self, cargo: int) -> None:
        range_ = _get_range(journal=self._journal, cargo_mass=cargo)
        if range_ is not None:
            self.range_spinbox.value = range_

    @QtCore.Slot()
    def _disable_loop_on_target(self, target_text: str) -> None:
        """Disable the loop route checkbox if there's any `target_text`."""
        self.loop_checkbox.enabled = not target_text

    @QtCore.Slot()
    def _set_submit_sensitive(self) -> None:
        self.submit_button.enabled = bool(
            self.source_edit.text
            and self._journal is not None
            and not self._journal.shut_down
        )


def _get_range(
    *,
    journal: Journal | None,
    cargo_mass: int | None = None,
    ship: Ship | None = None,
) -> float | None:
    """
    Get the user's jump range for `cargo_mass`.

    If `cargo_mass` is None or not passed in, the journal's cargo is used, or 0 if unknown.
    """
    if cargo_mass is None:
        if journal is not None and journal.cargo is not None:
            cargo_mass = journal.cargo
        else:
            cargo_mass = 0

    if ship is None and journal is not None:
        ship = journal.ship

    if ship is not None:
        return ship.jump_range(cargo_mass=cargo_mass)
