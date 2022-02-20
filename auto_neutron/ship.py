# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from auto_neutron.constants import BOOSTER_CONSTANTS, FSD_CONSTANTS, FrameShiftDrive

_RATING_TO_CLASS = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}

_DEEP_CHARGE_MODIFIER = 1.10  # max fuel usage increased by 10%
_MASS_MANAGER_MODIFIER = 1.04  # Adds 4% to optimal mass


class Ship:
    """Hold stats of a ship required for plotting."""

    def __init__(self):
        self.fsd: FrameShiftDrive | None = None
        self.jump_range_boost: float | None = None
        self.tank_size: int | None = None
        self.reserve_size: float | None = None
        self.unladen_mass: float | None = None
        self.max_cargo: int | None = None
        self.initialized = False

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
        self.fsd = self._fsd_from_loadout_dict(loadout_dict)
        self.jump_range_boost = self._fsd_boost_from_loadout_dict(loadout_dict)
        self.unladen_mass = loadout_dict["UnladenMass"]
        self.tank_size = int(loadout_dict["FuelCapacity"]["Main"])
        self.reserve_size = loadout_dict["FuelCapacity"]["Reserve"]
        self.max_cargo = loadout_dict["CargoCapacity"]
        self.initialized = True

    @staticmethod
    def _fsd_from_loadout_dict(loadout: dict) -> FrameShiftDrive:
        """Get FrameShiftDrive constants from `loadout`."""
        fsd_dict = next(
            filter(
                lambda module: module["Slot"] == "FrameShiftDrive", loadout["Modules"]
            )
        )
        fsd = FSD_CONSTANTS[fsd_dict["Item"]]

        engineering = fsd_dict.get("Engineering")
        if engineering is not None:
            for modifier in engineering["Modifiers"]:
                if modifier["Label"] == "FSDOptimalMass":
                    fsd = fsd._replace(optimal_mass=modifier["Value"])
                elif modifier["Label"] == "MaxFuelPerJump":
                    fsd = fsd._replace(max_fuel_usage=modifier["Value"])
        return fsd

    @staticmethod
    def _fsd_boost_from_loadout_dict(loadout: dict) -> float:
        """Get jump range boost of a fsd booster from `loadout`."""
        booster_dict = next(
            filter(lambda module: "fsdbooster" in module["Item"], loadout["Modules"]),
            None,
        )
        if booster_dict is not None:
            return BOOSTER_CONSTANTS[booster_dict["Item"]]
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
        self.fsd = self._fsd_from_coriolis_json(coriolis_json)
        self.jump_range_boost = self._fsd_boost_from_coriolis_json(coriolis_json)
        self.unladen_mass = coriolis_json["stats"]["unladenMass"]
        self.tank_size = coriolis_json["stats"]["fuelCapacity"]
        self.reserve_size = coriolis_json["stats"]["reserveFuelCapacity"]
        self.max_cargo = coriolis_json["stats"]["cargoCapacity"]
        self.initialized = True

    @classmethod
    def _fsd_from_coriolis_json(cls, json_data: dict) -> FrameShiftDrive:
        """Extract FSD information from coriolis json."""
        fsd_dict = json_data["components"]["standard"]["frameShiftDrive"]
        class_ = _RATING_TO_CLASS[fsd_dict["rating"]]
        size = fsd_dict["class"]
        fsd = FSD_CONSTANTS[cls._coriolis_class_and_size_to_ed_name(class_, size)]
        if (mod_dict := fsd_dict.get("modifications")) is not None:
            if (opt_mass_mod := mod_dict.get("optmass")) is not None:
                fsd = fsd._replace(
                    optimal_mass=fsd.optimal_mass * (1 + opt_mass_mod / 10000)
                )

            if (experimental_dict := fsd_dict["blueprint"].get("special")) is not None:
                if experimental_dict["edname"] == "special_fsd_heavy":
                    fsd = fsd._replace(
                        optimal_mass=fsd.optimal_mass * _MASS_MANAGER_MODIFIER
                    )
                elif experimental_dict["edname"] == "special_fsd_fuelcapacity":
                    fsd = fsd._replace(
                        max_fuel_usage=fsd.max_fuel_usage * _DEEP_CHARGE_MODIFIER
                    )
        return fsd

    @staticmethod
    def _fsd_boost_from_coriolis_json(json_data: dict) -> float:
        """Extract the jump range boost information from coriolis json, if any."""
        for component in json_data["components"]["internal"]:
            if component["group"] == "Guardian Frame Shift Drive Booster":
                return BOOSTER_CONSTANTS[
                    f"int_guardianfsdbooster_size{component['class']}"
                ]
        return 0

    @staticmethod
    def _coriolis_class_and_size_to_ed_name(class_: int, size: int) -> str:
        """Create the name used by ED in the logs for the FSD to be used to access the `FSD_CONSTANTS` dict."""
        return f"int_hyperdrive_size{size}_class{class_}"

    # endregion
