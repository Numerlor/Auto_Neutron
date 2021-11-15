# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from PySide6 import QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.windows.gui.error_window import ErrorWindowGUI


class ErrorWindow(ErrorWindowGUI):
    """
    Error window wrapper that modifies the base to show more information to the user.

    If the window is attempted to be shown multiple times at once, instead modify the top label
    to show that multiple errors have occurred and show the number of errors.
    """

    def __init__(self, parent: QtWidgets.QWidget):
        self._num_errors = 0
        super().__init__(parent)
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)

    def show(self) -> None:
        """Show the window, if the window was already displayed, change the label and increments its counter instead."""
        self._num_errors += 1
        if self._num_errors > 1:
            self.info_label.text = (
                f"Multiple unexpected errors have occurred (x{self._num_errors})"
            )
        else:
            super().show()

    def close_event(self, event: QtGui.QCloseEvent) -> None:
        """Reset the error count to zero when the window is closed."""
        self._num_errors = 0
