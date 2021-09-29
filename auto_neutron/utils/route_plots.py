# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import typing as t
from dataclasses import dataclass


@dataclass
class ExactPlotRow:
    """One row entry of an exact plot from the Spansh Galaxy Plotter."""

    system: str
    dist: float
    dist_rem: float
    fuel_left: t.Optional[float]
    fuel_used: t.Optional[float]
    refuel: t.Optional[bool]
    neutron_star: bool

    def __eq__(self, other: t.Union[ExactPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)


@dataclass
class NeutronPlotRow:
    """One row entry of an exact plot from the Spansh Neutron Router."""

    system: str
    dist_to_arrival: float
    dist_rem: float
    jumps: int

    def __eq__(self, other: t.Union[NeutronPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)


RouteList = t.Union[list[ExactPlotRow], list[NeutronPlotRow]]
