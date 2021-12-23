# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
import typing as t

from PySide6 import QtNetwork, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.utils.network import json_from_network_req, make_network_request
from auto_neutron.windows.gui.nearest_window import NearestWindowGUI

if t.TYPE_CHECKING:
    from auto_neutron.game_state import Location


log = logging.getLogger(__name__)


class NearestWindow(NearestWindowGUI):
    """Provide a UI to Spansh's nearest API and let the user get the result through the provided buttons."""

    def __init__(self, parent: QtWidgets.QWidget, start_location: Location):
        super().__init__(parent)
        self.set_input_values_from_location(start_location)
        self.search_button.pressed.connect(self._make_nearest_request)

    def set_input_values_from_location(self, location: t.Optional[Location]) -> None:
        """Set the input spinboxes to x, y, z."""
        if location is not None:
            log.debug(f"Applying spinbox values from {location=}")
            self.x_spinbox.value = location.x
            self.y_spinbox.value = location.y
            self.z_spinbox.value = location.z

    def _make_nearest_request(self) -> None:
        """Make a request to Spansh's nearest endpoint with the values from spinboxes."""
        make_network_request(
            SPANSH_API_URL + "/nearest",
            params={
                "x": self.x_spinbox.value,
                "y": self.y_spinbox.value,
                "z": self.z_spinbox.value,
            },
            reply_callback=self._assign_from_reply,
        )

    def _assign_from_reply(self, reply: QtNetwork.QNetworkReply) -> None:
        """Decode the spansh JSON reply and display the data to the user."""
        data = json_from_network_req(reply)

        self.system_name_result_label.text = data["system"]["name"]
        self.distance_result_label.text = (
            format(data["system"]["distance"], ".2f").rstrip("0").rstrip(".") + " Ly"
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
