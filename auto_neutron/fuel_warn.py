# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
import typing as t

from PySide6 import QtCore, QtMultimedia, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings

if t.TYPE_CHECKING:
    from auto_neutron.journal import Journal

log = logging.getLogger(__name__)

IN_SUPERCRUISE_FLAG = 1 << 4
FSD_COOLDOWN_FLAG = 1 << 18


class FuelWarn(QtCore.QObject):
    """Warn visually through the task bar and through audio when fuel is below set threshold."""

    def __init__(
        self,
        parent: QtCore.QObject,
        alert_widget: QtWidgets.QWidget,
    ):
        super().__init__(parent)
        self._warned = False
        self._alert_widget = alert_widget
        self._journal = None
        self.player = QtMultimedia.QMediaPlayer(self)
        self.player.audio_output = self.audio_output = QtMultimedia.QAudioOutput(self)

    def set_journal(self, journal: Journal) -> None:
        """Set the journal to get the ship values from."""
        self._journal = journal

    def warn(self, status_dict: dict) -> None:
        """Execute alert when in supercruise, on FSD cool down and fuel is below threshold."""
        if self._journal.ship is None or "Fuel" not in status_dict:
            # Sometimes we get empty JSON,
            # or when the game is shut down it only contains data up to flags.
            return

        status_flags = status_dict["Flags"]
        fuel_threshold = (
            self._journal.ship.fsd.max_fuel_usage * settings.Alerts.threshold / 100
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
        log.info("Attempting to execute fuel alert.")
        if settings.Alerts.audio:
            if settings.Paths.alert_sound:
                new_url = QtCore.QUrl.from_local_file(str(settings.Paths.alert_sound))
                if new_url != self.player.source:
                    self.player.source = new_url
                log.info(f"Playing file {settings.Paths.alert_sound} for alert.")
                self.player.play()

            else:
                QtWidgets.QApplication.instance().beep()
                log.info("Application beep for audi alert.")

        if settings.Alerts.visual:
            QtWidgets.QApplication.instance().alert(self._alert_widget, 5000)
            log.info("Executed flash alert.")
