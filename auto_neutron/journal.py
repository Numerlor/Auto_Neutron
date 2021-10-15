# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import collections.abc
import dataclasses
import json
import typing
from pathlib import Path

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.ship import Ship


@dataclasses.dataclass
class GameState:
    """
    Hold the current state of the game from the journal.

    The state can be updated through assignments on public attributes or using `update_from_loadout`.
    """

    ship: Ship = None
    shut_down: bool = None
    location: str = None


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
                            self.game_state.ship.update_from_loadout(entry)
                        else:
                            self.game_state = Ship.from_loadout(entry)

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
            self.game_state = Ship.from_loadout(loadout)
        self.game_state.shut_down = shut_down
        self.game_state.location = location
