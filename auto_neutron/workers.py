# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import abc
import collections.abc
import contextlib
import logging
import subprocess  # noqa S404
import tempfile
import typing as t
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.journal import Journal
from auto_neutron.settings import General, Paths
from auto_neutron.utils.route_plots import RouteList

log = logging.getLogger(__name__)


class Plotter(abc.ABC):
    """Provide the base interface for a game plotter."""

    def __init__(self, start_system: t.Optional[str] = None):
        if start_system is not None:
            self.update_system(start_system)

    @abc.abstractmethod
    def update_system(self, system: str, system_index: t.Optional[int] = None) -> t.Any:
        """Update the plotter with the given system."""
        ...

    def stop(self) -> t.Any:
        """Stop the plotter."""
        ...


class CopyPlotter(Plotter):
    """Plot by copying given systems on the route into the clipboard."""

    def update_system(self, system: str, system_index: t.Optional[int] = None) -> None:
        """Set the system clipboard to `system`."""
        QtWidgets.QApplication.clipboard().set_text(system)


class AhkPlotter(Plotter):
    """Plot through ahk by supplying the system through stdin to the ahk process."""

    def __init__(self, start_system: t.Optional[str] = None):
        super().__init__(start_system)
        self.process: t.Optional[subprocess.Popen] = None

    def _start_ahk(self) -> None:
        """
        Restart the ahk process.

        If the process terminates with 100ms (e.g. an invalid script file), a RuntimeError is raised.
        """
        self.stop()
        with self._create_temp_script_file() as script_path:
            log.info(f"Spawning AHK subprocess with {Paths.ahk=} {script_path=}")
            self.process = subprocess.Popen(  # noqa S603
                [Paths.ahk, str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(0.1)
                raise RuntimeError("AHK failed to start.")
        log.debug("Created AHK subprocess.")

    def update_system(self, system: str, system_index: t.Optional[int] = None) -> None:
        """Update the ahk script with `system`."""
        if self.process is None or self.process.poll() is not None:
            self._start_ahk()
        self.process.stdin.write(system.encode() + b"\n")
        self.process.stdin.flush()
        log.debug(f"Wrote {system!r} to AHK.")

    def stop(self) -> None:
        """Terminate the active process, if any."""
        if self.process is not None:
            log.debug("Terminating AHK subprocess.")
            self.process.terminate()
            self.process = None

    @staticmethod
    @contextlib.contextmanager
    def _create_temp_script_file() -> collections.abc.Iterator[Path]:
        """Create a temp file with the AHK script as its content."""
        temp_path = Path(
            tempfile.gettempdir(), tempfile.gettempprefix() + "_auto_neutron_script"
        )
        try:
            temp_path.write_text(General.script)
            yield temp_path
        finally:
            temp_path.unlink(missing_ok=True)


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
