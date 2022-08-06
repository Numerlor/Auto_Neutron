# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
from contextlib import contextmanager

from PySide6 import QtCore
from __feature__ import snake_case, true_property  # noqa: F401

if t.TYPE_CHECKING:
    import collections.abc


class ReconnectingSignal:
    """Signal that can be easily disconnected and reconnected to the given slot."""

    def __init__(self, signal: QtCore.SignalInstance, slot: collections.abc.Callable):
        self.signal = signal
        self.slot = slot
        self._disconnected = False
        self._depth = 0

    def connect(self) -> None:
        """Connect the signal to the slot."""
        if self._depth == 0:
            self.signal.connect(self.slot)
            self._disconnected = False

    def disconnect(self) -> None:
        """Disconnect the signal from the slot."""
        if not self._disconnected:
            self.signal.disconnect(self.slot)
            self._disconnected = True

    @contextmanager
    def temporarily_disconnect(self) -> collections.abc.Iterator[None]:
        """Disconnect the signal for the duration of the context manager, then reconnect it."""
        self.disconnect()
        self._depth += 1
        yield
        self._depth -= 1
        self.connect()
