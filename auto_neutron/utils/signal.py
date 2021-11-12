# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
from contextlib import contextmanager

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class ReconnectingSignal:
    """Signal that can be easily disconnected and reconnected to the given slot."""

    def __init__(self, signal: QtCore.SignalInstance, slot: collections.abc.Callable):
        self.signal = signal
        self.slot = slot

    def connect(self) -> None:
        """Connect the signal to the slot."""
        self.signal.connect(self.slot)

    def disconnect(self) -> None:
        """Disconnect the signal from the slot."""
        self.signal.disconnect(self.slot)

    @contextmanager
    def temporarily_disconnect(self) -> collections.abc.Iterator[None]:
        """Disconnect the signal for the duration of the context manager, then reconnect it."""
        self.disconnect()
        yield
        self.connect()