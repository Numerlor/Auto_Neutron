# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import abc
import collections.abc
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
# Can't use true_property because QTimer's single_shot method turns into a property for is_single_shot
from __feature__ import snake_case  # noqa F401
from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.settings import General, Paths
from auto_neutron.utils.network import json_from_network_req, make_network_request

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

    def __eq__(self, other: t.Union[ExactPlotRow, str]):
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


@dataclasses.dataclass
class NeutronPlotRow(DataClassBase):
    """One row entry of an exact plot from the Spansh Neutron Router."""

    system: str
    dist_to_arrival: float
    dist_rem: float
    jumps: int

    def __eq__(self, other: t.Union[NeutronPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> NeutronPlotRow:
        """Create a row dataclass from the given csv row."""
        return NeutronPlotRow(
            row[0], round(float(row[1]), 2), round(float(row[2]), 2), int(row[4])
        )


RouteList = t.Union[list[ExactPlotRow], list[NeutronPlotRow]]


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
        self.process: t.Optional[subprocess.Popen] = None
        super().__init__(start_system)

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


def _spansh_job_callback(
    reply: QtNetwork.QNetworkReply,
    *,
    result_callback: collections.abc.Callable[[list[NeutronPlotRow]], t.Any],
    delay_iterator: collections.abc.Iterator[float],
    result_decode_func: collections.abc.Callable[[dict], t.Any],
) -> None:
    """
    Handle a Spansh job reply, wait until a response is available and then return `result_decode_func` applied to it.

    When re-requesting for status, wait for `delay` seconds,
    where `delay` is the next value from the `delay_iterator`
    """
    job_response = json_from_network_req(reply)
    if job_response.get("status") == "queued":
        sec_delay = next(delay_iterator)
        log.debug(f"Re-requesting queued job result in {sec_delay} seconds.")
        QtCore.QTimer.single_shot(
            sec_delay * 1000,
            partial(
                make_network_request,
                SPANSH_API_URL + "/results/" + job_response["job"],
                reply_callback=partial(
                    _spansh_job_callback,
                    result_callback=result_callback,
                    delay_iterator=delay_iterator,
                    result_decode_func=result_decode_func,
                ),
            ),
        )
    elif job_response.get("result") is not None:
        log.debug("Received finished neutron job.")
        result_callback(result_decode_func(job_response["result"]))
    else:
        raise RuntimeError(
            "Received invalid JSON response from Spansh neutron route.",
            job_response,
        )


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


spansh_neutron_callback = partial(
    _spansh_job_callback, result_decode_func=_decode_neutron_result
)
spansh_exact_callback = partial(
    _spansh_job_callback, result_decode_func=_decode_exact_result
)
