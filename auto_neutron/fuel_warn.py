# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import logging
import typing as t

from PySide6 import QtCore, QtMultimedia, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings

if t.TYPE_CHECKING:
    from auto_neutron.hub import GameState

log = logging.getLogger(__name__)

IN_SUPERCRUISE_FLAG = 1 << 4
FSD_COOLDOWN_FLAG = 1 << 18

player = QtMultimedia.QMediaPlayer()
player.audio_output = audio_output = QtMultimedia.QAudioOutput()


class FuelWarn:
    """Warn visually through the task bar and through audio when fuel is below set threshold."""

    def __init__(self, game_state: GameState, alert_widget: QtWidgets.QWidget):
        self._warned = False
        self._alert_widget = alert_widget
        self._game_state = game_state

    def warn(self, status_dict: dict) -> None:
        """Execute alert when in supercruise, on FSD cool down and fuel is below threshold."""
        if not status_dict or "Fuel" not in status_dict:
            # Sometimes we get empty JSON,
            # or when the game is shut down it only contains data up to flags.
            return

        status_flags = status_dict["Flags"]
        fuel_threshold = (
            self._game_state.ship.tank_size * settings.Alerts.threshold / 100
        )
        if (
            not self._warned
            and status_flags & IN_SUPERCRUISE_FLAG
            and status_flags & FSD_COOLDOWN_FLAG
            and status_dict["Fuel"]["FuelMain"] < fuel_threshold
        ):
            log.info(
                f"Executing alert, {fuel_threshold=} ship_fuel={status_dict['Fuel']['FuelMain']}"
            )
            self._execute_alert()
            self._warned = True

        elif self._warned and status_dict["Fuel"]["FuelMain"] > fuel_threshold:
            log.debug("Resetting warned state.")
            self._warned = False

    def _execute_alert(self) -> None:
        """
        Execute an alert.

        If the audio alerts are enable and there is no path defined, use the default system alert,
        otherwise if the user provided a path, play it through the global QMediaPlayer instance.

        If the visual alert is enabled, attempt to flash the taskbar icon for 5 seconds.
        """
        if settings.Alerts.audio:
            if settings.Paths.alert_sound:
                new_url = QtCore.QUrl.from_local_file(str(settings.Paths.alert_sound))
                if new_url != player.source:
                    player.source = new_url
                log.info(f"Playing file {settings.Paths.alert_sound} for alert.")
                player.play()

            else:
                QtWidgets.QApplication.instance().beep()

        if settings.Alerts.visual:
            QtWidgets.QApplication.instance().alert(self._alert_widget, 5000)