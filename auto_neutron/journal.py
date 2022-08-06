# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import datetime
import json
import logging
import typing as t
from operator import attrgetter

import more_itertools
from PySide6 import QtCore
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.constants import JOURNAL_PATH
from auto_neutron.game_state import Location
from auto_neutron.ship import Ship
from auto_neutron.utils.utils import get_sector_midpoint

if t.TYPE_CHECKING:
    import collections.abc
    from pathlib import Path

log = logging.getLogger(__name__)


class Journal(QtCore.QObject):
    """Keep track of a journal file and the state of the game from it."""

    system_sig = QtCore.Signal(Location)
    target_signal = QtCore.Signal(Location)
    cargo_signal = QtCore.Signal(int)
    loadout_sig = QtCore.Signal(dict)
    shut_down_sig = QtCore.Signal()

    def __init__(self, journal_path: Path):
        super().__init__()
        self.path = journal_path
        self.ship = None
        self.location = None
        self.last_target = None
        self.cargo = None
        self.shut_down = False
        self.is_oddysey = False
        self.cmdr = None

        self._last_file_pos = 0

    def tail(self) -> collections.abc.Generator[None, None, None]:
        """Follow a log file, and emit signals for new systems, loadout changes and game shut down."""
        log.info(f"Starting tailer of journal file {self.path.name}.")
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(0, 2)
            while True:
                if line := journal_file.readline():
                    self._last_file_pos = journal_file.tell()
                    self._parse_journal_line(line)
                else:
                    yield

    def parse(self) -> None:
        """Parse the whole journal file and update the fields that were set."""
        log.info(
            f"Statically parsing journal file {self.path.name} from pos {self._last_file_pos}."
        )
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(self._last_file_pos)
            while line := journal_file.readline():
                self._last_file_pos = journal_file.tell()
                self._parse_journal_line(line)

    def _parse_journal_line(self, line: str) -> None:
        """Parse a single line from the journal, setting attributes and emitting signals appropriately."""
        entry = json.loads(line)
        if entry["event"] == "Loadout":
            if self.ship is None:
                self.ship = Ship()
            self.ship.update_from_loadout(entry)
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
            self.cargo_signal.emit(self.cargo)

        elif entry["event"] == "Fileheader":
            self.is_oddysey = entry.get("Odyssey", False)

        elif entry["event"] == "Commander":
            self.cmdr = entry["Name"]

        elif entry["event"] == "Shutdown":
            self.shut_down = True
            self.shut_down_sig.emit()


journal_cache = {}


def get_cached_journal(path: Path) -> Journal:
    """
    Get the journal object form `path`, if the journal was opened before, get the changed object.

    The journal is parsed before being returned.
    """
    try:
        journal = journal_cache[path]
    except KeyError:
        journal = journal_cache[path] = Journal(path)

    journal.parse()

    return journal


def get_unique_cmdr_journals() -> list[Journal]:
    """
    Get the latest journals for each found CMDR.

    Only the first 15 journals newer than a week are looked at.
    """
    week_before = (datetime.datetime.now() - datetime.timedelta(weeks=1)).timestamp()

    journal_paths = [
        path
        for path in JOURNAL_PATH.glob("Journal.*.log")
        if path.stat().st_ctime > week_before
    ]
    journal_paths.sort(key=lambda path: path.stat().st_ctime, reverse=True)

    journals = []
    for journal_path in journal_paths[:15]:
        journal = get_cached_journal(journal_path)
        if not journal.shut_down:
            journals.append(journal)

    return list(more_itertools.unique_everseen(journals, attrgetter("cmdr")))
