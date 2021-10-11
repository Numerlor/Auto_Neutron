# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import collections.abc
import contextlib
import json
import logging
import subprocess  # noqa S404
from functools import partial

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.constants import STATUS_PATH
from auto_neutron.journal import Journal
from auto_neutron.route_plots import RouteList

log = logging.getLogger(__name__)


class GameWorker(QtCore.QObject):
    """Handle dispatching route signals from the journal's tailer."""

    next_system_sig = QtCore.Signal(str, int)
    route_end_sig = QtCore.Signal()

    def __init__(self, route: RouteList, journal: Journal):
        super().__init__()
        self._generator = journal.tail()
        self._timer = QtCore.QTimer()
        self._timer.interval = 250
        self._timer.timeout.connect(partial(next, self._generator))
        self._stopped = False
        self.route = route
        journal.system_sig.connect(self._emit_next_system)

    def _emit_next_system(self, system_name: str) -> None:
        """Emit the next system in the route and its index, or end of route."""
        with contextlib.suppress(ValueError):
            new_system_index = self.route.index(system_name) + 1
            try:
                self.next_system_sig.emit(
                    self.route[new_system_index], new_system_index
                )
            except IndexError:
                self.route_end_sig.emit()

    def start(self) -> None:
        """Start the worker to tail the journal file."""
        if self._stopped:
            raise RuntimeError("Can't restart a stopped worker.")
        self._timer.start()

    def stop(self) -> None:
        """Stop the worker from tailing the journal file."""
        self._timer.stop()
        self._generator.close()
        self._stopped = True


class StatusWorker(QtCore.QObject):
    """Follow the status file and dispatch `status_signal` from its contents."""

    status_signal = QtCore.Signal(dict)

    def __init__(self):
        super().__init__()
        self._generator = self.read_status()
        self._timer = QtCore.QTimer()
        self._timer.interval = 250
        self._timer.timeout.connect(partial(next, self._generator))
        self._running = False

    def start(self) -> None:
        """Start the worker to follow the status file."""
        if self._running:
            raise RuntimeError("Worker already started")
        self._running = True
        self._generator = self.read_status()
        self._timer.start()

    def stop(self) -> None:
        """Stop following the status file."""
        self._timer.stop()
        self._generator.close()
        self._running = False

    def read_status(self) -> collections.abc.Generator[None, None, None]:
        """Emit status_signal with the status dict on every status file change."""
        last_content = None
        with open(STATUS_PATH, encoding="utf8") as file:
            while True:
                file.seek(0)
                content = file.read()
                if content and content != last_content:
                    self.status_signal.emit(json.loads(content))
                    last_content = content
                yield
