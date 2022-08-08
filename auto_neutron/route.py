# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import abc
import collections.abc
import csv
import dataclasses
import logging
import typing as t
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtNetwork
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.utils.network import (
    NetworkError,
    json_from_network_req,
    make_network_request,
)

if t.TYPE_CHECKING:
    import typing_extensions as te

log = logging.getLogger(__name__)


class SystemEntry(abc.ABC):
    """
    Provide indexed access to dataclass items.

    This class must be subclassed by a dataclass.
    """

    csv_header: t.ClassVar[tuple[str, ...]] = None
    system: str

    def __eq__(self, other: SystemEntry | str):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)

    def __setitem__(self, key: int, value: object) -> None:
        """Implement index based item assignment."""
        attr_name = dataclasses.fields(self)[key].name
        setattr(self, attr_name, value)

    @classmethod
    @abc.abstractmethod
    def from_csv_row(cls, row: list[str]) -> te.Self:
        """Create an instance from the `row` list of strings from csv."""

    @classmethod
    @abc.abstractmethod
    def from_json(cls, json: dict) -> te.Self:
        """Create an instance from the `json` json dict."""

    @abc.abstractmethod
    def to_csv(self) -> list[str]:
        """Create a list of the fields as csv."""


@dataclasses.dataclass
class ExactPlotRow(SystemEntry):
    """One row entry of an exact plot from the Spansh Galaxy Plotter."""

    csv_header: t.ClassVar = (
        "System Name",
        "Distance",
        "Distance Remaining",
        "Fuel Left",
        "Fuel Used",
        "Refuel",
        "Neutron Star",
    )

    system: str
    dist: float
    dist_rem: float
    refuel: bool
    neutron_star: bool

    @classmethod
    def from_csv_row(cls, row: list[str]) -> te.Self:  # noqa: D102
        return cls(
            row[0],
            round(float(row[1]), 2),
            round(float(row[2]), 2),
            row[5][0] == "Y",
            row[6][0] == "Y",
        )

    @classmethod
    def from_json(cls, json: dict) -> te.Self:  # noqa: D102
        return cls(
            json["name"],
            round(json["distance"], 2),
            round(json["distance_to_destination"], 2),
            bool(json["must_refuel"]),  # Spansh returns 0 or 1
            json["has_neutron"],
        )

    def to_csv(self) -> list[str]:  # noqa: D102
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
class NeutronPlotRow(SystemEntry):
    """One row entry of an exact plot from the Spansh Neutron Router."""

    csv_header: t.ClassVar = (
        "System Name",
        "Distance To Arrival",
        "Distance Remaining",
        "Neutron Star",
        "Jumps",
    )

    system: str
    dist_to_arrival: float
    dist_rem: float
    jumps: int

    @classmethod
    def from_csv_row(cls, row: list[str]) -> te.Self:  # noqa: D102
        return cls(
            row[0], round(float(row[1]), 2), round(float(row[2]), 2), int(row[4])
        )

    @classmethod
    def from_json(cls, json: dict) -> te.Self:  # noqa: D102
        return cls(
            json["system"],
            round(json["distance_jumped"], 2),
            round(json["distance_left"], 2),
            json["jumps"],
        )

    def to_csv(self) -> list[str]:  # noqa: D102
        return [self.system, self.dist_to_arrival, self.dist_rem, "", self.jumps]


_header_to_row_type: dict[tuple[str, ...], type[SystemEntry]] = {
    type_.csv_header: type_ for type_ in (NeutronPlotRow, ExactPlotRow)
}
RowT = t.TypeVar("RowT", bound=SystemEntry)


class Route(t.Generic[RowT]):
    """
    A route of `SystemEntry` entries.

    When instantiated, an appropriate subclass is returned that can work with row specific data.
    """

    _row_type_to_route_class = {}

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, "__orig_bases__"):
            cls._row_type_to_route_class[cls.__orig_bases__[0].__args__[0]] = cls

    def __new__(cls, row_type: type[RowT], *args, **kwargs) -> te.Self:  # noqa: D102
        return object.__new__(cls._row_type_to_route_class[row_type])

    def __init__(self, row_type: type[RowT], route: list[RowT]):
        self.row_type = row_type
        self.entries = route
        self.index = 0

    @property
    def total_jumps(self) -> int:
        """The total jumps in this route."""  # noqa: D401
        return len(self.entries)

    @property
    def remaining_jumps(self) -> int:
        """The remaining jumps of this route."""  # noqa: D401
        return len(self.entries) - self.index

    @property
    def current_system(self) -> str:
        """The current system in the route."""  # noqa: D401
        return self.entries[self.index].system

    @classmethod
    def from_csv_file(cls, path: Path) -> te.Self:
        """Create an instance from a CSV file at `path`."""
        with path.open(encoding="utf8", newline="") as csv_file:
            reader = csv.reader(csv_file, strict=True)
            row_type = _header_to_row_type[tuple(next(reader))]
            log.info(f"CSV file at {path} is of type {row_type.__name__}.")
            route = [row_type.from_csv_row(row) for row in reader]

        return cls(row_type, route)

    def to_csv_file(self, path: Path) -> None:
        """Save this route to a CSV file at `path`."""
        with path.open("w", encoding="utf8", newline="") as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
            writer.writerow(self.row_type.csv_header)
            writer.writerows(row.to_csv() for row in self.entries)

    @classmethod
    def from_json(cls, json_dict: dict) -> te.Self:
        """Create an instance from the `json_dict` json."""
        raise NotImplementedError


class NeutronRoute(Route[NeutronPlotRow]):
    """A route of the Spansh neutron plotter."""

    @classmethod
    def from_json(cls, json_dict: dict) -> te.Self:  # noqa: D102
        route = [
            NeutronPlotRow.from_json(system_json)
            for system_json in json_dict["system_jumps"]
        ]
        return cls(NeutronPlotRow, route)

    @property
    def total_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries)

    @property
    def remaining_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries[self.index :])


class ExactRoute(Route[ExactPlotRow]):
    """A route of the Spansh galaxy plotter."""

    @classmethod
    def from_json(cls, json_dict: dict) -> te.Self:  # noqa: D102
        route = [
            ExactPlotRow.from_json(system_json) for system_json in json_dict["jumps"]
        ]
        return cls(ExactPlotRow, route)


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
        result_callback: collections.abc.Callable[[Route], t.Any],
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
        self._reply_callback(*args, **kwargs, result_decode_func=ExactRoute.from_json)

    def spansh_neutron_callback(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Callback to call the result callback with a NeutronPlotRow list."""  # noqa: D401
        self._reply_callback(*args, **kwargs, result_decode_func=NeutronRoute.from_json)

    def make_request(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Make a network request and store the result reply."""
        self.abort()
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
