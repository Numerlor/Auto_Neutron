# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .gui.update_error_window import UpdateErrorWindowGUI


class UpdateErrorWindow(UpdateErrorWindowGUI):
    """Display `error_text` to the user in a simple window."""

    def __init__(self, parent: QtWidgets.QWidget, error_text: str):
        super().__init__(parent)
        self.retranslate()
        self._error_label.setText(error_text)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslate()
