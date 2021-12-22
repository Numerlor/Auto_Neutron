# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import logging
import typing as t
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.utils.file import get_file_name
from auto_neutron.windows.gui.error_window import ErrorWindowGUI

root_logger = logging.getLogger()

ISSUES_URL = "https://github.com/Numerlor/Auto_Neutron/issues/new"
ERROR_TEXT = (
    "Please make sure to report the bug at <br>"
    f'<a href="{ISSUES_URL}" style="color: #007bff">{ISSUES_URL}</a>,<br>'
    "and include the {file_name} file from<br>"
    ' <a href="{log_path}" style="color: #007bff">{log_path}</a>'
)


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

    def _set_text(self) -> None:
        """Set the help text to point the user to the current log file."""
        log_path = QtCore.QStandardPaths.writable_location(
            QtCore.QStandardPaths.AppConfigLocation
        )
        file_name = self._get_log_file_name()
        self.text_browser.html = ERROR_TEXT.format(
            log_path=log_path, file_name=file_name
        )

    def show(self) -> None:
        """Show the window, if the window was already displayed, change the label and increments its counter instead."""
        self._set_text()
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

    def _get_log_file_name(self) -> t.Optional[str]:
        """Get the file name of the current active file logger, or None if none are used."""
        handler = next(
            filter(
                lambda handler: isinstance(handler, logging.FileHandler),
                root_logger.handlers,
            ),
            None,
        )

        if handler is not None:
            return Path(get_file_name(handler.stream)).name
        else:
            return None
