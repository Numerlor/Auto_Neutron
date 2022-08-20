# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from functools import partial

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.journal import Journal, get_unique_cmdr_journals
from auto_neutron.utils.signal import ReconnectingSignal
from auto_neutron.utils.utils import cmdr_display_name

from ..workers import GameWorker
from .gui.shut_down_window import ShutDownWindowGUI


class ShutDownWindow(ShutDownWindowGUI):
    """
    Window displayed after the user reached a shut down.

    The user is given a choice to select a new journal to resome with, to quit, or to save their route.
    """

    new_journal_signal = QtCore.Signal(Journal)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._selected_journal = None
        self._journal_shutdown_connection: QtCore.QMetaObject.Connection | None = None
        self._journal_worker: GameWorker | None = None
        self._journals = []
        self.journal_changed_signal = ReconnectingSignal(
            self.journal_combo.currentIndexChanged, self._change_journal
        )
        self.journal_changed_signal.connect()
        self.new_journal_button.pressed.connect(
            lambda: self.new_journal_signal.emit(self._selected_journal)
        )
        self.new_journal_button.pressed.connect(self.close)
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)

        self._populate_journal_combos()
        self.retranslate()

    def _populate_journal_combos(self) -> None:
        """
        Populate the combo boxes with CMDR names referring to latest active journal files.

        The journals they're referring to are stored in `self._journals`.
        """
        font_metrics = self.journal_combo.font_metrics()

        combo_items = []
        self._journals = get_unique_cmdr_journals()

        if not self._journals:
            self.new_journal_button.enabled = False
            return

        for journal in self._journals:
            combo_items.append(
                font_metrics.elided_text(
                    cmdr_display_name(journal.cmdr),
                    QtCore.Qt.TextElideMode.ElideRight,
                    80,
                )
            )
        self._change_journal(0)
        with self.journal_changed_signal.temporarily_disconnect():
            self.journal_combo.clear()
            self.journal_combo.add_items(combo_items)

    def _change_journal(self, index: int) -> None:
        """Change the selected journal, enable/disable the button depending on its shut down state."""
        journal = self._journals[index]
        journal.parse()
        self.new_journal_button.enabled = not journal.shut_down

        if self._journal_worker is not None:
            self._journal_worker.stop()
        self._journal_worker = GameWorker(self, None, journal)
        self._journal_worker.start()

        if self._journal_shutdown_connection is not None:
            journal.disconnect(self._journal_shutdown_connection)

        self._journal_shutdown_connection = journal.shut_down_sig.connect(
            partial(setattr, self.new_journal_button, "enabled", False)
        )
        self._selected_journal = journal

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        with self.journal_changed_signal.temporarily_disconnect():
            super().retranslate()
