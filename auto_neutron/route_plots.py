# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import abc
import atexit
import contextlib
import dataclasses
import logging
import subprocess  # noqa S404
import tempfile
import typing as t
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtNetwork, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron import settings
from auto_neutron.constants import AHK_TEMPLATE, SPANSH_API_URL
from auto_neutron.utils.network import (
    NetworkError,
    json_from_network_req,
    make_network_request,
)

if t.TYPE_CHECKING:
    import collections.abc

log = logging.getLogger(__name__)


class DataClassBase:
    """
    Provide indexed access to dataclass items.

    This class must be subclassed by a dataclass.
    """

    def __init__(self):
        raise RuntimeError(
            f"{self.__class__.__name__} cannot be instantiated directly."
        )

    def __setitem__(self, key: int, value: object) -> None:
        """Implement index based item assignment."""
        attr_name = dataclasses.fields(self)[key].name
        setattr(self, attr_name, value)


@dataclasses.dataclass
class ExactPlotRow(DataClassBase):
    """One row entry of an exact plot from the Spansh Galaxy Plotter."""

    system: str
    dist: float
    dist_rem: float
    refuel: bool
    neutron_star: bool

    def __eq__(self, other: ExactPlotRow | str):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> ExactPlotRow:
        """Create a row dataclass from the given csv row."""
        return ExactPlotRow(
            row[0],
            round(float(row[1]), 2),
            round(float(row[2]), 2),
            row[5][0] == "Y",
            row[6][0] == "Y",
        )

    def to_csv(self) -> list[str]:
        """Dump the row into a csv list of the appropriate size."""
        return [
            self.system,
            self.dist,
            self.dist_rem,
            "",
            "",
            "Yes" if self.refuel else "No",
            "Yes" if self.refuel else "No",
        ]


@dataclasses.dataclass
class NeutronPlotRow(DataClassBase):
    """One row entry of an exact plot from the Spansh Neutron Router."""

    system: str
    dist_to_arrival: float
    dist_rem: float
    jumps: int

    def __eq__(self, other: NeutronPlotRow | str):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> NeutronPlotRow:
        """Create a row dataclass from the given csv row."""
        return NeutronPlotRow(
            row[0], round(float(row[1]), 2), round(float(row[2]), 2), int(row[4])
        )

    def to_csv(self) -> list[str]:
        """Dump the row into a csv list of the appropriate size."""
        return [self.system, self.dist_to_arrival, self.dist_rem, "", self.jumps]


RouteList = list[ExactPlotRow] | list[NeutronPlotRow]


class Plotter(abc.ABC):
    """Provide the base interface for a game plotter."""

    def __init__(self, start_system: str | None = None):
        if start_system is not None:
            self.update_system(start_system)

    @abc.abstractmethod
    def update_system(self, system: str, system_index: int | None = None) -> None:
        """Update the plotter with the given system."""

    def refresh_settings(self) -> None:
        """Refresh the settings."""

    def stop(self) -> None:
        """Stop the plotter."""


class CopyPlotter(Plotter):
    """Plot by copying given systems on the route into the clipboard."""

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
            self.process = subprocess.Popen(  # noqa S603
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


def _decode_neutron_result(result: dict) -> list[NeutronPlotRow]:
    return [
        NeutronPlotRow(
            row["system"],
            round(row["distance_jumped"], 2),
            round(row["distance_left"], 2),
            row["jumps"],
        )
        for row in result["system_jumps"]
    ]


def _decode_exact_result(result: dict) -> list[ExactPlotRow]:
    return [
        ExactPlotRow(
            row["name"],
            round(row["distance"], 2),
            round(row["distance_to_destination"], 2),
            bool(row["must_refuel"]),  # Spansh returns 0 or 1
            row["has_neutron"],
        )
        for row in result["jumps"]
    ]


class SpanshReplyTracker:
    """Track the current reply from Spansh to allow termination."""

    def __init__(self, parent: QtCore.QObject):
        self._current_reply = None
        self._delay_timer = QtCore.QTimer(parent)
        self._delay_timer.single_shot_ = True
        self._timer_connection = None

    def _reply_callback(
        self,
        reply: QtNetwork.QNetworkReply,
        *,
        result_callback: collections.abc.Callable[[RouteList], t.Any],
        error_callback: collections.abc.Callable[[str], t.Any],
        delay_iterator: collections.abc.Iterator[float],
        result_decode_func: collections.abc.Callable[[dict], t.Any],
    ) -> None:
        """
        Handle a Spansh job reply, wait until a response is available and then return `result_decode_func` applied to it.

        When re-requesting for status, wait for `delay` seconds,
        where `delay` is the next value from the `delay_iterator`
        """
        self._reset_reply()
        try:
            job_response = json_from_network_req(reply, json_error_key="error")
        except NetworkError as e:
            if (
                e.error_type
                is QtNetwork.QNetworkReply.NetworkError.OperationCanceledError
            ):
                return

            if e.reply_error is not None:
                error_callback(
                    _("Received error from Spansh: {}").format(e.reply_error)
                )
            else:
                error_callback(
                    e.error_message
                )  # Fall back to Qt error message if spansh didn't respond
        except Exception as e:
            error_callback(str(e))
            logging.error(e)
        else:
            if job_response.get("status") == "queued":
                sec_delay = next(delay_iterator)
                log.debug(f"Re-requesting queued job result in {sec_delay} seconds.")
                self._delay_timer.interval = 2000
                self._timer_connection = self._delay_timer.timeout.connect(
                    partial(
                        self.make_request,
                        SPANSH_API_URL + "/results/" + job_response["job"],
                        finished_callback=partial(
                            self._reply_callback,
                            result_callback=result_callback,
                            error_callback=error_callback,
                            delay_iterator=delay_iterator,
                            result_decode_func=result_decode_func,
                        ),
                    ),
                )
                self._delay_timer.start()
            elif job_response.get("result") is not None:
                log.debug("Received finished neutron job.")
                result_callback(result_decode_func(job_response["result"]))
            else:
                error_callback(_("Received invalid response from Spansh."))

    def spansh_exact_callback(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Callback to call the result callback with an ExactPlotRow list."""  # noqa: D401
        self._reply_callback(*args, **kwargs, result_decode_func=_decode_exact_result)

    def spansh_neutron_callback(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Callback to call the result callback with a NeutronPlotRow list."""  # noqa: D401
        self._reply_callback(*args, **kwargs, result_decode_func=_decode_neutron_result)

    def make_request(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Make a network request and store the result reply."""
        self._current_reply = make_network_request(*args, **kwargs)

    def abort(self) -> None:
        """Abort the current request."""
        log.debug("Aborting route plot request.")
        if self._current_reply is not None:
            self._current_reply.abort()
        self._delay_timer.stop()

    def _reset_reply(self) -> None:
        """Reset the reply and disconnect the timer from the old make_request."""
        self._current_reply = None
        if self._timer_connection is not None:
            self._delay_timer.disconnect(self._timer_connection)
