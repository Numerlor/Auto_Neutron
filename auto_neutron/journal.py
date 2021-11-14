# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import collections.abc
import json
import logging
import typing as t
from pathlib import Path

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.game_state import Location

log = logging.getLogger(__name__)


class Journal(QtCore.QObject):
    """Keep track of a journal file and the state of the game from it."""

    system_sig = QtCore.Signal(Location)
    loadout_sig = QtCore.Signal(dict)
    cargo_sig = QtCore.Signal(int)
    shut_down_sig = QtCore.Signal()

    def __init__(self, journal_path: Path):
        super().__init__()
        self.path = journal_path

    def tail(self) -> collections.abc.Generator[None, None, None]:
        """Follow a log file, and emit signals for new systems, loadout changes and game shut down."""
        log.info(f"Starting tailer of journal file at {self.path}.")
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(0, 2)
            while True:
                if line := journal_file.readline():
                    entry = json.loads(line)
                    if entry["event"] == "FSDJump":
                        self.system_sig.emit(
                            Location(entry["StarSystem"], *entry["StarPos"])
                        )

                    elif entry["event"] == "Loadout":
                        self.loadout_sig.emit(entry)

                    elif entry["event"] == "Shutdown":
                        self.shut_down_sig.emit()
                else:
                    yield

    def get_static_state(
        self,
    ) -> tuple[t.Optional[dict], t.Optional[Location], t.Optional[int], bool]:
        """Parse the whole journal file and return the ship, location, current cargo and game was shut down state."""
        log.info(f"Statically parsing journal file at {self.path}.")
        loadout = None
        location = None
        cargo = None
        with self.path.open(encoding="utf8") as journal_file:
            for line in journal_file:
                entry = json.loads(line)
                if entry["event"] == "Loadout":
                    loadout = entry
                elif entry["event"] == "Location":
                    location = Location(entry["StarSystem"], *entry["StarPos"])
                elif entry["event"] == "Cargo" and entry["Vessel"] == "Ship":
                    cargo = entry["Count"]
                elif entry["event"] == "Shutdown":
                    return loadout, location, cargo, True

        return loadout, location, cargo, False

    def reload(self) -> None:
        """Parse the whole journal file and emit signals with the appropriate data."""
        loadout, location, cargo, shut_down = self.get_static_state()

        if shut_down:
            self.shut_down_sig.emit()
        if location is not None:
            self.system_sig.emit(location)
        if loadout is not None:
            self.loadout_sig.emit(loadout)
        if cargo is not None:
            self.cargo_sig.emit(cargo)
