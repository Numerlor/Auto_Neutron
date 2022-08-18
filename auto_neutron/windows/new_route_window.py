# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import contextlib
import datetime
import logging

import babel.dates
from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.journal import Journal, get_unique_cmdr_journals
from auto_neutron.locale import get_active_locale
from auto_neutron.route import Route
from auto_neutron.spansh_request_manager import SpanshRequestManager
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.utils.utils import N_, cmdr_display_name
from auto_neutron.workers import GameWorker

from .gui.new_route_window import NewRouteWindowGUI
from .new_route_window_tabs import (
    CSVTab,
    ExactTab,
    LastRouteTab,
    NeutronTab,
    SpanshTabBase,
    TabBase,
)

log = logging.getLogger(__name__)


class NewRouteWindow(NewRouteWindowGUI):
    """The UI for plotting a new route, from CSV, Spansh plotters, or the last saved route."""

    route_created_signal = QtCore.Signal(Journal, Route)
    tabs: list[TabBase]

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(
            parent,
            tabs=[
                (
                    NeutronTab(status_callback=self._show_status_message),
                    N_("Neutron plotter"),
                ),
                (
                    ExactTab(status_callback=self._show_status_message),
                    N_("Galaxy plotter"),
                ),
                (
                    CSVTab(status_callback=self._show_status_message),
                    N_("CSV"),
                ),
                (
                    LastRouteTab(status_callback=self._show_status_message),
                    N_("Saved route"),
                ),
            ],
        )
        self._request_manager = SpanshRequestManager(self)

        self.selected_journal: Journal | None = None
        self._journals = list[Journal]()
        self._journal_worker: GameWorker | None = None
        self._status_hide_timer = QtCore.QTimer(self)
        self._status_hide_timer.single_shot_ = True
        self._status_hide_timer.timeout.connect(self._reset_status_text)
        self._status_has_hover = False
        self._status_scheduled_reset = False
        self._setup_status_widget()

        self.combo_signals = list[ReconnectingSignal]()
        self._source_sync_signals = list[ReconnectingSignal]()
        self._destination_sync_signals = list[ReconnectingSignal]()

        for tab in self.tabs:
            tab.refresh_button.pressed.connect(self._populate_journal_combos)
            tab.abort_button.pressed.connect(self._abort_request)
            tab.result_signal.connect(self.emit_and_close)

            if isinstance(tab, SpanshTabBase):
                tab.started_plotting.connect(self._set_busy_cursor)
                tab.started_plotting.connect(self.switch_submit_abort)
                tab.plotting_error.connect(self.switch_submit_abort)

                source_sync_signal = ReconnectingSignal(
                    tab.source_edit.textChanged,
                    self._sync_source_line_edits,
                )
                source_sync_signal.connect()
                self._source_sync_signals.append(source_sync_signal)

                destination_sync_signal = ReconnectingSignal(
                    tab.target_edit.textChanged,
                    self._sync_destination_line_edits,
                )
                destination_sync_signal.connect()
                self._destination_sync_signals.append(destination_sync_signal)

                tab.set_request_manager(self._request_manager)

            journal_changed_signal = ReconnectingSignal(
                tab.journal_combo.currentIndexChanged,
                self._sync_journal_combos,
            )
            journal_changed_signal.connect()
            self.combo_signals.append(journal_changed_signal)

        self.retranslate()
        self._populate_journal_combos()

    def _set_busy_cursor(self) -> None:
        """Set the cursor to the busy cursor."""
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.BusyCursor)

    def _abort_request(self) -> None:
        """Abort the current network request, if any."""
        self._request_manager.abort()
        self.switch_submit_abort()
        self._show_status_message("Cancelled route plot.", 2_500)
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def _sync_journal_combos(self, index: int) -> None:
        """Assign all journal combo boxes to display the item at `index`."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self.combo_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            for tab in self.tabs:
                tab.journal_combo.current_index = index
        self._change_journal(index)

    def _sync_source_line_edits(self, text: str) -> None:
        """Sync all source line edits of Spansh tabs."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self._source_sync_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            for tab in self.tabs:
                if isinstance(tab, SpanshTabBase) and (
                    tab.source_edit.modified or not tab.source_edit.text
                ):
                    tab.source_edit.text = text

    def _sync_destination_line_edits(self, text: str) -> None:
        """Sync all destination line edits of Spansh tabs."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self._destination_sync_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            for tab in self.tabs:
                if isinstance(tab, SpanshTabBase) and (
                    not tab.target_edit.modified or not tab.target_edit.text
                ):
                    tab.target_edit.text = text

    def _populate_journal_combos(self, *, show_change_message: bool = True) -> None:
        """
        Populate the combo boxes with CMDR names referring to latest active journal files.

        The journals they're referring to are stored in `self._journals`.
        """
        font_metrics = self.tabs[0].journal_combo.font_metrics()

        combo_items = []
        self._journals = get_unique_cmdr_journals()
        for journal in self._journals:
            combo_items.append(
                font_metrics.elided_text(
                    cmdr_display_name(journal.cmdr),
                    QtCore.Qt.TextElideMode.ElideRight,
                    80,
                )
            )

        with contextlib.ExitStack() as exit_stack:
            for signal in self.combo_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())

            for tab in self.tabs:
                tab.journal_combo.clear()

            if self._journals:
                log.info(
                    f"Populating journal combos with {len(self._journals)} journals."
                )
                for tab in self.tabs:
                    tab.journal_combo.add_items(combo_items)

                self._change_journal(0, show_change_message=show_change_message)
            else:
                log.info("No valid journals found to populate combos with.")
                self._show_status_message(
                    _("Found no active journal files from within the last week."),
                    timeout=10_000,
                )

                self.selected_journal = None
                for tab in self.tabs:
                    tab.set_journal(None)

    def _change_journal(self, index: int, *, show_change_message: bool = True) -> None:
        """Change the current journal and update the UI with its data, or display an error if shut down."""
        journal = self._journals[index]
        log.info(f"Changing selected journal to index {index} ({journal.path.name}).")

        journal.parse()
        if journal.shut_down:
            if self._journal_worker is not None:
                self._journal_worker.stop()
            self._refresh_journals_on_shutdown()
            return

        self.selected_journal = journal

        for tab in self.tabs:
            tab.set_journal(journal)

        if self._journal_worker is not None:
            self._journal_worker.stop()
        self._journal_worker = GameWorker(self, None, journal)
        self._journal_worker.start()

        creation_time = datetime.datetime.fromtimestamp(journal.path.stat().st_ctime)
        formatted_time = babel.dates.format_time(
            creation_time, locale=get_active_locale()
        )
        formatted_date = babel.dates.format_date(
            creation_time, locale=get_active_locale()
        )

        if show_change_message:
            self._show_status_message(
                _("Selected journal using {}, created at {}; {}").format(
                    "Oddysey" if journal.is_oddysey else "Horizons",
                    formatted_time,
                    formatted_date,
                ),
                timeout=5_000,
            )

    def _refresh_journals_on_shutdown(self) -> None:
        """Refresh the journal combo box and display a message saying that the selected journal got shut down."""
        self._show_status_message(
            _("Selected journal got shut down, available journals refreshed."),
            timeout=7_500,
        )
        self._populate_journal_combos(show_change_message=False)

    def emit_and_close(self, route: Route) -> None:
        """Emit a new route and close the window."""
        self.route_created_signal.emit(self.selected_journal, route)
        self.switch_submit_abort()
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

    def close_event(self, event: QtGui.QCloseEvent) -> None:
        """Abort any running network request on close."""
        self._abort_request()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        exit_stack = contextlib.ExitStack()
        with exit_stack:
            for signal in self.combo_signals:
                exit_stack.enter_context(signal.temporarily_disconnect())
            super().retranslate()
