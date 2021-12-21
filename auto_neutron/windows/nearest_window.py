# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from PySide6 import QtNetwork, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.utils.network import json_from_network_req, make_network_request
from auto_neutron.windows.gui.nearest_window import NearestWindowGUI


class NearestWindow(NearestWindowGUI):
    """Provide a UI to Spansh's nearest API and let the user get the result through the provided buttons."""

    def __init__(self, parent: QtWidgets.QWidget, x: float, y: float, z: float):
        super().__init__(parent)

        self.x_spinbox.value = x
        self.y_spinbox.value = y
        self.z_spinbox.value = z
        self.search_button.pressed.connect(self._make_nearest_request)

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
