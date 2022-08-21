# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import abc
import csv
import dataclasses
import logging
import typing as t
from pathlib import Path

import more_itertools

if t.TYPE_CHECKING:
    import typing_extensions as te

log = logging.getLogger(__name__)


class SystemEntry(abc.ABC):
    """
    Provide indexed access to dataclass items.

    This class must be subclassed by a dataclass.
    """

    csv_header: t.ClassVar[tuple[str, ...]] = None  # type: ignore
    system: str

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

    def to_csv(self) -> list:  # noqa: D102
        return [
            self.system,
            self.dist,
            self.dist_rem,
            "",
            "",
            "Yes" if self.refuel else "No",
            "Yes" if self.neutron_star else "No",
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

    def to_csv(self) -> list:  # noqa: D102
        return [self.system, self.dist_to_arrival, self.dist_rem, "", self.jumps]


_header_to_row_type: dict[tuple[str, ...], type[SystemEntry]] = {
    type_.csv_header: type_ for type_ in (NeutronPlotRow, ExactPlotRow)
}
RowT = t.TypeVar("RowT", bound=SystemEntry)


class Route(abc.ABC, t.Generic[RowT]):
    """
    A route of `SystemEntry` entries.

    When instantiated, an appropriate subclass is returned that can work with row specific data.
    """

    _row_type_to_route_class = {}

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, "__orig_bases__"):
            cls._row_type_to_route_class[cls.__orig_bases__[0].__args__[0]] = cls

    def __new__(cls, row_type: type[RowT], *args, **kwargs) -> te.Self:  # noqa: D102
        try:
            return object.__new__(cls._row_type_to_route_class[row_type])
        except KeyError:
            raise ValueError("Row type without a registered subclass.")

    def __init__(self, row_type: type[RowT], route: list[RowT]):
        self.row_type = row_type
        self.entries = route
        self._route_indices: dict[str, list[int]] = {}
        self._index = 0
        self.update_indices()

    @property
    def index(self) -> int:
        """The route's current index."""  # noqa: D401
        return self._index

    @index.setter
    def index(self, new_index: int) -> None:
        """
        Set the index to `new_index` clamped to the route's maximum.

        The new index should be positive.
        """
        self._index = min(len(self.entries) - 1, new_index)

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

    def system_index(self, system: str) -> int:
        """
        Get the index of `system`.

        If the system appears multiple times in the route, try to get the find the first entry after the current index,
        if none is found return the index of the first occurrence.
        """
        if (indices := self._route_indices.get(system)) is None:
            raise ValueError(f"System {system!r} not in route.")

        try:
            return more_itertools.first(
                index for index in indices if index > self.index
            )
        except ValueError:
            return indices[0]

    def update_indices(self) -> None:
        """Update system indices used in `system_index`."""
        self._route_indices.clear()
        for index, row in enumerate(self.entries):
            self._route_indices.setdefault(row.system, []).append(index)

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
    @abc.abstractmethod
    def from_json(cls, json_dict: dict) -> te.Self:
        """Create an instance from the `json_dict` json."""


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
