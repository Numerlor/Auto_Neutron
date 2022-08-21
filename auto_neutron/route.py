# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import abc
import csv
import dataclasses
import itertools
import logging
import typing as t
from operator import attrgetter, itemgetter
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
class GenericPlotRow(SystemEntry):
    """Plot row of an unknown route or a route with only system names."""

    csv_header: t.ClassVar = ("System Name",)
    system: str

    @classmethod
    def from_csv_row(cls, row: list[str]) -> te.Self:  # noqa: D102
        return cls(row[0])

    def to_csv(self) -> list[str]:  # noqa: D102
        return [self.system]

    def from_json(cls, json: dict) -> te.Self:  # noqa: D102
        raise NotImplementedError("Can't create generic plot rows.")


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


@dataclasses.dataclass
class RoadToRichesRow(SystemEntry):
    """
    One row entry of a road to riches  from the Spansh Road 2 Riches plotter.

    Can't be directly created from csv rows because information of a single plot row is spread across
    multiple csv rows.
    """

    csv_header: t.ClassVar = (
        "System Name",
        "Body Name",
        "Body Subtype",
        "Is Terraformable",
        "Distance To Arrival",
        "Estimated Scan Value",
        "Estimated Mapping Value",
        "Jumps",
    )

    system: str
    total_scan_value: int
    total_mapping_value: int
    jumps: int

    @classmethod
    def from_csv_row(cls, row: list[str]) -> te.Self:  # noqa: D102
        raise NotImplementedError("Can't create RoadToRichesRow from a single csv row.")

    @classmethod
    def from_json(cls, json: dict) -> te.Self:  # noqa: D102
        ...

    def to_csv(self) -> list[str]:  # noqa: D102
        return [
            self.system,
            "",
            "",
            "",
            "",
            self.total_scan_value,
            self.total_mapping_value,
            self.jumps,
        ]


_header_to_row_type: dict[tuple[str, ...], type[SystemEntry]] = {
    type_.csv_header: type_
    for type_ in (GenericPlotRow, NeutronPlotRow, ExactPlotRow, RoadToRichesRow)
}
RowT = t.TypeVar("RowT", bound=SystemEntry)


class Route(abc.ABC, t.Generic[RowT]):
    """
    A route of `SystemEntry` entries.

    When instantiated, an appropriate subclass is returned that can work with row specific data.
    """

    _row_type_to_route_class = {}
    row_type: type[RowT] | None = None

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, "__orig_bases__"):
            cls._row_type_to_route_class[cls.__orig_bases__[0].__args__[0]] = cls
            cls.row_type = cls.__orig_bases__[0].__args__[0]

    def __init__(self, route: list[RowT]):
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
    @t.final
    def from_csv_file(cls, path: Path) -> te.Self:
        """Create an instance from a CSV file at `path`."""
        with path.open(encoding="utf8", newline="") as csv_file:
            reader = more_itertools.peekable(csv.reader(csv_file, strict=True))
            header = tuple(reader.peek())
            try:
                row_type = _header_to_row_type[header]
                next(reader)  # Header was valid, shouldn't be included in result.
            except KeyError:
                # unknown route type, fall back to generic route.
                row_type = GenericPlotRow

            cls = cls._row_type_to_route_class[row_type]
            log.info(f"CSV file at {path} is of type {row_type.__name__}.")
            route = cls.route_rows_from_csv(reader)

        return cls(route)

    @classmethod
    def route_rows_from_csv(
        cls,
        reader: more_itertools.peekable[list[str]],
    ) -> list[RowT]:
        """Get route rows for `row_type` from `reader`."""
        return list(
            more_itertools.unique_justseen(
                (cls.row_type.from_csv_row(row) for row in filter(None, reader)),
                key=attrgetter("system"),
            )
        )

    @t.final
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


class GenericRoute(Route[GenericPlotRow]):
    """Unknown route with only system names."""

    @classmethod
    def from_json(cls, json_dict: dict) -> te.Self:  # noqa: D102
        raise NotImplementedError("Generic routes can't be created from json.")


class NeutronRoute(Route[NeutronPlotRow]):
    """A route of the Spansh neutron plotter."""

    @classmethod
    def from_json(cls, json_dict: dict) -> NeutronRoute:  # noqa: D102
        route = [
            NeutronPlotRow.from_json(system_json)
            for system_json in json_dict["system_jumps"]
        ]
        return NeutronRoute(route)

    @property
    def total_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries)

    @property
    def remaining_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries[self.index :])


class ExactRoute(Route[ExactPlotRow]):
    """A route of the Spansh galaxy plotter."""

    @classmethod
    def from_json(cls, json_dict: dict) -> ExactRoute:  # noqa: D102
        route = [
            ExactPlotRow.from_json(system_json) for system_json in json_dict["jumps"]
        ]
        return ExactRoute(route)


class RoadToRichesRoute(Route[RoadToRichesRow]):
    """A route of the Spansh Road 2 Riches plotter."""

    @classmethod
    def route_rows_from_csv(
        cls,
        reader: more_itertools.peekable[list[str]],
    ) -> list[RowT]:
        """
        Get the route from `reader`.

        All successive bodies in a single system are added to a single `RoadToRichesRow`.
        """
        route = []

        for system_name, bodies in itertools.groupby(reader, itemgetter(0)):
            bodies = list(bodies)
            jumps = int(bodies[0][7])
            total_scan_value = 0
            total_mapping_value = 0
            for body in bodies:
                total_scan_value += int(body[5])
                total_mapping_value += int(body[6])

            route.append(
                RoadToRichesRow(
                    system_name, total_scan_value, total_mapping_value, jumps
                )
            )
        return route

    @classmethod
    def from_json(cls, json_dict: dict) -> te.Self:  # noqa: D102
        ...

    @property
    def total_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries)

    @property
    def remaining_jumps(self) -> int:  # noqa: D102
        return sum(entry.jumps for entry in self.entries[self.index :])
