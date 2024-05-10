# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
import textwrap
import uuid
from pathlib import Path

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.utils.file import get_file_name

from ..utils.network import NetworkError, json_from_network_req, post_request
from ..utils.utils import get_application
from .gui.error_window import ErrorWindowGUI

root_logger = logging.getLogger()

ISSUES_URL = "https://github.com/Numerlor/Auto_Neutron/issues/new"


log = logging.getLogger(__name__)


class ErrorWindow(ErrorWindowGUI):
    """
    Error window wrapper that modifies the base to show more information to the user.

    If the window is attempted to be shown multiple times at once, instead modify the top label
    to show that multiple errors have occurred and show the number of errors.
    """

    def __init__(self, parent: QtWidgets.QWidget):
        self._num_errors = 0
        super().__init__(parent)
        self.quit_button.pressed.connect(get_application().quit)
        self.send_log.pressed.connect(self._send_error_report)
        self.error_template = ""
        self.retranslate()

    def _set_text(self) -> None:
        """Set the help text to point the user to the current log file."""
        log_path = QtCore.QStandardPaths.writable_location(
            QtCore.QStandardPaths.StandardLocation.AppConfigLocation
        )
        file_name = self._get_log_file_name().name
        self.text_browser.markdown = self.error_template.format(
            log_path=log_path, file_name=file_name
        )

    def _send_error_report(self) -> None:
        """Send error to the api with the log attached."""
        self.cursor = QtCore.Qt.CursorShape.BusyCursor
        log_file = self._get_log_file_name()
        log.info("Sending session log to api.")
        if log_file is not None:
            post_request(
                "https://www.numerlor.me/auto_neutron/error/",
                json_={
                    "user_uuid": str(uuid.UUID(int=uuid.getnode())),
                    "error_log": log_file.read_text("utf8"),
                },
                finished_callback=self._receive_reply,
            )
        else:
            log.info("No log file found.")

    def _receive_reply(self, reply: QtNetwork.QNetworkReply) -> None:
        """Receive response from the error api, if failed display a warning to the user."""
        self.cursor = QtCore.Qt.CursorShape.ArrowCursor
        try:
            json_from_network_req(reply)
            log.debug("Successfully sent log to api.")
        except NetworkError as e:
            if e.reply_error is not None:
                error_msg = e.reply_error
            else:
                error_msg = e.error_message
            log.warning("Failed to send error log: %s", error_msg)
            QtWidgets.QMessageBox.warning(
                self, "Auto_Neutron", _("Failed to upload session log.")
            )

    def show(self) -> None:
        """Show the window, if the window was already displayed, change the label and increments its counter instead."""
        self._set_text()
        self._num_errors += 1
        if self._num_errors > 1:
            self.info_label.text = _(
                "Multiple unexpected errors have occurred (x{})"
            ).format(self._num_errors)
        else:
            super().show()

    def close_event(self, event: QtGui.QCloseEvent) -> None:
        """Reset the error count to zero when the window is closed."""
        self._num_errors = 0

    def _get_log_file_name(self) -> Path | None:
        """Get the file name of the current active file logger, or None if none are used."""
        handler = next(
            (
                handler
                for handler in root_logger.handlers
                if isinstance(handler, logging.FileHandler)
            ),
            None,
        )

        if handler is not None:
            return Path(get_file_name(handler.stream))
        else:
            return None

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        if self._num_errors > 1:
            self.info_label.text = _(
                "Multiple unexpected errors have occurred (x{})"
            ).format(self._num_errors)

        self.error_template = textwrap.dedent(
            _(
                """\
        Please make sure to report the bug by submitting the session log, or at [Github]({issues_url}),
        and include the {{file_name}} file from [the log directory]({{log_path}}).\\
        You may close this window, but the program may not be fully functional, or it may produce erroneous behaviour.
        """
            )
        ).format(issues_url=ISSUES_URL)
        self._set_text()
