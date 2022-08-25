# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import abc
import atexit
import contextlib
import logging
import subprocess
import tempfile
import typing as t
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.constants import AHK_TEMPLATE

if t.TYPE_CHECKING:
    import collections.abc

log = logging.getLogger(__name__)


class Plotter(abc.ABC):
    """Provide the base interface for a game plotter."""

    def __init__(self, start_system: str | None = None):
        if start_system is not None:
            self.update_system(start_system)

    @QtCore.Slot(str, int)
    @QtCore.Slot(str)
    @abc.abstractmethod
    def update_system(self, system: str, system_index: int | None = None) -> None:
        """Update the plotter with the given system."""

    def refresh_settings(self) -> None:
        """Refresh the settings."""

    def stop(self) -> None:
        """Stop the plotter."""


class CopyPlotter(Plotter):
    """Plot by copying given systems on the route into the clipboard."""

    @QtCore.Slot(str, int)
    @QtCore.Slot(str)
    def update_system(self, system: str, system_index: int | None = None) -> None:
        """Set the system clipboard to `system`."""
        log.info(f"Pasting {system!r} to clipboard.")
        QtWidgets.QApplication.clipboard().set_text(system)


class AhkPlotter(Plotter):
    """Plot through ahk by supplying the system through stdin to the ahk process."""

    def __init__(self, start_system: str | None = None):
        self.process: subprocess.Popen | None = None
        self._used_script = None
        self._used_ahk_path = None
        self._used_hotkey = None
        self._last_system = None
        super().__init__(start_system)

    def _start_ahk(self) -> None:
        """
        Restart the ahk process.

        If the process terminates within 100ms (e.g. an invalid script file), a RuntimeError is raised.
        """
        self.stop()
        with self._create_temp_script_file() as script_path:
            log.info(
                f"Spawning AHK subprocess with {settings.Paths.ahk=} {script_path=}"
            )
            if settings.Paths.ahk is None or not settings.Paths.ahk.exists():
                log.error("AHK path not set or invalid.")
                return
            self.process = subprocess.Popen(
                [settings.Paths.ahk, script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(0.1)
                raise RuntimeError("AHK failed to start.")
        self._used_ahk_path = settings.Paths.ahk
        self._used_script = settings.AHK.get_script()
        self._used_hotkey = settings.AHK.bind
        atexit.register(self.process.terminate)
        log.debug("Created AHK subprocess.")

    @QtCore.Slot(str, int)
    @QtCore.Slot(str)
    def update_system(self, system: str, system_index: int | None = None) -> None:
        """Update the ahk script with `system`."""
        if self.process is None or self.process.poll() is not None:
            self._start_ahk()
        self._last_system = system
        self.process.stdin.write(system.encode() + b"\n")
        self.process.stdin.flush()
        log.debug(f"Wrote {system!r} to AHK.")

    def refresh_settings(self) -> None:
        """Restart AHK on setting change."""
        if (
            settings.Paths.ahk != self._used_ahk_path
            or settings.AHK.get_script() != self._used_script
            or settings.AHK.bind != self._used_hotkey
        ):
            self._start_ahk()
            self.update_system(self._last_system)

    def stop(self) -> None:
        """Terminate the active process, if any."""
        if self.process is not None:
            log.debug("Terminating AHK subprocess.")
            self.process.terminate()
            atexit.unregister(self.process.terminate)
            self.process = None

    @contextlib.contextmanager
    def _create_temp_script_file(self) -> collections.abc.Iterator[Path]:
        """Create a temp file with the AHK script as its content."""
        temp_path = Path(
            tempfile.gettempdir(), tempfile.gettempprefix() + "_auto_neutron_script"
        )
        try:
            temp_path.write_text(
                AHK_TEMPLATE.substitute(
                    hotkey=settings.AHK.bind, user_script=settings.AHK.get_script()
                )
            )
            yield temp_path
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                # There probably was an error in AHK and it's still holding the file open.
                log.warning(f"Unable to delete temp file at {temp_path}.")
