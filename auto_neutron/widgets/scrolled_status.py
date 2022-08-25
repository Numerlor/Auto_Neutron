# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.widgets import PlainTextScroller


class ScrolledStatus(PlainTextScroller):
    """Scrolling status widget for providing information to the user with a timeout."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        text: str = "",
        fade_width: int = 30,
        scroll_step: float = 1 / 4,
        scroll_interval: int = 4,
    ):
        super().__init__(
            parent,
            text=text,
            fade_width=fade_width,
            scroll_step=scroll_step,
            scroll_interval=scroll_interval,
        )
        self._hide_timer = QtCore.QTimer(self)
        self._hide_timer.single_shot_ = True
        self._hide_timer.timeout.connect(self._reset_text)

        self._hovered = False
        self._scheduled_reset = False

    def show_message(self, message: str, duration: int = 0) -> None:
        """
        Show message for `duration` ms.

        If duration is 0, keep showing until the next call to this function.
        """
        self._hide_timer.stop()
        if duration:
            self._hide_timer.interval = duration
            self._hide_timer.start()

        self.text = message

    @QtCore.Slot()
    def _reset_text(self) -> None:
        """Reset the text if not hovered, or schedule a reset for when the user leaves the widget if hovered."""
        if not self._hovered:
            self.text = ""
        else:
            self._scheduled_reset = True

    def _force_reset_text(self) -> None:
        """Force text reset, disable hide timer and scheduled reset."""
        self.text = ""
        self._hide_timer.stop()
        self._scheduled_reset = False

    def mouse_release_event(self, event: QtGui.QMouseEvent) -> None:
        """Reset text on click."""
        super().mouse_release_event(event)
        self._force_reset_text()

    def enter_event(self, event: QtGui.QEnterEvent) -> None:
        """Set hovered status to true."""
        super().enter_event(event)
        self._hovered = True

    def leave_event(self, event: QtGui.QEnterEvent) -> None:
        """Reset hovered status to false, and reset text if its reset is scheduled."""
        super().leave_event(event)
        self._hovered = False
        if self._scheduled_reset:
            self.text = ""
            self._scheduled_reset = False
