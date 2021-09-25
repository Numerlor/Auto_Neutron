import collections.abc
import json
import typing
from pathlib import Path

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.constants import BOOSTER_CONSTANTS, FSD_CONSTANTS, FrameShiftDrive


class GameState:
    """
    Hold the current state of the game from the journal.

    The state can be updated through assignments on public attributes or using `update_from_loadout`.
    """

    def __init__(self, loadout_dict: dict):
        # Assigned from update_from_loadout
        self._fsd = None
        self._jump_range_boost = None
        self._fueled_mass = None

        self.update_from_loadout(loadout_dict)
        self.shut_down = False
        self.location = None

    def jump_range(self, *, cargo_mass: int) -> float:
        """Calculate the jump range with `cargo_mass` t of cargo."""
        return (
            self._fsd.optimal_mass
            * (1000 * self._fsd.max_fuel_usage / self._fsd.rating_const)
            ** (1 / self._fsd.size_const)
            / (self._fueled_mass + cargo_mass)
        ) + self._jump_range_boost

    def update_from_loadout(self, loadout_dict: dict) -> None:
        """Update the state from a loadout event dict."""
        self._fsd = self._fsd_from_loadout_dict(loadout_dict)
        self._jump_range_boost = self._fsd_boost_from_loadout_dict(loadout_dict)
        self._fueled_mass = loadout_dict["UnladenMass"] + sum(
            loadout_dict["FuelCapacity"].values()
        )

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

    @staticmethod
    def _fsd_from_loadout_dict(loadout: dict) -> FrameShiftDrive:
        """Get FrameShiftDrive constants from `loadout`."""
        fsd_dict = next(
            filter(
                lambda module: module["Slot"] == "FrameShiftDrive", loadout["Modules"]
            )
        )
        engineered_optimal_mass = None
        engineered_jump_fuel_cap = None
        engineering = fsd_dict.get("Engineering")
        if engineering is not None:
            for modifier in engineering["Modifiers"]:
                if modifier["Label"] == "FrameShiftDriveOptimalMass":
                    engineered_optimal_mass = modifier["Value"]
                elif modifier["Label"] == "MaxFuelPerJump":
                    engineered_jump_fuel_cap = modifier["Value"]

        fsd = FSD_CONSTANTS[fsd_dict["Item"]]
        if engineered_optimal_mass is not None:
            fsd = fsd._replace(optimal_mass=engineered_optimal_mass)
        if engineered_jump_fuel_cap is not None:
            fsd = fsd._replace(max_fuel_usage=engineered_optimal_mass)
        return fsd


class Journal(QtCore.QObject):
    """Keep track of a journal file and the state of the game from it."""

    system_sig = QtCore.Signal(str)
    shutdown_sig = QtCore.Signal()

    def __init__(self, journal_path: Path):
        super().__init__()
        self.path = journal_path
        self.game_state: typing.Optional[GameState] = None
        self.reload()

    def tail(self) -> collections.abc.Generator[None, None, None]:
        """Follow a log file, updating `self.game_state` on location and loadout changes and on shutdown."""
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(0, 2)
            while True:
                if line := journal_file.readline():
                    entry = json.loads(line)
                    if entry["event"] == "FSDJump":
                        self.game_state.location = entry["StarSystem"]
                        self.system_sig.emit(entry["StarSystem"])

                    elif entry["event"] == "Loadout":
                        if self.game_state is not None:
                            self.game_state.update_from_loadout(entry)
                        else:
                            self.game_state = GameState(entry)

                    elif entry["event"] == "Shutdown":
                        self.shutdown_sig.emit()
                else:
                    yield

    def reload(self) -> None:
        """Parse the whole journal file and create a `GameState` for it behind `self.game_state`."""
        loadout = None
        shut_down = False
        with self.path.open(encoding="utf8") as journal_file:
            for line in journal_file:
                entry = json.loads(line)
                if entry["event"] == "Loadout":
                    loadout = entry
                elif entry["event"] == "Location":
                    location = entry["StarSystem"]
                elif entry["event"] == "Shutdown":
                    shut_down = True
        if loadout is not None:
            self.game_state = GameState(loadout)
        self.game_state.shut_down = shut_down
        self.game_state.location = location
