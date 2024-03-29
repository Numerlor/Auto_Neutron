# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import contextlib
import json
import logging
import typing as t
from functools import partial

from PySide6 import QtCore
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.constants import STATUS_PATH
from auto_neutron.route import Route

if t.TYPE_CHECKING:
    import collections.abc

    from auto_neutron.game_state import Location
    from auto_neutron.journal import Journal

log = logging.getLogger(__name__)


class _WorkerBase(QtCore.QObject):
    """The base class used for workers that advance generators at a given interval."""

    def __init__(
        self,
        parent: QtCore.QObject,
        generator: collections.abc.Generator,
        interval: int,
    ):
        super().__init__(parent)
        self._generator = generator
        self._timer = QtCore.QTimer(self)
        self._timer.interval = interval
        self._timer.timeout.connect(partial(next, self._generator))
        self._stopped = False

    def start(self) -> None:
        """Start the worker to tail the journal file."""
        log.debug("Starting GameWorker.")
        if self._stopped:
            raise RuntimeError("Can't restart a stopped worker.")
        self._timer.start()

    def stop(self) -> None:
        """Stop the worker from tailing the journal file."""
        log.debug(f"Stopping {self.__class__.__name__}.")
        self._timer.stop()
        self._generator.close()
        self._stopped = True


class GameWorker(_WorkerBase):
    """Handle dispatching route signals from the journal's tailer."""

    new_system_index_sig = QtCore.Signal(int)
    route_end_sig = QtCore.Signal(int)

    def __init__(self, parent: QtCore.QObject, route: Route | None, journal: Journal):
        super().__init__(parent, journal.tail(), 500)
        self.route = route
        self._journal_connection = journal.system_sig.connect(self.emit_next_system)

    @QtCore.Slot(object)
    def emit_next_system(self, location: Location) -> None:
        """Emit the next system in the route and its index if location is in the route, or the end of route signal."""
        if self.route is None:
            return

        with contextlib.suppress(ValueError):
            new_index = self.route.system_index(location.name) + 1
            if new_index < len(self.route.entries):
                self.new_system_index_sig.emit(new_index)
            else:
                if settings.General.loop_routes:
                    self.new_system_index_sig.emit(0)
                else:
                    self.route_end_sig.emit(new_index)

    def stop(self) -> None:
        """Disconnect the journal system signal."""
        super().stop()
        self.disconnect(self._journal_connection)


class StatusWorker(_WorkerBase):
    """Follow the status file and dispatch `status_signal` from its contents."""

    status_signal = QtCore.Signal(dict)

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent, self.read_status(), 250)

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
