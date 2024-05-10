# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import dataclasses
import typing as t
from functools import cached_property

from PySide6 import QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.route import (
    ExactPlotRow,
    GenericPlotRow,
    NeutronPlotRow,
    RoadToRichesRow,
    SystemEntry,
)
from auto_neutron.utils.utils import N_
from auto_neutron.windows.gui.delegates import (
    CheckBoxDelegate,
    DoubleSpinBoxDelegate,
    SpinBoxDelegate,
)

T = t.TypeVar("T")


@dataclasses.dataclass(kw_only=True)
class HeaderSection:
    """A single section of a table header."""

    text: str
    has_jumps: bool = False
    resize_mode: QtWidgets.QHeaderView.ResizeMode = (
        QtWidgets.QHeaderView.ResizeMode.Fixed
    )
    delegate_type: type[QtWidgets.QAbstractItemDelegate] = QtWidgets.QStyledItemDelegate


class RouteTableHeader:
    """
    Header for a table of a certain route type.

    Must be subclassed with filled `_header_sections` to be used.
    """

    _header_sections: t.ClassVar[tuple[HeaderSection, ...]]

    def __init__(self, table: QtWidgets.QTableWidget):
        self._table = table
        self._remaining_jumps: int | None = None
        self._total_jumps: int | None = None
        self._delegates = []

    def initialize_headers(self) -> None:
        """Initialize the table's columns and headers."""
        self._table.column_count = self.column_count
        for column in range(self.column_count):
            if self._table.horizontal_header_item(column) is None:
                self._table.set_horizontal_header_item(
                    column, QtWidgets.QTableWidgetItem()
                )

        header = self._table.horizontal_header()
        for index, header_section in enumerate(self._header_sections):
            header.set_section_resize_mode(index, header_section.resize_mode)
            delegate = header_section.delegate_type()
            self._table.set_item_delegate_for_column(index, delegate)
            self._delegates.append(delegate)

    def set_jumps(self, *, remaining: int, total: int) -> None:
        """Set the header's remaining/total jumps."""
        self._remaining_jumps = remaining
        self._total_jumps = total

    def retranslate_headers(self) -> None:
        """Retranslate the headers of the table."""
        for index, header_section in enumerate(self._header_sections):
            if (
                not header_section.has_jumps
                and (header := self._table.horizontal_header_item(index)) is not None
            ):
                header.set_text(_(header_section.text))

        self.format_jump_header()

    def item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        """
        Update the headers after a change to `item`.

        By default resizes the first column if the changes was in that column.
        """
        if item.column() == 0:
            self._table.resize_column_to_contents(0)

    def format_jump_header(self) -> None:
        """Update the header with the jump information."""
        self._table.horizontal_header_item(self._jump_col_index).set_text(
            _(self._header_sections[self._jump_col_index].text).format(
                self._remaining_jumps,
                self._total_jumps,
            )
        )
        self._table.resize_column_to_contents(self._jump_col_index)

    @property
    def column_count(self) -> int:
        """The header's column count for the table."""  # noqa: D401
        return len(self._header_sections)

    @cached_property
    def _jump_col_index(self) -> int:
        for index, header_section in enumerate(self._header_sections):
            if header_section.has_jumps:
                return index
        raise RuntimeError("No jump column for this header.")


class GenericHeader(RouteTableHeader):
    """Table header for generic plots of unknown type."""

    _header_sections = (
        HeaderSection(
            text=N_("System name ({}/{})"),
            has_jumps=True,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
    )


class NeutronHeader(RouteTableHeader):
    """Table header for neutron plots."""

    _header_sections = (
        HeaderSection(text="System name"),
        HeaderSection(
            text=N_("Distance"),
            delegate_type=DoubleSpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Remaining"),
            delegate_type=DoubleSpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Jumps {}/{}"),
            delegate_type=SpinBoxDelegate,
            has_jumps=True,
        ),
    )


class ExactHeader(RouteTableHeader):
    """Table header for exact plots."""

    _header_sections = (
        HeaderSection(text=N_("System name ({}/{})"), has_jumps=True),
        HeaderSection(
            text=N_("Distance"),
            delegate_type=DoubleSpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Remaining"),
            delegate_type=DoubleSpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Scoopable"),
            delegate_type=CheckBoxDelegate,
        ),
        HeaderSection(
            text=N_("Neutron"),
            delegate_type=CheckBoxDelegate,
        ),
    )


class RoadToRichesHeader(RouteTableHeader):
    """Table header for exact plots."""

    _header_sections = (
        HeaderSection(text=N_("System name")),
        HeaderSection(text=N_("Body count"), delegate_type=SpinBoxDelegate),
        HeaderSection(
            text=N_("Total scan value"),
            delegate_type=SpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Total mapping value"),
            delegate_type=DoubleSpinBoxDelegate,
            resize_mode=QtWidgets.QHeaderView.ResizeMode.Stretch,
        ),
        HeaderSection(
            text=N_("Jumps {}/{}"), delegate_type=SpinBoxDelegate, has_jumps=True
        ),
    )


_row_type_to_header = {
    GenericPlotRow: GenericHeader,
    NeutronPlotRow: NeutronHeader,
    ExactPlotRow: ExactHeader,
    RoadToRichesRow: RoadToRichesHeader,
}


def header_from_row_type(row_type: type[SystemEntry]) -> type[RouteTableHeader]:
    """Get the appropriate table header class for the given row type."""
    return _row_type_to_header[row_type]
