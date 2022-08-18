# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from auto_neutron.fsd import FrameShiftDrive

_BOOSTER_NAME_TO_RANGE = {
    "int_guardianfsdbooster_size1": 4.0,
    "int_guardianfsdbooster_size2": 6.0,
    "int_guardianfsdbooster_size3": 7.75,
    "int_guardianfsdbooster_size4": 9.25,
    "int_guardianfsdbooster_size5": 10.5,
}


class Ship:
    """Hold stats of a ship required for plotting."""

    def __init__(self):
        self.fsd: FrameShiftDrive | None = None
        self.jump_range_boost: float | None = None
        self.tank_size: int | None = None
        self.reserve_size: float | None = None
        self.unladen_mass: float | None = None
        self.max_cargo: int | None = None

    def jump_range(self, *, cargo_mass: int) -> float:
        """Calculate the jump range with `cargo_mass` t of cargo."""
        return (
            self.fsd.optimal_mass
            * (1000 * self.fsd.max_fuel_usage / self.fsd.rating_const)
            ** (1 / self.fsd.size_const)
            / (self.unladen_mass + self.tank_size + self.reserve_size + cargo_mass)
        ) + self.jump_range_boost

    # region: loadout
    @classmethod
    def from_loadout(cls, loadout_dict: dict):
        """Populate a new instance from `loadout_dict`."""
        instance = cls()
        instance.update_from_loadout(loadout_dict)
        return instance

    def update_from_loadout(self, loadout_dict: dict) -> None:
        """Update the state from a loadout event dict."""
        self.fsd = FrameShiftDrive.from_loadout_dict(loadout_dict)
        self.jump_range_boost = self._fsd_boost_from_loadout_dict(loadout_dict)
        self.unladen_mass = loadout_dict["UnladenMass"]
        self.tank_size = int(loadout_dict["FuelCapacity"]["Main"])
        self.reserve_size = loadout_dict["FuelCapacity"]["Reserve"]
        self.max_cargo = loadout_dict["CargoCapacity"]

    @staticmethod
    def _fsd_boost_from_loadout_dict(loadout: dict) -> float:
        """Get jump range boost of a fsd booster from `loadout`."""
        for module in loadout["Modules"]:
            if "fsdbooster" in module["Item"]:
                return _BOOSTER_NAME_TO_RANGE[module["Item"]]
        return 0

    # endregion

    # region: coriolis
    @classmethod
    def from_coriolis(cls, coriolis_json: dict):
        """Populate a new instance from `coriolis_json`."""
        instance = cls()
        instance.update_from_coriolis(coriolis_json)
        return instance

    def update_from_coriolis(self, coriolis_json: dict) -> None:
        """Update the state from a coriolis json dump."""
        self.fsd = FrameShiftDrive.from_coriolis_dict(coriolis_json)
        self.jump_range_boost = self._fsd_boost_from_coriolis_json(coriolis_json)
        self.unladen_mass = coriolis_json["stats"]["unladenMass"]
        self.tank_size = coriolis_json["stats"]["fuelCapacity"]
        self.reserve_size = coriolis_json["stats"]["reserveFuelCapacity"]
        self.max_cargo = coriolis_json["stats"]["cargoCapacity"]

    @staticmethod
    def _fsd_boost_from_coriolis_json(json_data: dict) -> float:
        """Extract the jump range boost information from coriolis json, if any."""
        for component in json_data["components"]["internal"]:
            if component["group"] == "Guardian Frame Shift Drive Booster":
                return _BOOSTER_NAME_TO_RANGE[
                    f"int_guardianfsdbooster_size{component['class']}"
                ]
        return 0

    # endregion
