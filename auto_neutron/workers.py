# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import abc
import collections.abc
import contextlib
import logging
import subprocess  # noqa S404
import tempfile
import typing as t
from pathlib import Path

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.settings import General, Paths

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
