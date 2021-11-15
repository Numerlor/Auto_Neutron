# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.constants import JOURNAL_PATH
from auto_neutron.journal import Journal

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
        self.journal_combo.currentIndexChanged.connect(self._change_journal)
        self.new_journal_button.pressed.connect(
            lambda: self.new_journal_signal.emit(self._selected_journal)
        )
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)

        self._change_journal(0)
        rect = self.geometry
        rect.adjust(-5, -18, 17, 5)  # expand the window a bit to give it breathing room
        self.geometry = rect

    def _change_journal(self, index: int) -> None:
        """Change the selected journal, enable/disable the button depending on its shut down state."""
        journals = sorted(
            JOURNAL_PATH.glob("Journal.*.log"),
            key=lambda path: path.stat().st_ctime,
            reverse=True,
        )
        journal_path = journals[min(index, len(journals) - 1)]
        journal = Journal(journal_path)
        _, _, _, shut_down = journal.get_static_state()
        self.new_journal_button.enabled = not shut_down
        self._selected_journal = journal
