# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import copy
import dataclasses
import typing as t

import more_itertools

_RATING_TO_CLASS = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}

_DEEP_CHARGE_MODIFIER = 1.10  # max fuel usage increased by 10%
_MASS_MANAGER_MODIFIER = 1.04  # Adds 4% to optimal mass


@dataclasses.dataclass(slots=True, frozen=True)
class FrameShiftDrive:
    """Hold information about a frame shift drive module."""

    size: int
    class_: int
    max_fuel_usage: float
    optimal_mass: float

    _SIZE_CONSTANTS: t.ClassVar[dict[int, float]] = {
        2: 2.0,
        3: 2.15,
        4: 2.3,
        5: 2.45,
        6: 2.6,
        7: 2.75,
        8: 2.9,
    }
    _CLASS_CONSTANTS: t.ClassVar[dict[int, int]] = {1: 11, 2: 10, 3: 8, 4: 10, 5: 12}

    @property
    def rating_const(self) -> int:
        """Get the linear rating const for the FSD's class rating."""
        return self._CLASS_CONSTANTS[self.class_]

    @property
    def size_const(self) -> float:
        """Get the power constant for the FSD's size."""
        return self._SIZE_CONSTANTS[self.size]

    @classmethod
    def from_loadout_dict(cls, loadout: dict) -> FrameShiftDrive:
        """Create a FrameShiftDrive instance for the FSD in `loadout`."""
        fsd_dict = more_itertools.only(
            module
            for module in loadout["Modules"]
            if module["Slot"] == "FrameShiftDrive"
        )
        fsd = _BASE_FSDS[fsd_dict["Item"]]

        engineering = fsd_dict.get("Engineering")
        if engineering is not None:
            fsd = copy.copy(fsd)
            for modifier in engineering["Modifiers"]:
                if modifier["Label"] == "FSDOptimalMass":
                    object.__setattr__(fsd, "optimal_mass", modifier["Value"])
                elif modifier["Label"] == "MaxFuelPerJump":
                    object.__setattr__(fsd, "max_fuel_usage", modifier["Value"])
        return fsd

    @classmethod
    def from_coriolis_dict(
        cls, coriolis_dict: dict
    ) -> FrameShiftDrive:  # TODO: Coriolis doesn't handle SCO yet
        """Create a FrameShiftDrive instance for the FSD in `coriolis_dict`."""
        fsd_dict = coriolis_dict["components"]["standard"]["frameShiftDrive"]
        class_ = _RATING_TO_CLASS[fsd_dict["rating"]]
        size = fsd_dict["class"]

        fsd = _BASE_FSDS[f"int_hyperdrive_size{size}_class{class_}"]
        if (mod_dict := fsd_dict.get("modifications")) is not None:
            fsd = copy.copy(fsd)
            if (opt_mass_mod := mod_dict.get("optmass")) is not None:
                object.__setattr__(
                    fsd, "optimal_mass", fsd.optimal_mass * (1 + opt_mass_mod / 10000)
                )

            if (experimental_dict := fsd_dict["blueprint"].get("special")) is not None:
                if experimental_dict["edname"] == "special_fsd_heavy":
                    object.__setattr__(
                        fsd,
                        "optimal_mass",
                        fsd.optimal_mass * _MASS_MANAGER_MODIFIER,
                    )
                elif experimental_dict["edname"] == "special_fsd_fuelcapacity":
                    object.__setattr__(
                        fsd,
                        "max_fuel_usage",
                        fsd.max_fuel_usage * _DEEP_CHARGE_MODIFIER,
                    )
        return fsd


@dataclasses.dataclass(slots=True, frozen=True)
class SCOFrameShiftDrive(FrameShiftDrive):
    """Supercruise overcharge FSD."""

    _CLASS_CONSTANTS = {1: 8, 2: 12, 3: 12, 4: 12, 5: 13}


_BASE_FSDS = {  # base unengineered FSDs
    "int_hyperdrive_size2_class1": FrameShiftDrive(2, 1, 0.60, 48),
    "int_hyperdrive_size2_class2": FrameShiftDrive(2, 2, 0.60, 54),
    "int_hyperdrive_size2_class3": FrameShiftDrive(2, 3, 0.60, 60),
    "int_hyperdrive_size2_class4": FrameShiftDrive(2, 4, 0.80, 75),
    "int_hyperdrive_size2_class5": FrameShiftDrive(2, 5, 0.90, 90),
    "int_hyperdrive_size3_class1": FrameShiftDrive(3, 1, 1.20, 80),
    "int_hyperdrive_size3_class2": FrameShiftDrive(3, 2, 1.20, 90),
    "int_hyperdrive_size3_class3": FrameShiftDrive(3, 3, 1.20, 100),
    "int_hyperdrive_size3_class4": FrameShiftDrive(3, 4, 1.50, 125),
    "int_hyperdrive_size3_class5": FrameShiftDrive(3, 5, 1.80, 150),
    "int_hyperdrive_size4_class1": FrameShiftDrive(4, 1, 2.00, 280),
    "int_hyperdrive_size4_class2": FrameShiftDrive(4, 2, 2.00, 315),
    "int_hyperdrive_size4_class3": FrameShiftDrive(4, 3, 2.00, 350),
    "int_hyperdrive_size4_class4": FrameShiftDrive(4, 4, 2.50, 438),
    "int_hyperdrive_size4_class5": FrameShiftDrive(4, 5, 3.00, 525),
    "int_hyperdrive_size5_class1": FrameShiftDrive(5, 1, 3.30, 560),
    "int_hyperdrive_size5_class2": FrameShiftDrive(5, 2, 3.30, 630),
    "int_hyperdrive_size5_class3": FrameShiftDrive(5, 3, 3.30, 700),
    "int_hyperdrive_size5_class4": FrameShiftDrive(5, 4, 4.10, 875),
    "int_hyperdrive_size5_class5": FrameShiftDrive(5, 5, 5.00, 1050),
    "int_hyperdrive_size6_class1": FrameShiftDrive(6, 1, 5.30, 960),
    "int_hyperdrive_size6_class2": FrameShiftDrive(6, 2, 5.30, 1080),
    "int_hyperdrive_size6_class3": FrameShiftDrive(6, 3, 5.30, 1200),
    "int_hyperdrive_size6_class4": FrameShiftDrive(6, 4, 6.60, 1500),
    "int_hyperdrive_size6_class5": FrameShiftDrive(6, 5, 8.00, 1800),
    "int_hyperdrive_size7_class1": FrameShiftDrive(7, 1, 8.50, 1440),
    "int_hyperdrive_size7_class2": FrameShiftDrive(7, 2, 8.50, 1620),
    "int_hyperdrive_size7_class3": FrameShiftDrive(7, 3, 8.50, 1800),
    "int_hyperdrive_size7_class4": FrameShiftDrive(7, 4, 10.60, 2250),
    "int_hyperdrive_size7_class5": FrameShiftDrive(7, 5, 12.80, 2700),
    "int_hyperdrive_overcharge_size2_class1": SCOFrameShiftDrive(2, 1, 0.60, 60),
    "int_hyperdrive_overcharge_size2_class2": SCOFrameShiftDrive(2, 2, 0.90, 90),
    "int_hyperdrive_overcharge_size2_class3": SCOFrameShiftDrive(2, 3, 0.90, 90),
    "int_hyperdrive_overcharge_size2_class4": SCOFrameShiftDrive(2, 4, 0.90, 90),
    "int_hyperdrive_overcharge_size2_class5": SCOFrameShiftDrive(2, 5, 1.00, 100),
    "int_hyperdrive_overcharge_size3_class1": SCOFrameShiftDrive(3, 1, 1.20, 100),
    "int_hyperdrive_overcharge_size3_class2": SCOFrameShiftDrive(3, 2, 1.80, 150),
    "int_hyperdrive_overcharge_size3_class3": SCOFrameShiftDrive(3, 3, 1.80, 150),
    "int_hyperdrive_overcharge_size3_class4": SCOFrameShiftDrive(3, 4, 1.80, 150),
    "int_hyperdrive_overcharge_size3_class5": SCOFrameShiftDrive(3, 5, 1.90, 167),
    "int_hyperdrive_overcharge_size4_class1": SCOFrameShiftDrive(4, 1, 2.00, 350),
    "int_hyperdrive_overcharge_size4_class2": SCOFrameShiftDrive(4, 2, 3.00, 525),
    "int_hyperdrive_overcharge_size4_class3": SCOFrameShiftDrive(4, 3, 3.00, 525),
    "int_hyperdrive_overcharge_size4_class4": SCOFrameShiftDrive(4, 4, 3.00, 525),
    "int_hyperdrive_overcharge_size4_class5": SCOFrameShiftDrive(4, 5, 3.20, 585),
    "int_hyperdrive_overcharge_size5_class1": SCOFrameShiftDrive(5, 1, 3.30, 700),
    "int_hyperdrive_overcharge_size5_class2": SCOFrameShiftDrive(5, 2, 5.00, 1050),
    "int_hyperdrive_overcharge_size5_class3": SCOFrameShiftDrive(5, 3, 5.00, 1050),
    "int_hyperdrive_overcharge_size5_class4": SCOFrameShiftDrive(5, 4, 5.00, 1050),
    "int_hyperdrive_overcharge_size5_class5": SCOFrameShiftDrive(5, 5, 5.20, 1175),
    "int_hyperdrive_overcharge_size6_class1": SCOFrameShiftDrive(6, 1, 5.30, 1200),
    "int_hyperdrive_overcharge_size6_class2": SCOFrameShiftDrive(6, 2, 8.00, 1800),
    "int_hyperdrive_overcharge_size6_class3": SCOFrameShiftDrive(6, 3, 8.00, 1800),
    "int_hyperdrive_overcharge_size6_class4": SCOFrameShiftDrive(6, 4, 8.00, 1800),
    "int_hyperdrive_overcharge_size6_class5": SCOFrameShiftDrive(6, 5, 8.30, 2000),
    "int_hyperdrive_overcharge_size7_class1": SCOFrameShiftDrive(7, 1, 8.50, 1800),
    "int_hyperdrive_overcharge_size7_class2": SCOFrameShiftDrive(7, 2, 12.80, 2700),
    "int_hyperdrive_overcharge_size7_class3": SCOFrameShiftDrive(7, 3, 12.80, 2700),
    "int_hyperdrive_overcharge_size7_class4": SCOFrameShiftDrive(7, 4, 12.80, 2700),
    "int_hyperdrive_overcharge_size7_class5": SCOFrameShiftDrive(7, 5, 13.10, 3000),
    "int_hyperdrive_overcharge_size8_class1": SCOFrameShiftDrive(8, 1, 13.60, 2800),
    "int_hyperdrive_overcharge_size8_class2": SCOFrameShiftDrive(8, 2, 20.40, 4200),
    "int_hyperdrive_overcharge_size8_class3": SCOFrameShiftDrive(8, 3, 20.40, 4200),
    "int_hyperdrive_overcharge_size8_class4": SCOFrameShiftDrive(8, 4, 20.40, 4200),
    "int_hyperdrive_overcharge_size8_class5": SCOFrameShiftDrive(8, 5, 20.70, 4670),
    "int_hyperdrive_overcharge_size8_class5_overchargebooster_mkii": SCOFrameShiftDrive(8, 5, 6.80, 4670),
}
