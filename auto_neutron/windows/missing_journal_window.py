# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.windows.gui.missing_journal_window import MissingJournalWindowGUI


class MissingJournalWindow(MissingJournalWindowGUI):
    """Wrap the GUI to provide the quit functionality."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
