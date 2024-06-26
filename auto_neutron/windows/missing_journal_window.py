# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from ..utils.utils import get_application
from .gui.missing_journal_window import MissingJournalWindowGUI


class MissingJournalWindow(MissingJournalWindowGUI):
    """Wrap the GUI to provide the quit functionality."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.quit_button.pressed.connect(get_application().quit)
        self.retranslate()

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslate()
