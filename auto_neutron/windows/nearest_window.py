# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
import typing as t

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.utils.network import (
    NetworkError,
    json_from_network_req,
    make_network_request,
)

from .gui.nearest_window import NearestWindowGUI

if t.TYPE_CHECKING:
    import collections.abc

    from auto_neutron.game_state import Location


log = logging.getLogger(__name__)


class NearestWindow(NearestWindowGUI):
    """Provide a UI to Spansh's nearest API and let the user get the result through the provided buttons."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        start_location: Location,
        status_callback: collections.abc.Callable[[str]]
        | collections.abc.Callable[[str, int]],
    ):
        super().__init__(parent)
        self.set_input_values_from_location(start_location)
        self.search_button.pressed.connect(self._make_nearest_request)
        self._status_callback = status_callback
        self._current_network_request = None
        self.retranslate()

    def set_input_values_from_location(self, location: Location | None) -> None:
        """Set the input spinboxes to x, y, z."""
        if location is not None:
            log.debug(f"Applying spinbox values from {location=}")
            self.x_spinbox.value = location.x
            self.y_spinbox.value = location.y
            self.z_spinbox.value = location.z

    def _make_nearest_request(self) -> None:
        """Make a request to Spansh's nearest endpoint with the values from spinboxes."""
        self._abort_request()
        self._current_network_request = make_network_request(
            SPANSH_API_URL + "/nearest",
            params={
                "x": self.x_spinbox.value,
                "y": self.y_spinbox.value,
                "z": self.z_spinbox.value,
            },
            finished_callback=self._assign_from_reply,
        )
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.BusyCursor)

    def _assign_from_reply(self, reply: QtNetwork.QNetworkReply) -> None:
        """Decode the spansh JSON reply and display the data to the user."""
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.BusyCursor)
        self._current_network_request = None

        try:
            data = json_from_network_req(reply, json_error_key="error")
        except NetworkError as e:
            if (
                e.error_type
                is QtNetwork.QNetworkReply.NetworkError.OperationCanceledError
            ):
                return

            if e.reply_error is not None:
                message = _("Received error from Spansh: {}").format(e.reply_error)
            else:
                # Fall back to Qt error message if spansh didn't respond
                message = e.error_message
            self._status_callback.show_message(message, 10_000)
        else:
            self.system_name_result_label.text = data["system"]["name"]
            self.distance_result_label.text = (
                format(data["system"]["distance"], ".2f").rstrip("0").rstrip(".")
                + " Ly"
            )

            self.x_result_label.text = (
                format(data["system"]["x"], ".2f").rstrip("0").rstrip(".")
            )
            self.y_result_label.text = (
                format(data["system"]["y"], ".2f").rstrip("0").rstrip(".")
            )
            self.z_result_label.text = (
                format(data["system"]["z"], ".2f").rstrip("0").rstrip(".")
            )

    def _abort_request(self) -> None:
        """Abort the currently running network request, if any."""
        if self._current_network_request is not None:
            self._current_network_request.abort()
        self.cursor = QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def close_event(self, event: QtGui.QCloseEvent) -> None:
        """Abort any running network request on close."""
        self._abort_request()

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()
