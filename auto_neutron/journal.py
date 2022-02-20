# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import json
import logging
import typing as t

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.game_state import Location
from auto_neutron.utils.utils import get_sector_midpoint

if t.TYPE_CHECKING:
    import collections.abc
    from pathlib import Path

log = logging.getLogger(__name__)


class Journal(QtCore.QObject):
    """Keep track of a journal file and the state of the game from it."""

    system_sig = QtCore.Signal(Location)
    target_signal = QtCore.Signal(Location)
    loadout_sig = QtCore.Signal(dict)
    cargo_sig = QtCore.Signal(int)
    shut_down_sig = QtCore.Signal()

    def __init__(self, journal_path: Path):
        super().__init__()
        self.path = journal_path
        self.loadout = None
        self.location = None
        self.last_target = None
        self.cargo = None
        self.shut_down = False

    def tail(self) -> collections.abc.Generator[None, None, None]:
        """Follow a log file, and emit signals for new systems, loadout changes and game shut down."""
        log.info(f"Starting tailer of journal file at {self.path}.")
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(0, 2)
            while True:
                if line := journal_file.readline():
                    self._parse_journal_line(line)
                else:
                    yield

    def parse(self) -> None:
        """Parse the whole journal file and update the fields that were set."""
        log.info(f"Statically parsing journal file at {self.path}.")
        with self.path.open(encoding="utf8") as journal_file:
            for line in journal_file:
                self._parse_journal_line(line)

    def _parse_journal_line(self, line: str) -> None:
        """Parse a single line from the journal, setting attributes and emitting signals appropriately."""
        entry = json.loads(line)
        if entry["event"] == "Loadout":
            self.loadout = entry
            self.loadout_sig.emit(entry)

        elif entry["event"] == "Location" or entry["event"] == "FSDJump":
            self.location = Location(entry["StarSystem"], *entry["StarPos"])
            if entry["event"] == "FSDJump":
                self.system_sig.emit(Location(entry["StarSystem"], *entry["StarPos"]))

        elif entry["event"] == "FSDTarget":
            self.last_target = Location(
                entry["Name"], *get_sector_midpoint(entry["SystemAddress"])
            )
            self.target_signal.emit(self.last_target)

        elif entry["event"] == "Cargo" and entry["Vessel"] == "Ship":
            self.cargo = entry["Count"]

        elif entry["event"] == "Shutdown":
            self.shut_down = True
            self.shut_down_sig.emit()
